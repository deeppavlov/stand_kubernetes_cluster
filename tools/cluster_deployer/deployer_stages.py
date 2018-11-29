import shutil
import logging
import sys
import yaml
from traceback import format_exception
from typing import Optional
from enum import Enum
from collections import namedtuple
from pathlib import Path
from abc import ABCMeta, abstractmethod
from multiprocessing import Process, Queue

import requests
from docker import DockerClient
from docker.models.containers import Container
from docker.errors import ImageNotFound
from kubernetes import client as kube_client, config as kube_config

from deployer_utils import safe_delete_path, fill_placeholders_from_dict, poll

LogMessage = namedtuple('LogMessage', ['full_model_name', 'log_level', 'log_message', 'extended_log_message'])


class LogLevel(Enum):
    INFO = logging.INFO
    ERROR = logging.ERROR


class DeploymentStatus:
    def __init__(self, full_model_name: str):
        self.full_model_name: str = full_model_name
        self.finish: bool = False
        self.extended_stage_info: str = ''


class AbstractDeploymentStage(Process, metaclass=ABCMeta):
    def __init__(self, config: dict, stage_name: str, in_queue: Queue, out_queue: Queue):
        super(AbstractDeploymentStage, self).__init__()
        self.config = config
        self.stage_name: str = stage_name
        self.in_queue: Queue = in_queue
        self.out_queue: Queue = out_queue
        self.container: Optional[Container] = None
        self.extended_log_message = ''

    def run(self) -> None:
        while True:
            deployment_status: DeploymentStatus = self.in_queue.get()
            full_model_name = deployment_status.full_model_name

            try:
                log_message = LogMessage(full_model_name=full_model_name,
                                         log_level=LogLevel.INFO,
                                         log_message=f'[{full_model_name}] [{self.stage_name}]: stage started',
                                         extended_log_message='')

                self.out_queue.put(log_message)

                out_log_level = LogLevel.INFO
                out_log_message = f'[{full_model_name}] [{self.stage_name}]: stage finished'
                deployment_status: DeploymentStatus = self._act(deployment_status)
                out_extended_log_message = deployment_status.extended_stage_info.strip().strip(';').strip()
                deployment_status.extended_stage_info = ''

            except Exception:
                deployment_status.finish = True
                exc_type, exc_value, exc_tb = sys.exc_info()
                tr = '\t{}'.format('\n\t'.join(format_exception(exc_type, exc_value, exc_tb)))

                out_log_level = LogLevel.ERROR
                out_log_message = f'[{full_model_name}] [{self.stage_name}]: error occurred during stage:\n{tr}'
                out_extended_log_message = ''

                if self.container:
                    self.container.stop()

            log_message = LogMessage(full_model_name=full_model_name,
                                     log_level=out_log_level,
                                     log_message=out_log_message,
                                     extended_log_message=out_extended_log_message)

            self.out_queue.put(log_message)
            self.out_queue.put(deployment_status)

    @abstractmethod
    def _act(self, deployment_status: DeploymentStatus) -> DeploymentStatus:
        pass


class MakeFilesDeploymentStage(AbstractDeploymentStage):
    def __init__(self, config: dict, in_queue: Queue, out_queue: Queue):
        stage_name = 'make deployment files'
        super(MakeFilesDeploymentStage, self).__init__(config, stage_name, in_queue, out_queue)

    def _act(self, deployment_status: DeploymentStatus) -> DeploymentStatus:
        def get_dir_files_recursive(path: Path) -> list:
            files_list = []
            for item in path.iterdir():
                if item.is_dir():
                    files_list.extend(get_dir_files_recursive(item))
                else:
                    files_list.append(item)
            return files_list

        model_config = self.config['models'][deployment_status.full_model_name]
        temp_dir = self.config['paths']['temp_dir']
        templates_dir = self.config['paths']['templates_dir']
        kuber_configs_dir = self.config['paths']['kuber_configs_dir']
        models_dir = self.config['paths']['models_dir']

        deploy_files_dir = Path(temp_dir, f'{model_config["FULL_MODEL_NAME"]}').resolve()
        safe_delete_path(deploy_files_dir)
        shutil.copytree(templates_dir / model_config['TEMPLATE'], deploy_files_dir)
        deploy_files = get_dir_files_recursive(deploy_files_dir)

        for deploy_file in deploy_files:
            with open(deploy_file, 'r') as f:
                file = f.read()
            file = fill_placeholders_from_dict(file, model_config)
            with open(deploy_file, 'w') as f:
                f.write(file)

        Path(deploy_files_dir, 'kuber_dp.yaml').rename(deploy_files_dir / model_config['KUBER_DP_FILE'])
        Path(deploy_files_dir, 'kuber_lb.yaml').rename(deploy_files_dir / model_config['KUBER_LB_FILE'])
        Path(deploy_files_dir, 'run_model.sh').rename(deploy_files_dir / model_config['RUN_FILE'])
        Path(deploy_files_dir, 'dockerignore').rename(deploy_files_dir / '.dockerignore')

        # move Kubernetes configs
        kuber_config_path = kuber_configs_dir / model_config['FULL_MODEL_NAME']
        if kuber_config_path.is_dir() and not kuber_config_path.samefile('/'):
            shutil.rmtree(kuber_config_path, ignore_errors=True)
        kuber_config_path.mkdir(parents=True, exist_ok=True)
        Path(deploy_files_dir / model_config['KUBER_DP_FILE']).rename(
            kuber_config_path / model_config['KUBER_DP_FILE'])
        Path(deploy_files_dir / model_config['KUBER_LB_FILE']).rename(
            kuber_config_path / model_config['KUBER_LB_FILE'])

        # move model building files
        model_path = models_dir / model_config['FULL_MODEL_NAME']
        safe_delete_path(model_path)
        deploy_files_dir.rename(model_path)

        return deployment_status


class DeleteImageDeploymentStage(AbstractDeploymentStage):
    def __init__(self, config: dict, in_queue: Queue, out_queue: Queue):
        stage_name = 'delete docker image'
        super(DeleteImageDeploymentStage, self).__init__(config, stage_name, in_queue, out_queue)
        self.docker_client: DockerClient = DockerClient(base_url=config['docker_base_url'])

    def _act(self, deployment_status: DeploymentStatus) -> DeploymentStatus:
        kuber_image_tag = self.config['models'][deployment_status.full_model_name]['KUBER_IMAGE_TAG']

        try:
            self.docker_client.images.remove(kuber_image_tag)
        except ImageNotFound:
            deployment_status.extended_stage_info = f'image not exists {kuber_image_tag}'

        return deployment_status


class BuildImageDeploymentStage(AbstractDeploymentStage):
    def __init__(self, config: dict, in_queue: Queue, out_queue: Queue):
        stage_name = 'build docker image'
        super(BuildImageDeploymentStage, self).__init__(config, stage_name, in_queue, out_queue)
        self.docker_client: DockerClient = DockerClient(base_url=config['docker_base_url'])

    def _act(self, deployment_status: DeploymentStatus) -> DeploymentStatus:
        models_dir_path = self.config['paths']['models_dir']
        build_dir_path = str(models_dir_path / deployment_status.full_model_name)
        image_tag = self.config['models'][deployment_status.full_model_name]['KUBER_IMAGE_TAG']

        kwargs = {
            'path': build_dir_path,
            'tag': image_tag,
            'rm': True
        }

        self.docker_client.images.build(**kwargs)

        deployment_status.log_level = LogLevel.INFO
        deployment_status.log_message = f'Finished [{self.stage_name}] deployment stage ' \
                                        f'for [{deployment_status.full_model_name}]'

        return deployment_status


class TestImageDeploymentStage(AbstractDeploymentStage):
    def __init__(self, config: dict, in_queue: Queue, out_queue: Queue):
        stage_name = 'test docker image'
        super(TestImageDeploymentStage, self).__init__(config, stage_name, in_queue, out_queue)
        self.docker_client: DockerClient = DockerClient(base_url=config['docker_base_url'])

    def _act(self, deployment_status: DeploymentStatus) -> DeploymentStatus:
        # run docker container from built image
        image_tag = self.config['models'][deployment_status.full_model_name]['KUBER_IMAGE_TAG']
        container_port = self.config['models'][deployment_status.full_model_name]['PORT']
        local_log_dir = str(Path(self.config['local_log_dir']).expanduser().resolve())
        container_log_dir = str(Path(self.config['container_log_dir']).expanduser().resolve())
        dockerfile_template = self.config['models'][deployment_status.full_model_name]['TEMPLATE']
        gpu_templates = self.config['gpu_templates']
        local_gpu_device_index = self.config['local_gpu_device_index']

        kwargs = {
            'image': image_tag,
            'auto_remove': True,
            'detach': True,
            'ports': {container_port: container_port},
            'volumes': {local_log_dir: {'bind': container_log_dir, 'mode': 'rw'}}
        }

        if dockerfile_template in gpu_templates:
            kwargs['runtime'] = 'nvidia'
            kwargs['devices'] = [f'/dev/nvidia{str(local_gpu_device_index)}']

        self.container: Container = self.docker_client.containers.run(**kwargs)

        # test model API
        url = self.config['models'][deployment_status.full_model_name]['test_image_url']
        model_args = self.config['models'][deployment_status.full_model_name]['MODEL_ARGS']
        json_payload = {arg_name: ['This is probe text.'] for arg_name in model_args}
        polling_timeout = self.config['models'][deployment_status.full_model_name]['image_polling_timeout_sec']

        polling_result, polling_time = poll(probe=lambda: requests.post(url=url, json=json_payload),
                                            estimator=lambda result: result.status_code == 200,
                                            interval_sec=1,
                                            timeout_sec=polling_timeout)

        polling_result = polling_result.json()
        self.container.stop()
        deployment_status.extended_stage_info = f'elapsed time: {polling_time}, model response: {polling_result}'

        return deployment_status


class PushImageDeploymentStage(AbstractDeploymentStage):
    def __init__(self, config: dict, in_queue: Queue, out_queue: Queue):
        stage_name = 'push to cluster repo'
        super(PushImageDeploymentStage, self).__init__(config, stage_name, in_queue, out_queue)
        self.docker_client: DockerClient = DockerClient(base_url=config['docker_base_url'])

    def _act(self, deployment_status: DeploymentStatus) -> DeploymentStatus:
        image_tag = self.config['models'][deployment_status.full_model_name]['KUBER_IMAGE_TAG']
        server_response_generator = self.docker_client.images.push(image_tag, stream=True)
        server_response = '\t{}'.format('\n\t'.join([str(resp_str) for resp_str in server_response_generator]))
        deployment_status.extended_stage_info = f'server response:\n{server_response}'

        return deployment_status


# TODO: remove code same with delete kuber deployment stage
class DeployKuberDeploymentStage(AbstractDeploymentStage):
    def __init__(self, config: dict, in_queue: Queue, out_queue: Queue):
        stage_name = 'deploy in kubernetes'
        super(DeployKuberDeploymentStage, self).__init__(config, stage_name, in_queue, out_queue)

        kube_config.load_kube_config()
        self.kube_apps_v1_beta1_api = kube_client.AppsV1beta1Api()
        self.kube_core_v1_api = kube_client.CoreV1Api()

    def _act(self, deployment_status: DeploymentStatus) -> DeploymentStatus:
        kuber_configs_dir = self.config['paths']['kuber_configs_dir'] / deployment_status.full_model_name
        dp_name = self.config['models'][deployment_status.full_model_name]['KUBER_DP_NAME']
        dp_file_name = self.config['models'][deployment_status.full_model_name]['KUBER_DP_FILE']
        lb_name = self.config['models'][deployment_status.full_model_name]['KUBER_LB_NAME']
        lb_file_name = self.config['models'][deployment_status.full_model_name]['KUBER_LB_FILE']

        with open(kuber_configs_dir / dp_file_name) as f:
            dp_config = yaml.load(f)

        with open(kuber_configs_dir / lb_file_name) as f:
            lb_config = yaml.load(f)

        dp_namespace = dp_config['metadata']['namespace']
        lb_namespace = lb_config['metadata']['namespace']

        # remove existing deployment
        deployments_raw = kube_client.models.apps_v1beta1_deployment_list.AppsV1beta1DeploymentList = \
            self.kube_apps_v1_beta1_api.list_namespaced_deployment(namespace=dp_namespace)
        deployments = [item.metadata.name for item in deployments_raw.items]

        if dp_name in deployments:
            delete_dp_kwargs = {
                'name': dp_name,
                'namespace': dp_namespace,
                'body': kube_client.V1DeleteOptions(propagation_policy='Background')
            }
            self.kube_apps_v1_beta1_api.delete_namespaced_deployment(**delete_dp_kwargs)

        # remove existing load balancer
        load_balancers_raw: kube_client.models.v1_api_service_list.V1APIServiceList = \
            self.kube_core_v1_api.list_namespaced_service(namespace=lb_namespace)
        load_balancers = [item.metadata.name for item in load_balancers_raw.items]

        if lb_name in load_balancers:
            delete_lb_kwargs = {
                'name': lb_name,
                'namespace': lb_namespace,
                'body': kube_client.V1DeleteOptions(propagation_policy='Background')
            }
            self.kube_core_v1_api.delete_namespaced_service(**delete_lb_kwargs)

        # create deployment
        create_dp_kwargs = {
            'namespace': dp_namespace,
            'body': dp_config,
            'include_uninitialized': True
        }
        self.kube_apps_v1_beta1_api.create_namespaced_deployment(**create_dp_kwargs)

        # create load balancer
        create_lb_kwargs = {
            'namespace': dp_namespace,
            'body': lb_config,
            'include_uninitialized': True
        }
        self.kube_core_v1_api.create_namespaced_service(**create_lb_kwargs)

        return deployment_status


class DeleteKuberDeploymentStage(AbstractDeploymentStage):
    def __init__(self, config: dict, in_queue: Queue, out_queue: Queue):
        stage_name = 'delete kubernetes deployment'
        super(DeleteKuberDeploymentStage, self).__init__(config, stage_name, in_queue, out_queue)

        kube_config.load_kube_config()
        self.kube_apps_v1_beta1_api = kube_client.AppsV1beta1Api()
        self.kube_core_v1_api = kube_client.CoreV1Api()

    def _act(self, deployment_status: DeploymentStatus) -> DeploymentStatus:
        kuber_configs_dir = self.config['paths']['kuber_configs_dir'] / deployment_status.full_model_name
        dp_name = self.config['models'][deployment_status.full_model_name]['KUBER_DP_NAME']
        dp_file_name = self.config['models'][deployment_status.full_model_name]['KUBER_DP_FILE']
        lb_name = self.config['models'][deployment_status.full_model_name]['KUBER_LB_NAME']
        lb_file_name = self.config['models'][deployment_status.full_model_name]['KUBER_LB_FILE']

        with open(kuber_configs_dir / dp_file_name) as f:
            dp_config = yaml.load(f)

        with open(kuber_configs_dir / lb_file_name) as f:
            lb_config = yaml.load(f)

        dp_namespace = dp_config['metadata']['namespace']
        lb_namespace = lb_config['metadata']['namespace']

        # remove deployment
        deployments_raw = kube_client.models.apps_v1beta1_deployment_list.AppsV1beta1DeploymentList = \
            self.kube_apps_v1_beta1_api.list_namespaced_deployment(namespace=dp_namespace)
        deployments = [item.metadata.name for item in deployments_raw.items]

        if dp_name in deployments:
            delete_dp_kwargs = {
                'name': dp_name,
                'namespace': dp_namespace,
                'body': kube_client.V1DeleteOptions(propagation_policy='Background')
            }
            self.kube_apps_v1_beta1_api.delete_namespaced_deployment(**delete_dp_kwargs)
        else:
            deployment_status.extended_stage_info += f'; deployment not exists {dp_name}'

        # remove load balancer
        load_balancers_raw: kube_client.models.v1_api_service_list.V1APIServiceList = \
            self.kube_core_v1_api.list_namespaced_service(namespace=lb_namespace)
        load_balancers = [item.metadata.name for item in load_balancers_raw.items]

        if lb_name in load_balancers:
            delete_lb_kwargs = {
                'name': lb_name,
                'namespace': lb_namespace,
                'body': kube_client.V1DeleteOptions(propagation_policy='Background')
            }
            self.kube_core_v1_api.delete_namespaced_service(**delete_lb_kwargs)
        else:
            deployment_status.extended_stage_info += f'; load balancer not exists {lb_name}'

        return deployment_status


class TestKuberDeploymentStage(AbstractDeploymentStage):
    def __init__(self, config: dict, in_queue: Queue, out_queue: Queue):
        stage_name = 'test kuber deployment'
        super(TestKuberDeploymentStage, self).__init__(config, stage_name, in_queue, out_queue)

    def _act(self, deployment_status: DeploymentStatus) -> DeploymentStatus:
        url = self.config['models'][deployment_status.full_model_name]['test_deployment_url']
        model_args = self.config['models'][deployment_status.full_model_name]['MODEL_ARGS']
        json_payload = {arg_name: ['This is probe text.'] for arg_name in model_args}
        polling_timeout = self.config['models'][deployment_status.full_model_name]['deployment_polling_timeout_sec']

        polling_result, polling_time = poll(probe=lambda: requests.post(url=url, json=json_payload),
                                            estimator=lambda result: result.status_code == 200,
                                            interval_sec=1,
                                            timeout_sec=polling_timeout)

        polling_result = polling_result.json()

        deployment_status.log_level = LogLevel.INFO
        deployment_status.log_message = f'Finished [{self.stage_name}] deployment stage ' \
                                        f'for [{deployment_status.full_model_name}], ' \
                                        f'model response: {polling_result}, elapsed time: {polling_time}'

        return deployment_status


class PushToDockerHubDeploymentStage(AbstractDeploymentStage):
    def __init__(self, config: dict, in_queue: Queue, out_queue: Queue):
        stage_name = 'push to docker hub'
        super(PushToDockerHubDeploymentStage, self).__init__(config, stage_name, in_queue, out_queue)
        self.docker_client: DockerClient = DockerClient(base_url=config['docker_base_url'])
        self.docker_client.login(self.config['dockerhub_registry'], self.config['dockerhub_password'])

    def _act(self, deployment_status: DeploymentStatus) -> DeploymentStatus:
        kuber_image_tag = self.config['models'][deployment_status.full_model_name]['KUBER_IMAGE_TAG']
        model_name = self.config['models'][deployment_status.full_model_name]['MODEL_NAME']
        dockerhub_image_tag = f"{self.config['dockerhub_registry']}/{model_name}"

        images = self.docker_client.images
        image = images.get(kuber_image_tag)
        image.tag(dockerhub_image_tag)

        server_response_generator = self.docker_client.images.push(dockerhub_image_tag, stream=True)
        server_response = '\t{}'.format('\n\t'.join([str(resp_str) for resp_str in server_response_generator]))
        deployment_status.extended_stage_info = f'server response:\n{server_response}'

        images.remove(dockerhub_image_tag)

        return deployment_status


class FinalDeploymentStage(AbstractDeploymentStage):
    def __init__(self, config: dict, in_queue: Queue, out_queue: Queue):
        stage_name = 'FINISH DEPLOYMENT'
        super(FinalDeploymentStage, self).__init__(config, stage_name, in_queue, out_queue)

    def _act(self, deployment_status: DeploymentStatus) -> DeploymentStatus:
        deployment_status.finish = True
        return deployment_status

import shutil
import logging
import sys
import yaml
import json
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
from docker.errors import ImageNotFound, NotFound
from kubernetes import client as kube_client, config as kube_config

from deployer_utils import safe_delete_path, fill_placeholders_from_dict, poll

LogMessage = namedtuple('LogMessage', ['full_model_name', 'log_level', 'log_message', 'extended_log_message'])
KuberEntityData = namedtuple('KuberEntityData', ['name', 'namespace', 'config'])


class LogLevel(Enum):
    INFO = logging.INFO
    ERROR = logging.ERROR


class DeploymentStatus:
    def __init__(self, full_model_name: str, pipeline: list):
        self.full_model_name: str = full_model_name
        self.pipeline: list = pipeline
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
                    try:
                        self.container.stop()
                    except NotFound:
                        pass
                    finally:
                        self.container = None

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

        run_model_file = Path(deploy_files_dir, 'run_model.sh')
        if run_model_file.is_file():
            run_model_file.rename(deploy_files_dir / model_config['RUN_FILE'])

        dockerignore_file = Path(deploy_files_dir, 'dockerignore')
        if dockerignore_file.is_file():
            dockerignore_file.rename(deploy_files_dir / '.dockerignore')

        # move Kubernetes configs
        kuber_config_path = kuber_configs_dir / model_config['FULL_MODEL_NAME']
        if kuber_config_path.is_dir() and not kuber_config_path.samefile('/'):
            shutil.rmtree(kuber_config_path, ignore_errors=True)
        kuber_config_path.mkdir(parents=True, exist_ok=True)

        kuber_dp_file = Path(deploy_files_dir, 'kuber_dp.yaml')
        if kuber_dp_file.is_file():
            kuber_dp_file.rename(deploy_files_dir / model_config['KUBER_DP_FILE'])
            Path(deploy_files_dir / model_config['KUBER_DP_FILE']).rename(
                kuber_config_path / model_config['KUBER_DP_FILE'])

        kuber_lb_file = Path(deploy_files_dir, 'kuber_lb.yaml')
        if kuber_lb_file.is_file():
            kuber_lb_file.rename(deploy_files_dir / model_config['KUBER_LB_FILE'])
            Path(deploy_files_dir / model_config['KUBER_LB_FILE']).rename(
                kuber_config_path / model_config['KUBER_LB_FILE'])

        # move model building files
        model_path = models_dir / model_config['FULL_MODEL_NAME']
        safe_delete_path(model_path)
        deploy_files_dir.rename(model_path)

        if model_config['serialize_config']:
            model_config_path: Path = model_path / 'deployment_config.json'
            with model_config_path.open('w') as f:
                json.dump(model_config, f, indent=2)

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

        model_config: dict = self.config['models'][deployment_status.full_model_name]
        image_tag = model_config['KUBER_IMAGE_TAG']

        # TODO: think how to get rid of hardcode buildargs
        buildarg_keys = ['BASE_IMAGE', 'COMMIT', 'CONFIG', 'RUN_CMD', 'FULL_MODEL_NAME']
        buildargs = {key: model_config.get(key, '') for key in buildarg_keys}
        dumped_args = json.dumps(model_config['MODEL_ARGS'])
        # TODO: find out how to get rid of the replacement
        dumped_args = dumped_args.replace('"', '\\"').replace('[', '\\[').replace(']', '\\]')
        buildargs['MODEL_ARGS'] = dumped_args

        kwargs = {
            'path': build_dir_path,
            'tag': image_tag,
            'rm': True,
            'buildargs': buildargs
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
        local_gpu_device_index = self.config['local_gpu_device_index']

        kwargs = {
            'image': image_tag,
            'auto_remove': True,
            'detach': True,
            'ports': {container_port: container_port},
            'volumes': {local_log_dir: {'bind': container_log_dir, 'mode': 'rw'}},
            'runtime': 'nvidia',
            'devices': [f'/dev/nvidia{str(local_gpu_device_index)}']
        }

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


class PullImageDeploymentStage(AbstractDeploymentStage):
    def __init__(self, config: dict, in_queue: Queue, out_queue: Queue):
        stage_name = 'pull from cluster repo'
        super(PullImageDeploymentStage, self).__init__(config, stage_name, in_queue, out_queue)
        self.docker_client: DockerClient = DockerClient(base_url=config['docker_base_url'])

    def _act(self, deployment_status: DeploymentStatus) -> DeploymentStatus:
        image_tag = self.config['models'][deployment_status.full_model_name]['KUBER_IMAGE_TAG']
        server_response_generator = self.docker_client.images.pull(image_tag)
        server_response = '\t{}'.format('\n\t'.join([str(resp_str) for resp_str in server_response_generator]))
        deployment_status.extended_stage_info = f'server response:\n{server_response}'

        return deployment_status


class AbstractKuberEntitiesHandler(AbstractDeploymentStage):
    def __init__(self, config: dict, stage_name: str, in_queue: Queue, out_queue: Queue):
        super(AbstractKuberEntitiesHandler, self).__init__(config, stage_name, in_queue, out_queue)

        kube_config.load_kube_config()
        self.kube_apps_v1_beta1_api = kube_client.AppsV1beta1Api()
        self.kube_core_v1_api = kube_client.CoreV1Api()

        self.dp_data: Optional[KuberEntityData] = None
        self.lb_data: Optional[KuberEntityData] = None

    def update_kuber_configs(self, deployment_status: DeploymentStatus) -> None:
        kuber_configs_dir: Path = self.config['paths']['kuber_configs_dir'] / deployment_status.full_model_name

        # Update Kubernetes Deployment data
        self.dp_data = None
        dp_file_name = self.config['models'][deployment_status.full_model_name]['KUBER_DP_FILE']
        dp_file = kuber_configs_dir / dp_file_name

        if dp_file.is_file():
            dp_name = self.config['models'][deployment_status.full_model_name]['KUBER_DP_NAME']
            
            with dp_file.open('r') as f:
                dp_config: dict = yaml.load(f)

            try:
                dp_namespace = dp_config['metadata']['namespace']
            except KeyError:
                dp_namespace = 'default'

            self.dp_data = KuberEntityData(dp_name, dp_namespace, dp_config)

        # Update Kubernetes Load Balancer data
        self.lb_data = None
        lb_file_name = self.config['models'][deployment_status.full_model_name]['KUBER_LB_FILE']
        lb_file = kuber_configs_dir / lb_file_name

        if lb_file.is_file():
            lb_name = self.config['models'][deployment_status.full_model_name]['KUBER_LB_NAME']
            
            with lb_file.open('r') as f:
                lb_config: dict = yaml.load(f)
                
            try:
                lb_namespace = lb_config['metadata']['namespace']
            except KeyError:
                lb_namespace = 'default'
                
            self.lb_data = KuberEntityData(lb_name, lb_namespace, lb_config)

    @abstractmethod
    def _act(self, deployment_status: DeploymentStatus) -> DeploymentStatus:
        pass


class DeployKuberDeploymentStage(AbstractKuberEntitiesHandler):
    def __init__(self, config: dict, in_queue: Queue, out_queue: Queue):
        stage_name = 'deploy in kubernetes'
        super(DeployKuberDeploymentStage, self).__init__(config, stage_name, in_queue, out_queue)

    def _act(self, deployment_status: DeploymentStatus) -> DeploymentStatus:
        self.update_kuber_configs(deployment_status)

        # create Kubernetes Deployment
        if self.dp_data:
            create_dp_kwargs = {
                'namespace':  self.dp_data.namespace,
                'body': self.dp_data.config,
                'include_uninitialized': True
            }
            self.kube_apps_v1_beta1_api.create_namespaced_deployment(**create_dp_kwargs)
            deployment_status.extended_stage_info += f'; created Deployment: {self.dp_data.name}'

        # create Kubernetes Load Balancer
        if self.lb_data:
            create_lb_kwargs = {
                'namespace': self.lb_data.namespace,
                'body': self.lb_data.config,
                'include_uninitialized': True
            }
            self.kube_core_v1_api.create_namespaced_service(**create_lb_kwargs)
            deployment_status.extended_stage_info += f'; created Load Balancer: {self.lb_data.name}'

        deployment_status.extended_stage_info.strip('; ')

        return deployment_status


class DeleteKuberDeploymentStage(AbstractKuberEntitiesHandler):
    def __init__(self, config: dict, in_queue: Queue, out_queue: Queue):
        stage_name = 'delete kubernetes deployment'
        super(DeleteKuberDeploymentStage, self).__init__(config, stage_name, in_queue, out_queue)

    def _act(self, deployment_status: DeploymentStatus) -> DeploymentStatus:
        self.update_kuber_configs(deployment_status)

        # remove Kubernetes Deployment
        if self.dp_data:
            deployments_raw = self.kube_apps_v1_beta1_api.list_namespaced_deployment(namespace=self.dp_data.namespace)
            deployments = [item.metadata.name for item in deployments_raw.items]

            if self.dp_data.name in deployments:
                delete_dp_kwargs = {
                    'name': self.dp_data.name,
                    'namespace': self.dp_data.namespace,
                    'body': kube_client.V1DeleteOptions(propagation_policy='Background')
                }
                self.kube_apps_v1_beta1_api.delete_namespaced_deployment(**delete_dp_kwargs)
                deployment_status.extended_stage_info += f'; deleted Deployment: {self.dp_data.name}'
            else:
                deployment_status.extended_stage_info += f'; Deployment not exists: {self.dp_data.name}'

        # remove Kubernetes Load Balancer
        if self.lb_data:
            load_balancers_raw = self.kube_core_v1_api.list_namespaced_service(namespace=self.lb_data.namespace)
            load_balancers = [item.metadata.name for item in load_balancers_raw.items]

            if self.lb_data.name in load_balancers:
                delete_lb_kwargs = {
                    'name': self.lb_data.name,
                    'namespace': self.lb_data.namespace,
                    'body': kube_client.V1DeleteOptions(propagation_policy='Background')
                }
                self.kube_core_v1_api.delete_namespaced_service(**delete_lb_kwargs)
                deployment_status.extended_stage_info += f'; deleted Load Balancer: {self.lb_data.name}'
            else:
                deployment_status.extended_stage_info += f'; Load Balancer not exists: {self.lb_data.name}'

        deployment_status.extended_stage_info.strip('; ')

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

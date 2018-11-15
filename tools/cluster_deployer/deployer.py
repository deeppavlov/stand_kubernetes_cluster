import shutil
import logging
import sys
from queue import Empty
from traceback import format_exception
from typing import Optional
from enum import Enum
from datetime import datetime
from collections import namedtuple
from pathlib import Path
from abc import ABCMeta, abstractmethod
from multiprocessing import Process, Queue, Event

from docker import DockerClient

from tools.cluster_deployer.utils import safe_delete_path, fill_placeholders_from_dict


Logger = logging.getLoggerClass()
DeployerStage = namedtuple('DeployerStage', ['stage', 'stage_name', 'in_queue', 'out_queue'])


class LogLevel(Enum):
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR


class DeploymentStatus:
    def __init__(self, full_model_name: str):
        self.full_model_name: str = full_model_name
        self.finish: bool = False
        self.log_level: Optional[LogLevel] = None
        self.log_message: Optional[str] = None


class Deployer:
    def __init__(self, config: dict, pipeline: list):
        self.config: dict = config
        self.stages: list = []
        self.full_model_names: set = set()

        self.pipline: list = pipeline
        self.pipline.append(FinalDeploymentStage)

        utc_timestamp_str = datetime.strftime(datetime.utcnow(), '%Y-%m-%d_%H-%M-%S_%f')
        log_file_name = f'{utc_timestamp_str}_deployment.log'
        self.logger: Logger = self._get_logger(self.config['paths']['log_dir'] / log_file_name)

        for stage_class in self.pipline:
            in_queue = Queue()
            out_queue = Queue()

            stage_instance: AbstractDeploymentStage = stage_class(self.config, in_queue, out_queue)
            stage_instance.start()

            stage = DeployerStage(stage=stage_instance, stage_name=stage_instance.stage_name,
                                  in_queue=in_queue, out_queue=out_queue)

            self.stages.append(stage)

    def _get_logger(self, log_file_path: Path) -> Logger:
        self.config['paths']['log_dir'].mkdir(parents=True, exist_ok=True)

        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        return logger

    def deploy(self, full_model_names: list) -> None:
        first_stage: AbstractDeploymentStage = self.stages[0]
        self.full_model_names = set(full_model_names)

        for full_model_name in full_model_names:
            deployment_status = DeploymentStatus(full_model_name)
            self.logger.info(f'Starting {first_stage.stage_name} deploying stage '
                             f'for {deployment_status.full_model_name}')
            first_stage.in_queue.put(deployment_status)

        while len(self.full_model_names) > 0:
            for stage_i, stage in enumerate(self.stages):
                stage: AbstractDeploymentStage = stage

                try:
                    deployment_status: DeploymentStatus = stage.out_queue.get_nowait()
                except Empty:
                    deployment_status = None

                if deployment_status:
                    self.logger.log(deployment_status.log_level.value, deployment_status.log_message)
                    if deployment_status.finish:
                        self.full_model_names = self.full_model_names - {*[deployment_status.full_model_name]}
                    else:
                        next_stage: AbstractDeploymentStage = self.stages[stage_i + 1]
                        self.logger.info(f'Starting {next_stage.stage_name} deploying stage '
                                         f'for {deployment_status.full_model_name}')
                        next_stage.in_queue.put(deployment_status)

        for stage in self.stages:
            stage: DeployerStage = stage
            stage.stage.terminate()

        safe_delete_path(self.config['paths']['temp_dir'])


class AbstractDeploymentStage(Process, metaclass=ABCMeta):
    def __init__(self, config: dict, stage_name: str, in_queue: Queue, out_queue: Queue):
        super(AbstractDeploymentStage, self).__init__()
        self.config = config
        self.stage_name: str = stage_name
        self.in_queue: Queue = in_queue
        self.out_queue: Queue = out_queue
        self.exit: Event = Event()

    def run(self) -> None:
        while True:
            deployment_status = self.in_queue.get()

            try:
                deployment_status = self._act(deployment_status)
            except Exception:
                deployment_status.finish = True
                exc_type, exc_value, exc_tb = sys.exc_info()
                tr = '\n'.join(format_exception(exc_type, exc_value, exc_tb))
                deployment_status.log_level = LogLevel.ERROR
                deployment_status.log_message = f'Error occurred during {self.stage_name} for ' \
                                                f'{deployment_status.full_model_name} stage:\n{tr}'

            self.out_queue.put(deployment_status)

    @abstractmethod
    def _act(self, deployment_status: DeploymentStatus) -> DeploymentStatus:
        pass


class MakeFilesDeploymentStage(AbstractDeploymentStage):
    def __init__(self, config: dict, in_queue: Queue, out_queue: Queue):
        stage_name = 'Make Deployment Files'
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

        deploy_files_dir = Path(temp_dir, f'{model_config["PREFIX"]}_{model_config["MODEL_NAME"]}').resolve()
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

        deployment_status.log_level = LogLevel.INFO
        deployment_status.log_message = f'Finished making deployment files for {deployment_status.full_model_name}'

        return deployment_status


class BuildImageDeploymentStage(AbstractDeploymentStage):
    def __init__(self, config: dict, in_queue: Queue, out_queue: Queue):
        stage_name = 'Build Docker Image'
        super(BuildImageDeploymentStage, self).__init__(config, stage_name, in_queue, out_queue)
        self.docker_client: DockerClient = DockerClient(base_url=config['docker_base_url'])

    def _act(self, deployment_status: DeploymentStatus) -> DeploymentStatus:
        models_dir_path = self.config['paths']['models_dir']
        build_dir_path = str(models_dir_path / deployment_status.full_model_name)
        image_tag = self.config['models'][deployment_status.full_model_name]['KUBER_IMAGE_TAG']
        self.docker_client.images.build(path=build_dir_path,
                                        tag=image_tag,
                                        rm=True)

        deployment_status.log_level = LogLevel.INFO
        deployment_status.log_message = f'Finished building docker image for {deployment_status.full_model_name}'

        return deployment_status


class FinalDeploymentStage(AbstractDeploymentStage):
    def __init__(self, config: dict, in_queue: Queue, out_queue: Queue):
        stage_name = 'Finish Deployment'
        super(FinalDeploymentStage, self).__init__(config, stage_name, in_queue, out_queue)

    def _act(self, deployment_status: DeploymentStatus) -> DeploymentStatus:
        deployment_status.finish = True
        deployment_status.log_level = LogLevel.INFO
        deployment_status.log_message = f'DEPLOYMENT FINISHED for {deployment_status.full_model_name}'

        return deployment_status

import argparse
import json
import shutil
import re
import logging
from queue import Empty
from traceback import print_exc, print_stack
from typing import Optional
from enum import Enum
from datetime import datetime
from collections import namedtuple
from pathlib import Path
from abc import ABCMeta, abstractmethod
from multiprocessing import Process, Queue, Event

from tools.cluster_deployer.utils import safe_delete_path

Logger = logging.getLoggerClass()
DeployerStage = namedtuple('DeployerStage', ['stage', 'stage_name', 'in_queue', 'out_queue'])

parser = argparse.ArgumentParser()
parser.add_argument('-m', '--model', help='full model name with prefix', type=str)
parser.add_argument('-g', '--group', help='model group name', type=str)
parser.add_argument('-c', '--custom', action='store_true', help='generate deploying files for editing')
parser.add_argument('-l', '--list', action='store_true', help='list available models from config')


def fill_placeholders_from_dict(str_in: str, values_dict: dict) -> str:
    pattern = r'{{([A-Za-z_]+)}}'
    str_out = re.sub(pattern,
                     lambda x: json.dumps(values_dict[x.group(1)])
                     if isinstance(values_dict[x.group(1)], (list, dict))
                     else str(values_dict[x.group(1)]),
                     str_in)
    return str_out


def fill_dict_placeholders_recursive(dict_in: dict) -> dict:
    pattern = r'{{([A-Za-z_]+)}}'
    dict_out = {}
    completed = True

    for key, value in dict_in.items():
        dict_out[key] = fill_placeholders_from_dict(value, dict_in)
        completed &= not bool(re.search(pattern, dict_out[key]))

    dict_out = dict_out if completed else fill_dict_placeholders_recursive(dict_out)

    return dict_out


def make_config_from_file(config_path: Path, root_dir: Path) -> dict:
    with open(str(config_path), 'r') as f:
        config = json.load(f)

    # make paths
    config['paths']['root_dir'] = str(root_dir)
    config['paths'] = fill_dict_placeholders_recursive(config['paths'])
    config['paths'] = {key: Path(value) for key, value in config['paths'].items()}

    # make model configs
    config['models_list'] = config['models']
    config['models'] = {}

    for model_config in config['models_list']:
        model_config['FULL_MODEL_NAME'] = f'{model_config["PREFIX"]}_{model_config["MODEL_NAME"]}'
        model_config['FULL_MODEL_NAME_DASHED'] = model_config['FULL_MODEL_NAME'].replace('_', '-')

        model_config['LOG_FILE'] = f'{model_config["PREFIX"]}_{model_config["MODEL_NAME"]}.log'
        model_config['RUN_FILE'] = f'run_{model_config["MODEL_NAME"]}.sh'
        model_config['KUBER_DP_FILE'] = f'{model_config["PREFIX"]}_{model_config["MODEL_NAME"]}_dp.yaml'
        model_config['KUBER_LB_FILE'] = f'{model_config["PREFIX"]}_{model_config["MODEL_NAME"]}_lb.yaml'

        # TODO: remove models_subdir from config (was made for run_model.sh compatibility)
        model_config['MODELS_FOLDER'] = str(config['paths']['models_subdir']) + '/'

        model_config['KUBER_DP_NAME'] = f'{model_config["FULL_MODEL_NAME_DASHED"]}-dp'
        model_config['KUBER_LB_NAME'] = f'{model_config["FULL_MODEL_NAME_DASHED"]}-lb'
        model_config['KUBER_IMAGE_TAG'] = f'{model_config["DOCKER_REGISTRY"]}/' \
                                          f'{model_config["PREFIX"]}/' \
                                          f'{model_config["MODEL_NAME"]}'
        model_config['KUBER_CONTAINER_PORT_NAME'] = f'cp{model_config["PORT"]}'

        if model_config['FULL_MODEL_NAME'] not in config['models'].keys():
            config['models'][model_config['FULL_MODEL_NAME']] = model_config
        else:
            raise KeyError(f'Double full model name: {model_config["FULL_MODEL_NAME"]}')

    return config


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
        self.pipline.append(FinalDeployerStage)

        utc_timestamp_str = datetime.strftime(datetime.utcnow(), '%Y-%m-%d_%H-%M-%S_%f')
        log_file_name = f'{utc_timestamp_str}_deployment.log'
        self.logger: Logger = self._get_logger(self.config['paths']['log_dir'] / log_file_name)

        for stage_class in self.pipline:
            in_queue = Queue()
            out_queue = Queue()

            stage_instance: AbstractDeployerStage = stage_class(self.config, in_queue, out_queue)
            stage_instance.start()

            stage = DeployerStage(stage=stage_instance, stage_name=stage_instance.stage_name,
                                  in_queue=in_queue, out_queue=out_queue)

            self.stages.append(stage)

    def _get_logger(self, log_file_path: Path) -> Logger:
        self.config['paths']['log_dir'].mkdir(parents=True, exist_ok=True)

        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        return logger

    def deploy(self, full_model_names: list) -> None:
        self.full_model_names = set(full_model_names)
        for full_model_name in full_model_names:
            deployment_status = DeploymentStatus(full_model_name)
            first_stage: AbstractDeployerStage = self.stages[0]
            self.logger.info(f'Starting {first_stage.stage_name} deploying stage '
                             f'for {deployment_status.full_model_name}')
            first_stage.in_queue.put(deployment_status)

        while len(self.full_model_names) > 0:
            for stage_i, stage in enumerate(self.stages):
                stage: AbstractDeployerStage = stage
                try:
                    deployment_status: DeploymentStatus = stage.out_queue.get_nowait()
                    self.logger.log(deployment_status.log_level.value, deployment_status.log_message)
                    if deployment_status.finish:
                        self.full_model_names = self.full_model_names - {*[deployment_status.full_model_name]}
                    else:
                        next_stage: AbstractDeployerStage = self.stages[stage_i + 1]
                        self.logger.info(f'Starting {next_stage.stage_name} deploying stage '
                                         f'for {deployment_status.full_model_name}')
                        next_stage.in_queue.put(deployment_status)
                except Empty:
                    pass

        for stage in self.stages:
            stage.stage.terminate()

        safe_delete_path(self.config['paths']['temp_dir'])


class AbstractDeployerStage(Process, metaclass=ABCMeta):
    def __init__(self, config: dict, stage_name: str, in_queue: Queue, out_queue: Queue):
        super(AbstractDeployerStage, self).__init__()
        self.config = config
        self.stage_name: str = stage_name
        self.in_queue: Queue = in_queue
        self.out_queue: Queue = out_queue
        self.exit: Event = Event()

    def run(self) -> None:
        while True:
            in_deployment_status = self.in_queue.get()
            out_deployment_status = self._act(in_deployment_status)
            self.out_queue.put(out_deployment_status)

    @abstractmethod
    def _act(self, deployment_status: DeploymentStatus) -> DeploymentStatus:
        pass


class MakeFilesDeployerStage(AbstractDeployerStage):
    def __init__(self, config: dict, in_queue: Queue, out_queue: Queue):
        stage_name = 'Make Files'
        super(MakeFilesDeployerStage, self).__init__(config, stage_name, in_queue, out_queue)

    def _act(self, deployment_status: DeploymentStatus) -> DeploymentStatus:
        try:
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

            deployment_status.finish = True
            deployment_status.log_level = LogLevel.INFO
            deployment_status.log_message = f'Finished deployment for {deployment_status.full_model_name}'

        except Exception:
            tr = print_stack()
            deployment_status.log_level = LogLevel.ERROR
            deployment_status.log_message = f'Error occurred during {self.stage_name} stage:\n{tr}'

        finally:
            return deployment_status


class FinalDeployerStage(AbstractDeployerStage):
    def __init__(self, config: dict, in_queue: Queue, out_queue: Queue):
        stage_name = 'Finish Deployment'
        super(FinalDeployerStage, self).__init__(config, stage_name, in_queue, out_queue)

    def _act(self, deployment_status: DeploymentStatus) -> DeploymentStatus:
        try:
            deployment_status.finish = True
            deployment_status.log_level = LogLevel.INFO
            deployment_status.log_message = f'Finished deployment for {deployment_status.full_model_name}'

        except Exception:
            tr = print_stack()
            deployment_status.log_level = LogLevel.ERROR
            deployment_status.log_message = f'Error occurred during {self.stage_name} stage:\n{tr}'

        finally:
            return deployment_status


def deploy() -> None:
    args = parser.parse_args()
    model = args.model
    group = args.group
    custom = args.custom
    list = args.list

    config_file_path = Path(__file__, '..').resolve() / 'config.json'
    config = make_config_from_file(config_file_path, Path(__file__, '..', '..', '..').resolve())

    #pipeline = []
    pipeline = [MakeFilesDeployerStage]
    deployer = Deployer(config, pipeline)
    deployer.deploy(['stand_ner_ru'])


if __name__ == '__main__':
    deploy()

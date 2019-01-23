import logging
from queue import Empty
from datetime import datetime
from multiprocessing import Queue
from typing import Optional
from copy import deepcopy

from deployer_utils import safe_delete_path
from deployer_stages import DeploymentStatus, LogMessage, AbstractDeploymentStage
from pipelines import all_stages, preset_pipelines


Logger = logging.getLoggerClass()


class Deployer:
    def __init__(self, config: dict):
        self.config: dict = config
        self.stages: dict = {}
        self.current_task: Optional[dict] = None

        for stage_class in all_stages:
            in_queue = Queue()
            out_queue = Queue()
            stage_instance: AbstractDeploymentStage = stage_class(self.config, in_queue, out_queue)
            stage_instance.start()
            self.stages[stage_class.__name__] = stage_instance

    def _setup_loggers(self, full_model_names: list) -> None:
        self.config['paths']['log_dir'].mkdir(parents=True, exist_ok=True)
        utc_timestamp_str = datetime.strftime(datetime.utcnow(), '%Y-%m-%d_%H-%M-%S_%f')

        for full_model_name in full_model_names:
            logger = logging.getLogger(full_model_name)
            logger.setLevel(logging.DEBUG)

            log_file_name = f'{utc_timestamp_str}_{full_model_name}.log'
            log_file_path = self.config['paths']['log_dir'] / log_file_name

            file_handler = logging.FileHandler(log_file_path)
            file_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    def deploy(self, full_model_names: list) -> None:
        self.current_task = set(full_model_names)
        full_model_names = list(self.current_task)
        self._setup_loggers(full_model_names + ['_task_info'])

        task_info = []

        for full_model_name in full_model_names:
            pipeline_name = self.config['models'][full_model_name]['pipeline']
            pipeline = deepcopy(preset_pipelines[pipeline_name]['pipeline'])
            deployment_status = DeploymentStatus(full_model_name, pipeline)

            info_str = f'\t[{full_model_name}]:\t\t[{", ".join([stage.__name__ for stage in pipeline])}]'
            task_info.append(info_str)

            first_stage_class_name = deployment_status.pipeline.pop(0).__name__
            first_stage: AbstractDeploymentStage = self.stages[first_stage_class_name]
            first_stage.in_queue.put(deployment_status)

        logger: Logger = logging.getLogger('_task_info')
        task_info = '\n'.join(task_info)
        logger.info(f'Created task:\n{task_info}')

        while len(self.current_task) > 0:
            for stage in self.stages.values():
                stage: AbstractDeploymentStage = stage

                try:
                    q_get = stage.out_queue.get_nowait()
                except Empty:
                    q_get = None

                if isinstance(q_get, DeploymentStatus):
                    deployment_status: DeploymentStatus = q_get

                    if deployment_status.finish:
                        self.current_task = self.current_task - {deployment_status.full_model_name}
                    elif deployment_status.pipeline:
                        next_stage: AbstractDeploymentStage = self.stages[deployment_status.pipeline.pop(0).__name__]
                        next_stage.in_queue.put(deployment_status)
                    elif not deployment_status.pipeline:
                        self.current_task = self.current_task - {deployment_status.full_model_name}
                        logger: Logger = logging.getLogger(deployment_status.full_model_name)
                        logger.info(f'[{deployment_status.full_model_name}] DEPLOYMENT FINISHED')

                elif isinstance(q_get, LogMessage):
                    log_message: LogMessage = q_get
                    logger: Logger = logging.getLogger(log_message.full_model_name)

                    if self.config['extended_deployer_logging'] and log_message.extended_log_message:
                        log_text = f'{log_message.log_message}, extended info: {log_message.extended_log_message}'
                    else:
                        log_text = log_message.log_message

                    logger.log(log_message.log_level.value, log_text)

        for stage in self.stages.values():
            stage.terminate()

        safe_delete_path(self.config['paths']['temp_dir'])

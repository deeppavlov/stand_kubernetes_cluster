import logging
from queue import Empty
from datetime import datetime
from collections import namedtuple
from multiprocessing import Queue

from deployer_utils import safe_delete_path
from deployer_stages import DeploymentStatus, LogMessage, AbstractDeploymentStage, FinalDeploymentStage


Logger = logging.getLoggerClass()
DeployerStage = namedtuple('DeployerStage', ['stage', 'stage_name', 'in_queue', 'out_queue'])


class Deployer:
    def __init__(self, config: dict, pipeline: list):
        self.config: dict = config
        self.stages: list = []
        self.full_model_names: set = set()

        self.pipline: list = pipeline
        self.pipline.append(FinalDeploymentStage)

        for stage_class in self.pipline:
            in_queue = Queue()
            out_queue = Queue()

            stage_instance: AbstractDeploymentStage = stage_class(self.config, in_queue, out_queue)
            stage_instance.start()

            stage = DeployerStage(stage=stage_instance, stage_name=stage_instance.stage_name,
                                  in_queue=in_queue, out_queue=out_queue)

            self.stages.append(stage)

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
        first_stage: AbstractDeploymentStage = self.stages[0]
        self.full_model_names = set(full_model_names)
        self._setup_loggers(full_model_names)

        for full_model_name in full_model_names:
            deployment_status = DeploymentStatus(full_model_name)
            first_stage.in_queue.put(deployment_status)

        while len(self.full_model_names) > 0:
            for stage_i, stage in enumerate(self.stages):
                stage: AbstractDeploymentStage = stage

                try:
                    q_get = stage.out_queue.get_nowait()
                except Empty:
                    q_get = None

                if isinstance(q_get, DeploymentStatus):
                    deployment_status: DeploymentStatus = q_get

                    if deployment_status.finish:
                        self.full_model_names = self.full_model_names - {*[deployment_status.full_model_name]}
                    else:
                        next_stage: AbstractDeploymentStage = self.stages[stage_i + 1]
                        next_stage.in_queue.put(deployment_status)

                elif isinstance(q_get, LogMessage):
                    log_message: LogMessage = q_get
                    logger: Logger = logging.getLogger(log_message.full_model_name)

                    if self.config['extended_deployer_logging'] and log_message.extended_log_message:
                        log_text = f'{log_message.log_message}, extended info: {log_message.extended_log_message}'
                    else:
                        log_text = log_message.log_message

                    logger.log(log_message.log_level.value, log_text)

        for stage in self.stages:
            stage: DeployerStage = stage
            stage.stage.terminate()

        safe_delete_path(self.config['paths']['temp_dir'])

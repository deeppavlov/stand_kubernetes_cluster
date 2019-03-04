import json
import yaml
import shutil
import re
from pathlib import Path
from datetime import datetime, timedelta
from threading import Timer
from queue import Queue
from typing import Callable, Any, Tuple, Optional


def safe_delete_path(path: Path):
    if path.exists():
        if not path.samefile('/'):
            if path.is_dir():
                shutil.rmtree(str(path), ignore_errors=True)
            elif path.is_file():
                path.unlink()
        else:
            raise OSError.filename('root path deletion attempt')


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
        if isinstance(value, str):
            dict_out[key] = fill_placeholders_from_dict(value, dict_in)
            completed &= not bool(re.search(pattern, dict_out[key]))
        else:
            dict_out[key] = value

    dict_out = dict_out if completed else fill_dict_placeholders_recursive(dict_out)

    return dict_out


def make_config_from_files(config_dir_path: Path, root_dir: Path, models_config_path: Optional[Path] = None) -> dict:
    config_file_path = config_dir_path / 'config.yaml'
    model_groups_path = config_dir_path / 'model_groups.yaml'
    templates_path = config_dir_path / 'templates.yaml'
    model_configs_path = config_dir_path / 'models'

    with config_file_path.open('r') as f:
        config: dict = yaml.load(f)

    with model_groups_path.open('r') as f:
        model_groups: dict = yaml.load(f)

    with templates_path.open('r') as f:
        templates: dict = yaml.load(f)

    models = {}
    for models_config_file in model_configs_path.iterdir():
        if models_config_file.is_file():
            with models_config_file.open('r') as f:
                model_configs = yaml.load(f)
                models.update(**model_configs)

    if models_config_path:
        with models_config_path.open('r') as f:
            models_merge_config: dict = yaml.load(f)
    else:
        models_merge_config = {}

    # make paths
    config['paths']['root_dir'] = str(root_dir)
    config['paths'] = fill_dict_placeholders_recursive(config['paths'])
    config['paths'] = {key: Path(value) for key, value in config['paths'].items()}

    # add model groups
    config['model_groups'] = model_groups

    # make model configs
    config['models'] = {}

    for model_full_name, model_config_params in models.items():
        # all capitalised keys are used in deploy files placeholders filling
        model_config = templates['_root']  # get config params from root template

        pattern = r'(.+?)_(.+)'
        match = re.search(pattern, model_full_name)

        if not match:
            raise KeyError(f'Wrong model full name: {model_full_name}, should be in <prefix>_<model_name> fromat')
        else:
            model_config['FULL_MODEL_NAME'] = model_full_name
            model_config['PREFIX'] = match.group(1)
            model_config['MODEL_NAME'] = match.group(2)

        # TODO: uncapitalize template
        model_config.update(**templates[model_config_params['TEMPLATE']])  # get config params from model template
        model_config.update(**model_config_params)  # get config params from model config
        model_config.update(**models_merge_config.get(model_full_name, {}))  # merge with external model config file
        model_config: dict = fill_dict_placeholders_recursive(model_config)  # fill model config placeholders

        run_mode: str = model_config['run_mode']
        run_params: dict = model_config.get('run_params', {})
        flags: list = run_params.pop('_flags', [])
        params: list = [f"{param} {value}" for param, value in run_params.items()]
        model_config['RUN_CMD'] = f' {run_mode} {" ".join(flags)} {" ".join(params)} '

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


# TODO: needs refactoring
def poll(probe: Callable, interval_sec: float, timeout_sec: float,
         estimator: Callable, *args, **kwargs) -> Tuple[Any, timedelta]:

    interval_sec = 0.001 if interval_sec < 0.001 else round(interval_sec, 3)
    timeout_sec = 0.001 if timeout_sec < 0.001 else round(timeout_sec, 3)

    queue = Queue()

    def set_timer(in_timestamp: datetime, in_timeout: timedelta):
        if datetime.utcnow() >= in_timestamp + in_timeout:
            q_out = {'result': None, 'timeout': True, 'polling_time': None}
            queue.put(q_out)
        else:
            try:
                result = probe(*args, **kwargs)
            except Exception:
                result = None

            if result and estimator(result):
                q_out = {'result': result, 'timeout': False, 'polling_time': datetime.utcnow() - in_timestamp}
                queue.put(q_out)
            else:
                in_timer = Timer(interval_sec, set_timer, [timestamp, timeout])
                in_timer.start()

    timestamp = datetime.utcnow()
    timeout = timedelta(seconds=timeout_sec)

    timer = Timer(interval_sec, set_timer, [timestamp, timeout])
    timer.start()

    while True:
        q_in = queue.get()
        if q_in['timeout']:
            _ = probe(*args, **kwargs)
            raise TimeoutError
        else:
            return q_in['result'], q_in['polling_time']


def prompt_confirmation(question: str, default: Optional[str] = None) -> bool:
    valid_map = {'y': True, 'yes': True, 'n': False, 'no': False}
    prompt_map = {None: '[y/n]', 'yes': '[Y/n]', 'no': '[y/N]'}

    if default not in prompt_map.keys():
        raise ValueError('default option should be None, "yes" or "no"')

    confirm = input(f"{question} {prompt_map[default]}: ").lower().strip()

    if not confirm and default:
        return prompt_confirmation(default, default)
    elif confirm in valid_map.keys():
        return valid_map[confirm]
    else:
        return prompt_confirmation(question, default)

import json
import shutil
import re
from pathlib import Path


def safe_delete_path(path: Path):
    if path.exists():
        if not path.samefile('/'):
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
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

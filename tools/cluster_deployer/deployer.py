import argparse
import json
import shutil
import re
from pathlib import Path

MODELS_FOLDER = 'models/'

root_dir = Path(__file__, '..', '..', '..').resolve()
deployer_dir = root_dir / 'tools' / 'cluster_deployer'
templates_dir = root_dir / 'tools' / 'add_dp_model' / 'templates'
models_dir = root_dir / MODELS_FOLDER
kuber_configs_dir = root_dir / 'kuber_configs' / 'models'
temp_dir = deployer_dir / 'temp'
results_dir = deployer_dir / 'results'
config_file_path = deployer_dir / 'config.json'

parser = argparse.ArgumentParser()
parser.add_argument('-m', '--model', help='full model name with prefix', type=str)
parser.add_argument('-g', '--group', help='model group name', type=str)
parser.add_argument('-c', '--custom', action='store_true', help='generate deploying files for editing')
parser.add_argument('-l', '--list', action='store_true', help='list available models from config')


def make_config_from_file(config_path: Path) -> dict:
    with open(str(config_path), 'r') as f:
        config = json.load(f)

    config['models_list'] = config['models']
    config['models'] = {}

    for model_config in config['models_list']:
        model_config['FULL_MODEL_NAME'] = f'{model_config["PREFIX"]}_{model_config["MODEL_NAME"]}'
        model_config['FULL_MODEL_NAME_DASHED'] = model_config['FULL_MODEL_NAME'].replace('_', '-')

        model_config['LOG_FILE'] = f'{model_config["PREFIX"]}_{model_config["MODEL_NAME"]}.log'
        model_config['RUN_FILE'] = f'run_{model_config["MODEL_NAME"]}.sh'
        model_config['KUBER_DP_FILE'] = f'{model_config["PREFIX"]}_{model_config["MODEL_NAME"]}_dp.yaml'
        model_config['KUBER_LB_FILE'] = f'{model_config["PREFIX"]}_{model_config["MODEL_NAME"]}_lb.yaml'
        model_config['MODELS_FOLDER'] = MODELS_FOLDER

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


def get_dir_files_recursive(path: Path) -> list:
    result = []

    for item in path.iterdir():
        if item.is_dir():
            result.extend(get_dir_files_recursive(item))
        else:
            result.append(item)

    return result


def make_deployment_files(model_config: dict, make: bool = True, move: bool = True) -> None:
    deploy_files_dir = Path(temp_dir, f'{model_config["PREFIX"]}_{model_config["MODEL_NAME"]}').resolve()

    if not (make or move):
        raise ValueError(f'At least one of make and move params must be True')

    if make:
        if temp_dir.is_dir() and not temp_dir.samefile('/'):
            shutil.rmtree(temp_dir, ignore_errors=True)

        shutil.copytree(templates_dir / model_config['TEMPLATE'], deploy_files_dir)
        deploy_files = get_dir_files_recursive(deploy_files_dir)

        for deploy_file in deploy_files:
            with open(deploy_file, 'r') as f:
                file = f.read()

            pattern = r'{{([A-Z_]+)}}'
            result = re.sub(pattern,
                            lambda x: json.dumps(model_config[x.group(1)])
                            if isinstance(model_config[x.group(1)], list)
                            else str(model_config[x.group(1)]),
                            file)

            with open(deploy_file, 'w') as f:
                f.write(result)

        Path(deploy_files_dir, 'kuber_dp.yaml').rename(deploy_files_dir / model_config['KUBER_DP_FILE'])
        Path(deploy_files_dir, 'kuber_lb.yaml').rename(deploy_files_dir / model_config['KUBER_LB_FILE'])
        Path(deploy_files_dir, 'run_model.sh').rename(deploy_files_dir / model_config['RUN_FILE'])
        Path(deploy_files_dir, 'dockerignore').rename(deploy_files_dir / '.dockerignore')

    if move:
        # move Kubernetes configs
        kuber_config_path = kuber_configs_dir / model_config['FULL_MODEL_NAME']
        if kuber_config_path.is_dir() and not kuber_config_path.samefile('/'):
            shutil.rmtree(kuber_config_path, ignore_errors=True)
        kuber_config_path.mkdir(parents=True, exist_ok=True)
        Path(deploy_files_dir / model_config['KUBER_DP_FILE']).rename(kuber_config_path / model_config['KUBER_DP_FILE'])
        Path(deploy_files_dir / model_config['KUBER_LB_FILE']).rename(kuber_config_path / model_config['KUBER_LB_FILE'])

        # move model building files
        model_path = models_dir / model_config['FULL_MODEL_NAME']
        if model_path.is_dir() and not model_path.samefile('/'):
            shutil.rmtree(model_path, ignore_errors=True)
        deploy_files_dir.rename(model_path)


def deploy():
    args = parser.parse_args()
    model = args.model
    group = args.group
    custom = args.custom
    list = args.list

    config = make_config_from_file(config_file_path)
    make_deployment_files(config['models']['stand_ner_ru'])


if __name__ == '__main__':
    deploy()

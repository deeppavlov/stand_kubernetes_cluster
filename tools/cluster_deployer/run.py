import argparse
from pathlib import Path

from docker import DockerClient
from docker.errors import APIError

from pipelines import preset_pipelines
from deployer_utils import make_config_from_files, prompt_confirmation
from deployer import Deployer

parser = argparse.ArgumentParser()
parser.add_argument('action', help='select action', type=str, choices={'build', 'models', 'groups', 'pipelines'})

parser.add_argument('-c', '--models-config', default=None, help='path to models overriding config', type=str)

parser.add_argument('-m', '--model', default=None, help='full model name with prefix', type=str)
parser.add_argument('-g', '--group', default=None, help='model group name', type=str)
parser.add_argument('-p', '--pipeline', default=None, help='pipeline name', type=str)

parser.add_argument('-d', '--dockerhub-pass', default=None, help='Docker Hub password', type=str)


def build(config: dict, args: argparse.Namespace) -> None:
    model = args.model
    group = args.group
    pipeline = args.pipeline

    if group:
        models = config['model_groups'].get(group)
        if not models:
            print(f'Group {group} does not exist or empty')
            return
    elif model:
        models = [model]
    else:
        print('Please, specify group or model full name')
        return

    absent_models = set(models) - set(config['models'].keys())
    if len(absent_models) > 0:
        absent_models = ', '.join(absent_models)
        print(f'Unknown model full names: {absent_models}')
        return

    if pipeline and pipeline not in preset_pipelines.keys():
        print(f'Unknown pipeline name: {pipeline}')
        return
    elif pipeline:
        for model in models:
            config['models'][model]['pipeline'] = pipeline
    else:
        absent_pipeline_models = []
        for model in models:
            if config['models'][model].get('pipeline') not in preset_pipelines.keys():
                absent_pipeline_models.append(model)
        if absent_pipeline_models:
            absent_pipeline_models = ', '.join(absent_pipeline_models)
            print(f'Incorrect or absent pipeline names for: {absent_pipeline_models}')
            return

    # Test Docker Hub authentication
    dockerhub_password = args.dockerhub_pass

    if not dockerhub_password:
        prompt_text = 'Docker Hub password was not entered, would you like for proceed without Docker Hub login?'
        if not prompt_confirmation(prompt_text):
            return
    else:
        try:
            client: DockerClient = DockerClient(base_url=config['docker_base_url'])
            client.login(config['dockerhub_registry'], dockerhub_password)
        except APIError as e:
            print(e)
            prompt_text = 'Docker Hub login error occurred, would you like for proceed without Docker Hub login?'
            if not prompt_confirmation(prompt_text):
                return

    config['dockerhub_password'] = dockerhub_password

    deployer = Deployer(config)
    deployer.deploy(models)


def list_names(config: dict, args: argparse.Namespace) -> None:
    if args.action == 'models':
        models_info = [f'{model.get("PREFIX", "-")}_'
                       f'{model.get("MODEL_NAME", "-")} | '
                       f'{model.get("TEMPLATE", "-")} | '
                       f'{model.get("CONFIG_FILE", "-")}' for model in config['models'].values()]

        models_str = '\n'.join(models_info)
        print(models_str)

    if args.action == 'groups':
        groups_str = '\n'.join([f'{group}:\t\t{", ".join(models)}' for group, models in config['model_groups'].items()])
        print(groups_str)

    if args.action == 'pipelines':
        pipelines_str = '\n\n'.join([f'{name}:\t{content["description"]} '
                                     f'{str([stage.__name__ for stage in content["pipeline"]])}'
                                     for name, content in preset_pipelines.items()])

        print(pipelines_str)


# TODO: make docker running containers check and cleanup
def main() -> None:
    args = parser.parse_args()

    config_dir_path = Path(__file__, '..').resolve() / 'configs/'
    models_config_file_path = Path(args.models_config).resolve() if args.models_config else None

    config = make_config_from_files(config_dir_path,
                                    Path(__file__, '..', '..', '..').resolve(),
                                    models_config_file_path)

    if args.action == 'build':
        build(config, args)
    else:
        list_names(config, args)


if __name__ == '__main__':
    main()

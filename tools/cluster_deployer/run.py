import argparse
from pathlib import Path

from docker import DockerClient
from docker.errors import APIError

from pipelines import pipelines
from deployer_utils import make_config_from_file, prompt_confirmation
from deployer import Deployer


parser = argparse.ArgumentParser()
parser.add_argument('action', help='select action', type=str, choices={'build', 'models', 'groups', 'pipelines'})

parser.add_argument('-m', '--model', default=None, help='full model name with prefix', type=str)
parser.add_argument('-g', '--group', default=None, help='model group name', type=str)
parser.add_argument('-p', '--pipeline', default=None, help='pipeline name', type=str)

parser.add_argument('-d', '--dockerhub-pass', default=None, help='Docker Hub password', type=str)


def build(config: dict, args: argparse.Namespace) -> None:
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

    model = args.model
    group = args.group
    pipeline = args.pipeline

    if pipeline not in pipelines.keys():
        print(f'Unknown pipeline name full name: {model}')
        return

    if model:
        model_full_names = config['models'].keys()

        if model in model_full_names:
            deployer = Deployer(config, pipelines[pipeline]['pipeline'])
            deployer.deploy([model])
        else:
            print(f'Unknown model full name: {model}')

    if group:
        group_names = config['model_groups'].keys()

        if group in group_names:
            models = config['model_groups'][group]
            absent_models = set(models) - set(config['models'].keys())

            if len(absent_models) > 0:
                absent_models = ', '.join(absent_models)
                print(f'Unknown model full names: {absent_models}')
            else:
                deployer = Deployer(config, pipelines['all']['pipeline'])
                deployer.deploy(models)

        else:
            print(f'Unknown group name: {group}')


def list_names(config: dict, args: argparse.Namespace) -> None:
    if args.action == 'models':
        models_str = '\n'.join(config['models'].keys())
        print(models_str)
    if args.action == 'groups':
        groups_str = '\n'.join([f'{group}:\t\t{", ".join(models)}' for group, models in config['model_groups'].items()])
        print(groups_str)
    if args.action == 'pipelines':
        pipelines_str = '\n\n'.join([f'{name}:\t{content["description"]} '
                                     f'{str([stage.__name__ for stage in content["pipeline"]])}'
                                     for name, content in pipelines.items()])
        print(pipelines_str)


# TODO: make docker running containers check and cleanup
# TODO: implement custom pipelines for models (with pipeline dicts)
# TODO: get rid of add_dp_model util
def main() -> None:
    args = parser.parse_args()

    config_file_path = Path(__file__, '..').resolve() / 'config.json'
    config = make_config_from_file(config_file_path, Path(__file__, '..', '..', '..').resolve())

    if args.action == 'build':
        build(config, args)
    else:
        list_names(config, args)


if __name__ == '__main__':
    main()

import argparse
from pathlib import Path

from docker import DockerClient
from docker.errors import APIError

from pipelines import pipelines
from deployer_utils import make_config_from_file, prompt_confirmation
from deployer import Deployer


parser = argparse.ArgumentParser()
parser.add_argument('-m', '--model', default=None, help='full model name with prefix', type=str)
parser.add_argument('-g', '--group', default=None, help='model group name', type=str)
parser.add_argument('-c', '--custom', action='store_true', help='generate deploying files for editing')
parser.add_argument('-l', '--list', action='store_true', help='list available models from config')

parser.add_argument('-d', '--dockerhub-pass', default=None, help='Docker Hub password', type=str)


# TODO: make docker running containers check and cleanup
# TODO: implement custom pipelines for models (with pipeline dicts)
# TODO: get rid of add_dp_model util
def main() -> None:
    args = parser.parse_args()

    model = args.model
    group = args.group
    # TODO: implement custom model config making (and building models without configs making)
    custom = args.custom
    list = args.list

    dockerhub_password = args.dockerhub_pass

    config_file_path = Path(__file__, '..').resolve() / 'config.json'
    config = make_config_from_file(config_file_path, Path(__file__, '..', '..', '..').resolve())

    # Test Docker Hub authentication
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

    model_group_names = config['model_groups'].keys()
    model_full_names = config['models'].keys()

    if list:
        for model_full_name in model_full_names:
            print(model_full_name)
    elif model:
        if model in model_full_names:
            deployer = Deployer(config, FULL_CYCLE_PIPELINE)
            deployer.deploy([model])
        else:
            print(f'Unknown model full name: {model}')
    elif group:
        if group in model_group_names:
            models = config['model_groups'][group]
            absent_models = set(models) - set(config['models'].keys())
            if len(absent_models) > 0:
                absent_models = ', '.join(absent_models)
                print(f'Unknown model full names: {absent_models}')
            else:
                deployer = Deployer(config, pipelines['all']['pipeline'])
                deployer.deploy(models)
        else:
            print(f'Unknown model group name: {group}')


if __name__ == '__main__':
    main()

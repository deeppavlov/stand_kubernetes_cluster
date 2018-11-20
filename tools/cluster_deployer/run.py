import argparse
from pathlib import Path

from deployer_utils import make_config_from_file
from deployer import Deployer
from deployer import MakeFilesDeploymentStage, BuildImageDeploymentStage
from deployer import TestImageDeploymentStage, PushImageDeploymentStage
from deployer import DeployKuberDeploymentStage, TestKuberDeploymentStage

FULL_CYCLE_PIPELINE = [MakeFilesDeploymentStage, BuildImageDeploymentStage, TestImageDeploymentStage,
                       PushImageDeploymentStage, DeployKuberDeploymentStage, TestKuberDeploymentStage]

parser = argparse.ArgumentParser()
parser.add_argument('-m', '--model', default=None, help='full model name with prefix', type=str)
parser.add_argument('-g', '--group', default=None, help='model group name', type=str)
parser.add_argument('-c', '--custom', action='store_true', help='generate deploying files for editing')
parser.add_argument('-l', '--list', action='store_true', help='list available models from config')


def main() -> None:
    args = parser.parse_args()
    model = args.model
    group = args.group
    # TODO: implemet custom model config building
    custom = args.custom
    list = args.list

    config_file_path = Path(__file__, '..').resolve() / 'config.json'
    config = make_config_from_file(config_file_path, Path(__file__, '..', '..', '..').resolve())
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
        models = config['model_groups'][group]
        absent_models = set(models) - set(config['models'].keys())
        if len(absent_models) > 0:
            absent_models = ', '.join(absent_models)
            print(f'Unknown model full names: {absent_models}')
        else:
            deployer = Deployer(config, FULL_CYCLE_PIPELINE)
            deployer.deploy(models)


if __name__ == '__main__':
    main()

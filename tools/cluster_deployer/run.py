import argparse
from pathlib import Path

from tools.cluster_deployer.utils import make_config_from_file
from tools.cluster_deployer.deployer import Deployer, MakeFilesDeploymentStage, BuildImageDeploymentStage


parser = argparse.ArgumentParser()
parser.add_argument('-m', '--model', help='full model name with prefix', type=str)
parser.add_argument('-g', '--group', help='model group name', type=str)
parser.add_argument('-c', '--custom', action='store_true', help='generate deploying files for editing')
parser.add_argument('-l', '--list', action='store_true', help='list available models from config')


def main() -> None:
    args = parser.parse_args()
    model = args.model
    group = args.group
    custom = args.custom
    list = args.list

    config_file_path = Path(__file__, '..').resolve() / 'config.json'
    config = make_config_from_file(config_file_path, Path(__file__, '..', '..', '..').resolve())

    pipeline = [MakeFilesDeploymentStage, BuildImageDeploymentStage]
    deployer = Deployer(config, pipeline)
    deployer.deploy(['stand_ner_ru', 'stand_ner_en'])


if __name__ == '__main__':
    main()

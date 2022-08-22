import argparse
from pathlib import Path
import yaml
import os

skc_path = Path(__file__).resolve().parents[2]
default_output_path = skc_path / 'tools' / 'cluster_deployer' / 'configs' / 'models' / 'dream.yml'
default_dream_path = Path.home() / 'dev' / 'dream'

parser = argparse.ArgumentParser()

parser.add_argument('-d', '--dream', default=None, help='path to dream directory', type=str)
parser.add_argument('-ap', '--agent-port', default=7019, help='agent port on kubeadm', type=str)
parser.add_argument('-o', '--output', default=None, type=str)
parser.add_argument('-s', '--secret', default=None, type=str)
parser.add_argument('-v', '--version', default=None, type=str)

args = parser.parse_args()


commands = {
    'combined-classification': 'gunicorn --workers=1 --bind 0.0.0.0:8087 --timeout=300 server:app',
    'comet-atomic': 'uvicorn server:app --host 0.0.0.0 --port 8053',
    'comet-conceptnet': 'uvicorn server:app --host 0.0.0.0 --port 8065',
    'convers-evaluator-annotator': 'gunicorn --workers=1 --bind 0.0.0.0:8004 --timeout=300 server:app',
    'entity-linking': 'gunicorn  --workers=1 --timeout 500 server:app -b 0.0.0.0:8075'
}

gpu = {
    'combined-classification': 1,
    'comet-atomic': 0,
    'comet-conceptnet': 0,
    'convers-evaluator-annotator': 2,
    'entity-detection': 2,
    'entity-linking': 1,
    'fact-retrieval': 1,
    'hypothesis-scorer': 1,
    'kbqa': 2,
    'knowledge-grounding': 0,
    'knowledge-grounding-skill': '',
    'masked-lm': 0,
    'midas-classification': 0,
    'ner': 1,
    'text-qa': 8,
    'wiki-parser': '',
    'midas-predictor': '',
    'dialogpt': 8,
    'infilling': 8,
    'intent-catcher': 8
}


def get_config(dream_path, agent_port, drop_mongo=True):
    conf = os.popen(f'cd {dream_path} && AGENT_PORT={agent_port} docker-compose -f docker-compose.yml'
                    f' -f assistant_dists/dream/docker-compose.override.yml'
                    f' -f assistant_dists/dream/dev.yml'
                    f' -f assistant_dists/dream/test.yml config').read()
    conf = yaml.safe_load(conf)['services']
    if drop_mongo:
        del conf['mongo']
    return conf


def gen_models(conf, secret, version):
    _models = {}
    for key, val in conf.items():
        model_name = f'dream_{key}'
        if len(val['ports']) == 2 and key == 'agent':
            for ports in val['ports']:
                if ports['published'] != 4242:
                    val['ports'] = [ports]
                    break
        assert len(val['ports']) == 1, f'{model_name} {val["ports"]}'
        try:
            command = val['command']
        except KeyError:
            print(f'no command for {key}')
            command = commands[key]
        _models[model_name] = {
            'TEMPLATE': 'socialbot_service',
            'BASE_IMAGE': model_name,
            'CMD_SCRIPT': command,
            'CLUSTER_PORT': val['ports'][0]['published'],
            'PORT': val['ports'][0]['target']
        }
        if 'CUDA_VISIBLE_DEVICES' in val['environment']:
            _models[model_name]['CUDA_VISIBLE_DEVICES'] = gpu[key]
            if gpu[key] != '':
                _models[model_name]['NODE_LIST'] = ['gpu9']
        if secret is not None:
            _models[model_name]['SECRET_NAME'] = secret
        if version is not None:
            _models[model_name]['VERSION_TAG'] = version
    return _models


if __name__ == '__main__':
    config = get_config(args.dream or default_dream_path, args.agent_port)
    models = gen_models(config, args.secret, args.version)
    with open(args.output or default_output_path, 'w') as fout:
        yaml.safe_dump(models, fout)
    print(yaml.dump({'dream': list(models.keys())}))

#  AGENT_PORT=4242 docker-compose -f docker-compose.yml -f assistant_dists/dream/docker-compose.override.yml -f assistant_dists/dream/dev.yml -f assistant_dists/dream/test.yml up --build

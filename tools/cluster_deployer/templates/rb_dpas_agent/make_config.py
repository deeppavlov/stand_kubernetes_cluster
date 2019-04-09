import json
import yaml
from pathlib import Path


deployment_config_path = Path(__file__).resolve().parent / 'deployment_config.json'
agent_config_path = Path('/base/DeepPavlov/deeppavlov/core/agent_v2/config.yaml').resolve()

with deployment_config_path.open('r') as f:
    deployment_config: dict = json.load(f)

agent_config = deployment_config['agent_config']
agent_config['use_config'] = True

with agent_config_path.open('w') as f:
    yaml.safe_dump(agent_config, f)

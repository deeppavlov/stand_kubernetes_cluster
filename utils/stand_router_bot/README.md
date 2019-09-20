# Router Bot

## Build
```
docker build -t <cluster_registry_url>/stand/router_bot .
```

Where:
* `cluster_registry_url` - cluster Docker registry URL

Current cluster Docker registry URL is:
`kubeadm.ipavlov.mipt.ru:5000`

## Usage
1. Ssh to router bot container
2. Run `routerstart` to start router bot
3. Run `routerstop` to stop router bot
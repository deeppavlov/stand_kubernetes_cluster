# MongoDB Docker
Build with:
```
docker build --build-arg MONGO_DOCKER_TAG=<mongo_docker_tag> -t <cluster_registry_url>/stand/db/mongo .
```

Where:
* `mongo_docker_tag` - tag of MongoDB base docker image
* `cluster_registry_url` - cluster Docker registry URL

Current cluster Docker registry URL is:
`kubeadm.ipavlov.mipt.ru:5000`

MongoDB Docker versions (tags) in current use:
* `4.0.6-xenial`

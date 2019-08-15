# DeepPavlov base Docker images
DeepPavlov base GPU and no-GPU docker files.

## No-GPU
Build instructions:

```
docker build -t deeppavlov/base:<dp_version> \
    --build-arg PYTHON_BASE_IMAGE=<python_base_docker_image> \
    --build-arg COMMIT=<dp_version> .
```

For now we are using:

| COMMIT | PYTHON_BASE_IMAGE       | latest |
| ------ | ----------------------- | ------ |
| 0.5.1  | python:3.7-slim-stretch | V      |
| 0.3.0  | python:3.6-slim-stretch |        |

Run instructions:

This runs container with DeepPavlov served in `riseapi` mode.

```
docker run -e CONFIG=<dp_config_name> -p <your_port>:5000 \
    -e COMMIT=<git_commit_id> \
    -v <dp_logs_volume>:/logs \
    -v <dp_components_volume>:/root/.deeppavlov \
    deeppavlov/base:<dp_version>
```

# DeepPavlov base Docker images
DeepPavlov base GPU and no-GPU docker files.

## No-GPU
Build instructions:

```shell script
cd stand_kubernetes_cluster/utils/dp_base/base_no_gpu
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

This runs container with DeepPavlov served in `riseapi` mode on cpu.

```shell script
docker run -e CONFIG=<dp_config_name> -p <your_port>:5000 \
    -e COMMIT=<git_commit_id> \
    -v <dp_logs_volume>:/logs \
    -v <dp_components_volume>:/root/.deeppavlov \
    deeppavlov/base:<dp_version>
```

## GPU
Build instructions:

```shell script
cd stand_kubernetes_cluster/utils/dp_base/base_gpu
docker build -t deeppavlov/base-gpu:<dp_version> \
    --build-arg NVIDIA_BASE_IMAGE=<python_base_docker_image> \
    --build-arg COMMIT=<dp_version>
    --build-arg CUDNN_VERSION=<cudnn_version>
    --build-arg PYTHON_VERSION=<python_version> .
```

For now we are using:

| COMMIT | NVIDIA_BASE_IMAGE                  | CUDNN_VERSION | PYTHON_VERSION | latest |
| ------ | ---------------------------------- | ------------- | -------------- | ------ |
| 0.5.1  | nvidia/cuda:10.0-devel-ubuntu16.04 | 7.6.2.24      | 3.7.4          | V      |
| 0.3.0  | nvidia/cuda:9.0-devel-ubuntu16.04  | 7.1.4.18      | 3.6.9          |        |

Run instructions:

This runs container with DeepPavlov served in `riseapi` mode on GPU.

```shell script
docker run -e CONFIG=<dp_config_name> -p <your_port>:5000 \
    --runtime=nvidia \
    -e COMMIT=<git_commit_id> \
    -v <dp_logs_volume>:/logs \
    -v <dp_components_volume>:/root/.deeppavlov \
    deeppavlov/base-gpu:<dp_version>
```

## DeepPavlov model
Build instructions:

```shell script
cd stand_kubernetes_cluster/utils/dp_base/dp_model
docker build -t deeppavlov/<dp_model_name>:<gpu|cpu> \
    --build-arg BASE_IMAGE=<dp_base_image> \
    --build-arg COMMIT=<dp_version> \
    --build-arg CONFIG=<dp_config_name>
```

Build arguments examples for some models:

| COMMIT | BASE_IMAGE                | CONFIG                          |
| ------ | ------------------------- | ------------------------------- |
| 0.5.1  | deeppavlov/base:0.5.1     | ner_ru                          |
| 0.5.1  | deeppavlov/base-gpu:0.5.1 | ru_odqa_infer_wiki_rubert_noans |

Run instructions on CPU:

```shell script
docker run -e CONFIG=<dp_config_name> -p <your_port>:5000 \
    -v <dp_logs_volume>:/logs \
    -v <dp_components_volume>:/root/.deeppavlov \
    deeppavlov/ner_ru:cpu
```

Run instructions on GPU:

```shell script
docker run -e CONFIG=<dp_config_name> -p <your_port>:5000 \
    --runtime=nvidia \
    -v <dp_logs_volume>:/logs \
    -v <dp_components_volume>:/root/.deeppavlov \
    deeppavlov/ner_ru:gpu

```

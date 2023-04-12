# DeepPavlov Docker images

## Base images

Base images allow to run any DeepPavlov config from specific DP version.

### CPU

#### Build instructions:

`cd` `cpu` dir, then: 


```shell script
docker build -t deeppavlov/base-cpu:<dp_version> \
    --build-arg PYTHON_BASE_IMAGE=<python_base_docker_image> \
    --build-arg COMMIT=<dp_version> .
```

#### Run instructions:

```shell script
docker run -e CONFIG=<dp_config_name> -p <your_port>:5000 \
    -e COMMIT=<git_commit_id> \
    -v <dp_components_volume>:/root/.deeppavlov \
    -v <host_venv_dir>:/venv \
    deeppavlov/base-cpu:<dp_version>
```

### GPU

#### Build instructions:

`cd` `gpu` dir, then:


```shell script
docker build -t deeppavlov/base-gpu:<dp_version> \
    --build-arg NVIDIA_BASE_IMAGE=<python_base_docker_image> \
    --build-arg COMMIT=<dp_version> \
    --build-arg CUDNN_VERSION=<cudnn_version> \
    --build-arg PYTHON_VERSION=<python_version> .
```

#### Run instructions:

```shell script
docker run -e CONFIG=<dp_config_name> -p <your_port>:5000 \
    --runtime=nvidia \
    -e COMMIT=<git_commit_id> \
    -v <dp_components_volume>:/root/.deeppavlov \
    -v <host_venv_dir>:/venv \
    deeppavlov/base-gpu:<dp_version>
```

## Model images

Model images allow to run specific DeepPavlov config from specific DP version.

### Build instructions:

`cd` `model` dir, then:


```shell script
docker build -t deeppavlov/<dp_config_name>[_cpu | _gpu]:<dp_version> \
    --build-arg BASE_IMAGE=<dp_base_image> \
    --build-arg COMMIT=<dp_version> \
    --build-arg CONFIG=<dp_config_name> .
```

#### CPU run instructions:

```shell script
docker run -p <your_port>:5000 \
    -v <dp_components_volume>:/root/.deeppavlov \
    deeppavlov/<dp_config_name>_cpu:<dp_version>
```

#### GPU run instructions:

```shell script
docker run -p <your_port>:5000 \
    --runtime=nvidia \
    -v <dp_components_volume>:/root/.deeppavlov \
    deeppavlov/<dp_config_name>_gpu:<dp_version>
```

## For now we are using:

### CPU

| COMMIT | PYTHON_BASE_IMAGE       | latest |
| ------ | ----------------------- | ------ |
| 0.14.1 | python:3.7-slim-stretch | V      |
| 0.7.1  | python:3.7-slim-stretch |        |
| 0.6.1  | python:3.7-slim-stretch |        |
| 0.5.1  | python:3.7-slim-stretch |        |
| 0.3.0  | python:3.6-slim-stretch |        |

### GPU

| COMMIT | NVIDIA_BASE_IMAGE                  | CUDNN_VERSION | PYTHON_VERSION | latest |
| ------ | ---------------------------------- | ------------- | -------------- | ------ |
| 0.7.1  | nvidia/cuda:10.0-devel-ubuntu16.04 | 7.6.2.24      | 3.7.4          | V      |
| 0.6.1  | nvidia/cuda:10.0-devel-ubuntu16.04 | 7.6.2.24      | 3.7.4          |        |
| 0.5.1  | nvidia/cuda:10.0-devel-ubuntu16.04 | 7.6.2.24      | 3.7.4          |        |
| 0.3.0  | nvidia/cuda:9.0-devel-ubuntu16.04  | 7.1.4.18      | 3.6.9          |        |

### NGC

docker build -t ngc-deeppavlov --build-arg COMMIT=0.14.1 \
    --build-arg NGC_BASE_IMAGE=nvcr.io/nvidia/tensorflow:20.11-tf1-py3 .

| COMMIT | NGC_BASE_IMAGE                          |
| ------ | --------------------------------------- |
| 0.14.1 | nvcr.io/nvidia/tensorflow:20.11-tf1-py3 |

## 1.0.0+

### Build and push

```commandline
export DP_VERSION=1.1.1
docker compose -f build.yml build cpu gpu
docker compose -f build.yml build cpu-jupyter gpu-jupyter
# for-loop below is needed to make proper order in deeppavlov dockerhub repo
for service in gpu-jupyter cpu-jupyter gpu cpu; do docker compose -f build.yml push $service; done
```

### Test

```commandline
export DP_VERSION=1.1.0
docker-compose -f test.yml build
docker-compose -f test.yml up
```

### GPU

| DP_VERSION | BASE_IMAGE                                     |
|------------|------------------------------------------------|
| 1.0.0+     | pytorch/pytorch:1.12.1-cuda11.3-cudnn8-runtime |

### CPU

| DP_VERSION | BASE_IMAGE    |
|------------|---------------|
| 1.0.0+     | python:3.7.13 |

TODO:
add tests. In particular, check that LANG == C.UTF-8 for python cpu image

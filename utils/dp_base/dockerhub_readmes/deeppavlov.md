## DeepPavlov Docker Images

### What is DeepPavlov?

DeepPavlov is an open-source conversational AI library built on PyTorch. DeepPavlov is designed for
- development of production ready chat-bots and complex conversational systems,
- research in the area of NLP and, particularly, of dialog systems.

### Images

This repository contains images for DeepPavlov 1.0.0 and later. For earlier releases, look at
[base-cpu](https://hub.docker.com/r/deeppavlov/base-cpu) and [base-gpu](https://hub.docker.com/r/deeppavlov/base-gpu) repos.

Images with tags `*.*.*`, `latest`, `*.*.*-gpu` and `latest-gpu` allow you to run DeepPavlov models and communicate
them via REST-like HTTP API (see [riseapi](http://docs.deeppavlov.ai/en/master/integrations/rest_api.html) DeepPavlov docs for more details).

Images with tags `*.*.*-jupyter`, `latest-jupyter`, `*.*.*-gpu-jupyter` and `latest-gpu-jupyter` allow you to run Jupyter notebook server. 

Images with tags containing `gpu` from this repository are built to be run on GPU
and require to have [NVIDIA Container Toolkit](https://github.com/NVIDIA/nvidia-docker) installed.

### Instructions

#### REST-like HTTP API

Run following to start server for particular DeepPavlov model in [riseapi](http://docs.deeppavlov.ai/en/master/integrations/rest_api.html) mode:
```
docker run -e CONFIG=<dp_config_name> -p <host_port>:5000 \
    --runtime=nvidia \
    -v <dp_components_volume>:/root/.deeppavlov \
    -v <cache_volume>:/root/.cache \
    deeppavlov/deeppavlov:<image_tag>
```

Where:

1. `<dp_config_name>` (mandatory) - is config file name (**without extension**) for model you want to serve. You can get DeepPavlov
`latest` models list with description in [DP features docs](http://docs.deeppavlov.ai/en/master/features/overview.html)
or browse DP gitHub [here](https://github.com/deepmipt/DeepPavlov/tree/master/deeppavlov/configs).

2. `<host_port>` (mandatory) - port on which you want to serve DeepPavlov model.

3. `--runtime=nvidia` (optional) - enables GPU usage for images with `*.*.*-gpu` and `latest-gpu` tags
if [NVIDIA Container Toolkit](https://github.com/NVIDIA/nvidia-docker) is installed.

4. `<dp_components_volume>` (optional) - directory on your host where you can mount DeepPavlov downloaded components dir.
Most of DeepPavlov models use downloadable components (pretrained model pickles, embeddings...) which are downloaded from our
servers. To prevent downloading components (some of them are quite heavy) each time you run Docker image for specific DeepPavlov
config, you can make this mount. If you do it, DeepPavlov will store in this dir components downloaded during the first 
launch of any DeepPavlov config, so during the further launches DP will use components from the mounted folder. We recommend to
use one `<dp_components_volume>` for all models because some of them can use same components. DeepPavlov will automatically
manage downloaded components for all configs in this folder. To skip components download add `SKIP_DOWNLOAD` environment
variable to container with non-empty value (for example, `-e SKIP_DOWNLOAD=true`).

5. `<cache_volume>` (optional) - directory on your host where you can mount container cache dir. Many DeepPavlov models use
Hugging Face Transformers-based components. Components cache is downloaded to `/root/.cache`. 

6. `<image_tag>` - `*.*.*`, `latest`, `*.*.*-gpu` or `latest-gpu` tag.

After model initiate, follow url `http://localhost:<host_port>` in your browser to get Swagger for model API and endpoint reference.

#### Jupyter Notebook

Run following to start Jupyter Notebook server:
```
docker run -p <host_port>:5000 \
    --runtime=nvidia \
    -v <dp_components_volume>:/root/.deeppavlov \
    -v <src_dir>:/app \
    -v <cache_volume>:/root/.cache \
    deeppavlov/deeppavlov:<image_tag>
```

Where:

1. `<host_port>`, `<dp_components_volume>` and `<cache_volume>` - see corresponding description in `REST-like HTTP API` section.
2. `--runtime=nvidia` (optional) - enables GPU usage for images with `*.*.*-gpu-jupyter` and `latest-gpu-jupyter` tags
if [NVIDIA Container Toolkit](https://github.com/NVIDIA/nvidia-docker) is installed.
3. `<src_dir>` (optional) - directory to store Jupyter notebooks. `/app` directory is the workdir in the container.
4. `<image_tag>` - `*.*.*-jupyter`, `latest-jupyter`, `*.*.*-gpu-jupyter` or `latest-gpu-jupyter` tag.

After Jupyter start, navigate to `localhost:<host_port>` in your browser.

### Example:

#### REST-like HTTP API

Run GPU container with [NER Ontonotes](http://docs.deeppavlov.ai/en/master/features/overview.html#ner-model-docs) model: 

```commandline
docker run -e CONFIG=ner_ontonotes_bert -p 5000:5000 \
    --runtime=nvidia \
    -v ~/.deeppavlov:/root/.deeppavlov \
    -v ~/.cache:/root/.cache \
    deeppavlov/deeppavlov:latest-gpu
```

Follow `http://0.0.0.0:5000` URL in your browser to get Swagger with model API info.

#### Jupyter Notebook

Start CPU container with Jupyter Notebook:

```commandline
docker run -p 5000:5000 \
    -v ~/.deeppavlov:/root/.deeppavlov \
    -v ~/.cache:/root/.cache \
    -v /tmp:/app \
    deeppavlov/deeppavlov:latest-jupyter
```

Follow `http://0.0.0.0:5000` URL in your browser.

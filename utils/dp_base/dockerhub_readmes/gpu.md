Pre-built DeepPavlov models served via HTTP (using GPU).



This repository contains pre-built DeepPavlov images for different library releases (`latest` tag equals to the latest
release in this repo). These images allow you to run DeepPavlov models and communicate them via REST-like HTTP API
(see [riseapi](http://docs.deeppavlov.ai/en/master/integrations/rest_api.html) DeepPavlov docs for more details).

Images from these repository are built to be run on GPU and require to have [NVIDIA Container Toolkit](https://github.com/NVIDIA/nvidia-docker) installed.
To use CPU please explore [base-cpu](https://hub.docker.com/r/deeppavlov/base-cpu) repo.

### Instructions

Run following to rise server for particular DeepPavlov model in GPU mode:
```
docker run -e CONFIG=<dp_config_name> -p <your_port>:5000 \
    --runtime=nvidia \
    -v <dp_logs_volume>:/logs \
    -v <dp_components_volume>:/root/.deeppavlov \
    -v <host_venv_dir>:/venv \
    deeppavlov/base-gpu:<dp_version>
```

Where:

1. `<dp_config_name>` (mandatory) - is config file name (**without extension**) for model you want to serve. You can get DeepPavlov
`latest` models list with description in [DP features docs](http://docs.deeppavlov.ai/en/master/features/overview.html)
or browse DP gitHub [here](https://github.com/deepmipt/DeepPavlov/tree/master/deeppavlov/configs).

2. `<your_port>` (mandatory) - port on which you want to serve DP model.

3. `<dp_logs_volume>` - directory on your host, where you can mount DeepPavlov models log dirs. If you provide this mount,
DeepPavlov create `<dp_config_name>.log` file in `<dp_logs_volume>` dir on your host, with `<dp_config_name>` logs.

4. `<dp_components_volume>` - directory on your host where you can mount DeepPavlov downloaded components dir.
Most of DeepPavlov models use downloadable components (pretrained model pickles, embeddings...) which are downloaded from our
servers. To prevent downloading components (some of them are quite heavy) each time you run Docker image for specific DP
config, you can make this mount. If you do it, DeepPavlov will store in this dir components downloaded during the first 
launch of any DP config, so during the further launches DP will use components from the mounted folder. DeepPavlov will
automatically manage downloaded components for all configs in this folder.

5. `<host_venv_dir>` - directory on your host where you can mount DeepPavlov Python virtual environments dir. Each DP
config uses its own set of Python dependencies, which are installed each time you run Docker image for specific DP
config. To prevent it you can make this mount. In this case DeepPavlov create `<dp_config_name>` dir in `<dp_logs_volume>` dir on 
your host with virtual environment for subsequent reuse with this config.

6. `<dp_version>` - DeepPavlov release ID. Omit to use run latest DP release.

After model initiate, follow url `http://127.0.0.1:<your_port>` in your browser to get Swagger for model API and endpoint reference.

### Example:
1. This will run Docker container with [NER Ontonotes](http://docs.deeppavlov.ai/en/master/features/overview.html#ner-model-docs)
on your host in GPU mode: 

```
docker run -e CONFIG=ner_ontonotes -p 5555:5000 \
    --runtime=nvidia \
    -v ~/my_dp_logs:/logs \
    -v ~/my_dp_components:/root/.deeppavlov \
    -v ~/my_dp_envs:/venv \
    deeppavlov/base-gpu
```

2. Follow `http://127.0.0.1:5555/` URL in your browser to get Swagger with model API info;

3. You can get model logs in `~/my_dp_logs/ner_ontonotes.log` file, model env located in `~/my_dp_envs/ner_ontonotes`,
downloadable components in `~/my_dp_components` (contents of this dir is managed by DeepPavlov).
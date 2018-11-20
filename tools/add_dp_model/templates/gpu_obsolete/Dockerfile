FROM stand/docker_deeppavlov:cuda-{{CUDA_VERSION}}

VOLUME /logs
WORKDIR /app
ADD . /app

RUN cd /base/DeepPavlov && \
    git checkout {{BRANCH}} && \
    git fetch && \
    git pull origin {{BRANCH}} && \
    python3.6 setup.py develop && \
    pip uninstall tensorflow-gpu && \
    pip install tensorflow=={{TF_VERSION}} && \
    pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-2.0.0/en_core_web_sm-2.0.0.tar.gz#en_core_web_sm

RUN python3.6 -m deeppavlov.deep download /base/DeepPavlov/deeppavlov/configs/{{CONFIG_FILE}} && \
    cp /app/configs/server_config.json /base/DeepPavlov/utils/server_utils/server_config.json

RUN cd /base/DeepPavlov && \
    pip install tensorflow-gpu=={{TF_VERSION}}

EXPOSE {{PORT}}

ENV MODEL_NAME={{FULL_MODEL_NAME}}
ENV DEFAULT_POD_NODE="unknown_node"
ENV DEFAULT_POD_NAME="unknown_pod"

CMD if [ -z $POD_NODE ] || [ $POD_NODE = "" ]; then POD_NODE=$DEFAULT_POD_NODE; fi && \
    if [ -z $POD_NAME ] || [ $POD_NAME = "" ]; then POD_NAME=$DEFAULT_POD_NAME; fi && \
    DATE_TIME=$(date '+%Y-%m-%d_%H-%M-%S.%N') && \
    LOG_DIR="/logs/"$MODEL_NAME"/"$POD_NODE"/" && \
    LOG_FILE=$MODEL_NAME"_"$DATE_TIME"_"$POD_NAME".log" && \
    LOG_PATH=$LOG_DIR$LOG_FILE && \
    mkdir -p $LOG_DIR && \
    python3.6 -m deeppavlov.deep riseapi /base/DeepPavlov/deeppavlov/configs/{{CONFIG_FILE}} > $LOG_PATH 2>&1
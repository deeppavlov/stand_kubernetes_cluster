FROM stand/docker_deeppavlov:cuda-8.0

VOLUME /logs
WORKDIR /app
ADD . /app

RUN cd /base/DeepPavlov && \
    git checkout squad_confidence && \
    git fetch && \
    git pull origin squad_confidence && \
    python3.6 setup.py develop && \
    pip uninstall tensorflow-gpu && \
    pip install tensorflow==1.4.0

RUN python3.6 -m deeppavlov.deep download /base/DeepPavlov/deeppavlov/configs/squad/squad_ru.json && \
    cp /app/configs/server_config.json /base/DeepPavlov/utils/server_utils/server_config.json

RUN cd /base/DeepPavlov && \
    pip install tensorflow-gpu==1.4.0

EXPOSE 6019

ENV MODEL_NAME=demo_squad_ru_confidence
ENV DEFAULT_POD_NODE="unknown_node"
ENV DEFAULT_POD_NAME="unknown_pod"

CMD if [ -z $POD_NODE ] || [ $POD_NODE = "" ]; then POD_NODE=$DEFAULT_POD_NODE; fi && \
    if [ -z $POD_NAME ] || [ $POD_NAME = "" ]; then POD_NAME=$DEFAULT_POD_NAME; fi && \
    DATE_TIME=$(date '+%Y-%m-%d_%H-%M-%S.%N') && \
    LOG_DIR="/logs/"$MODEL_NAME"/"$POD_NODE"/" && \
    LOG_FILE=$MODEL_NAME"_"$DATE_TIME"_"$POD_NAME".log" && \
    LOG_PATH=$LOG_DIR$LOG_FILE && \
    mkdir -p $LOG_DIR && \
    python3.6 -m deeppavlov.deep riseapi /base/DeepPavlov/deeppavlov/configs/squad/squad_ru.json > $LOG_PATH 2>&1
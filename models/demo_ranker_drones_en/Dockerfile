FROM stand/docker_deeppavlov:cuda-9.0

VOLUME /logs
WORKDIR /app
ADD . /app

ENV TFHUB_CACHE_DIR='/base/DeepPavlov/download/tfhub/'

RUN cd /base/DeepPavlov && \
    git checkout odqa_pmef_tf_1.7 && \
    git fetch && \
    git pull origin odqa_pmef_tf_1.7 && \
    python3.6 setup.py develop && \
    pip uninstall -y tensorflow-gpu && \
    pip install tensorflow==1.7.0 && \
    printf "import tensorflow_hub\ne = tensorflow_hub.Module('https://tfhub.dev/google/universal-sentence-encoder/1')" | python3.6

RUN python3.6 -m deeppavlov.deep download /base/DeepPavlov/deeppavlov/configs/odqa/en_ranker_drones.json && \
    cp /app/configs/server_config.json /base/DeepPavlov/utils/server_utils/server_config.json

RUN cd /base/DeepPavlov && \
    pip install tensorflow-gpu==1.7.0

EXPOSE 6020

ENV MODEL_NAME=demo_ranker_drones_en
ENV DEFAULT_POD_NODE="unknown_node"
ENV DEFAULT_POD_NAME="unknown_pod"

CMD if [ -z $POD_NODE ] || [ $POD_NODE = "" ]; then POD_NODE=$DEFAULT_POD_NODE; fi && \
    if [ -z $POD_NAME ] || [ $POD_NAME = "" ]; then POD_NAME=$DEFAULT_POD_NAME; fi && \
    DATE_TIME=$(date '+%Y-%m-%d_%H-%M-%S.%N') && \
    LOG_DIR="/logs/"$MODEL_NAME"/"$POD_NODE"/" && \
    LOG_FILE=$MODEL_NAME"_"$DATE_TIME"_"$POD_NAME".log" && \
    LOG_PATH=$LOG_DIR$LOG_FILE && \
    mkdir -p $LOG_DIR && \
    python3.6 -m deeppavlov.deep riseapi /base/DeepPavlov/deeppavlov/configs/odqa/en_ranker_drones.json > $LOG_PATH 2>&1
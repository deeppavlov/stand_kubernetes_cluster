ARG BASE_IMAGE
FROM $BASE_IMAGE

ARG COMMIT
ARG CONFIG
ARG FULL_MODEL_NAME

ENV COMMIT=$COMMIT
ENV CONFIG=$CONFIG
ENV TFHUB_CACHE_DIR=/tmp/tfhub

ENV DEFAULT_POD_NODE="unknown_node"
ENV DEFAULT_POD_NAME="unknown_pod"
ENV MODEL_NAME=$FULL_MODEL_NAME

VOLUME /tmp/tfhub

WORKDIR /agent

RUN git clone https://github.com/deepmipt/dp-agent.git && \
    cd dp-agent && \
    if [ "$COMMIT" != "" ]; then \
        git checkout $COMMIT; \
    fi && \
    python -m deeppavlov install $CONFIG && \
    sed -i "/uvicorn.run/s/app,/app, timeout_keep_alive=20,/g" "/base/DeepPavlov/deeppavlov/utils/server/server.py"

CMD if [ -z $POD_NODE ] || [ $POD_NODE = "" ]; then POD_NODE=$DEFAULT_POD_NODE; fi && \
    if [ -z $POD_NAME ] || [ $POD_NAME = "" ]; then POD_NAME=$DEFAULT_POD_NAME; fi && \
    DATE_TIME=$(date '+%Y-%m-%d_%H-%M-%S.%N') && \
    LOG_DIR="/logs/"$MODEL_NAME"/" && \
    LOG_FILE=$MODEL_NAME"_"$DATE_TIME"_"$POD_NODE"_"$POD_NAME".log" && \
    LOG_PATH=$LOG_DIR$LOG_FILE && \
    mkdir -p $LOG_DIR && \
    cd /agent/dp-agent && \
    python -m deeppavlov riseapi $CONFIG -p 5000 -d > $LOG_PATH 2>&1
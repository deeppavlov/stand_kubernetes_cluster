ARG BASE_IMAGE
FROM $BASE_IMAGE

ARG DPA_COMMIT
ARG DP_COMMIT
ARG CONFIG
ARG FULL_MODEL_NAME

ENV CONFIG=$CONFIG
ENV TFHUB_CACHE_DIR=/tmp/tfhub

ENV DEFAULT_POD_NODE="unknown_node"
ENV DEFAULT_POD_NAME="unknown_pod"
ENV MODEL_NAME=$FULL_MODEL_NAME

VOLUME /tmp/tfhub

WORKDIR /agent

RUN if [ "$DP_COMMIT" != "" ]; then \
        cd /base/DeepPavlov && \
        git fetch --all --tags --prune && \
        git checkout $DP_COMMIT && \
        python setup.py develop; \
    fi && \
    cd /agent && \
    git clone https://github.com/deepmipt/dp-agent.git && \
    cd dp-agent && \
    if [ "$DPA_COMMIT" != "" ]; then \
        git checkout $DPA_COMMIT; \
    fi && \
    python -m deeppavlov install $CONFIG

CMD if [ -z $POD_NODE ] || [ $POD_NODE = "" ]; then POD_NODE=$DEFAULT_POD_NODE; fi && \
    if [ -z $POD_NAME ] || [ $POD_NAME = "" ]; then POD_NAME=$DEFAULT_POD_NAME; fi && \
    DATE_TIME=$(date '+%Y-%m-%d_%H-%M-%S.%N') && \
    LOG_DIR="/logs/"$MODEL_NAME"/" && \
    LOG_FILE=$MODEL_NAME"_"$DATE_TIME"_"$POD_NODE"_"$POD_NAME".log" && \
    LOG_PATH=$LOG_DIR$LOG_FILE && \
    mkdir -p $LOG_DIR && \
    cd /agent/dp-agent && \
    python -m deeppavlov riseapi $CONFIG -p 5000 -d > $LOG_PATH 2>&1
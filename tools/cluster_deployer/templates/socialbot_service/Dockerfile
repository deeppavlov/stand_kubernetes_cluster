ARG BASE_IMAGE
FROM $BASE_IMAGE

ARG FULL_MODEL_NAME
ARG CMD_SCRIPT

ENV DEFAULT_POD_NODE="unknown_node"
ENV DEFAULT_POD_NAME="unknown_pod"
ENV MODEL_NAME=$FULL_MODEL_NAME
ENV CMD_SCRIPT=$CMD_SCRIPT


CMD if [ -z $POD_NODE ] || [ $POD_NODE = "" ]; then POD_NODE=$DEFAULT_POD_NODE; fi && \
    if [ -z $POD_NAME ] || [ $POD_NAME = "" ]; then POD_NAME=$DEFAULT_POD_NAME; fi && \
    DATE_TIME=$(date '+%Y-%m-%d_%H-%M-%S.%N') && \
    LOG_DIR="/logs/"$MODEL_NAME"/" && \
    LOG_FILE=$MODEL_NAME"_"$DATE_TIME"_"$POD_NODE"_"$POD_NAME".log" && \
    LOG_PATH=$LOG_DIR$LOG_FILE && \
    mkdir -p $LOG_DIR && \
    sh $CMD_SCRIPT > $LOG_PATH 2>&1
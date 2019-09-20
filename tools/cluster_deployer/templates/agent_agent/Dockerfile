FROM deeppavlov/agent:transport

COPY ./config.yaml /dp-agent/core/config.yaml
COPY ./log_config.yaml /dp-agent/core/log_config.yaml

ENV DEFAULT_POD_NODE="unknown_node"
ENV DEFAULT_POD_NAME="unknown_pod"

CMD ARG_SERVICE="" ; if [ ! -z $SERVICE_NAME ]; then ARG_SERVICE="-n "$SERVICE_NAME; fi && \
    ARG_INSTANCE="" ; if [ ! -z $INSTANCE_ID ]; then ARG_INSTANCE="-i "$INSTANCE_ID; fi && \
    if [ -z $POD_NODE ] || [ $POD_NODE = "" ]; then POD_NODE=$DEFAULT_POD_NODE; fi && \
    if [ -z $POD_NAME ] || [ $POD_NAME = "" ]; then POD_NAME=$DEFAULT_POD_NAME; fi && \
    DATE_TIME=$(date '+%Y-%m-%d_%H-%M-%S.%N') && \
    LOG_DIR="/logs/"$MODEL_NAME"/" && \
    LOG_FILE=$MODEL_NAME"_"$DATE_TIME"_"$POD_NODE"_"$POD_NAME".log" && \
    LOG_PATH=$LOG_DIR$LOG_FILE && \
    mkdir -p $LOG_DIR && \
    python3 /dp-agent/core/run.py $MODE $ARG_SERVICE $ARG_INSTANCE > $LOG_PATH 2>&1
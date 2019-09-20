FROM deeppavlov/agent:skill-legacy

ENV DEFAULT_POD_NODE="unknown_node"
ENV DEFAULT_POD_NAME="unknown_pod"

CMD if [ -z $POD_NODE ] || [ $POD_NODE = "" ]; then POD_NODE=$DEFAULT_POD_NODE; fi && \
    if [ -z $POD_NAME ] || [ $POD_NAME = "" ]; then POD_NAME=$DEFAULT_POD_NAME; fi && \
    DATE_TIME=$(date '+%Y-%m-%d_%H-%M-%S.%N') && \
    LOG_DIR="/logs/"$MODEL_NAME"/" && \
    LOG_FILE=$MODEL_NAME"_"$DATE_TIME"_"$POD_NODE"_"$POD_NAME".log" && \
    LOG_PATH=$LOG_DIR$LOG_FILE && \
    mkdir -p $LOG_DIR && \
    python3.6 -m legacy_components.core.run_dp_servers $CONFIG -p 5000 -host 0.0.0.0 -ep answer > $LOG_PATH 2>&1
FROM stand/docker_deeppavlov:cuda-9.0

VOLUME /logs
WORKDIR /app

RUN git clone https://github.com/deepmipt/sbrf_bot.git && \
    python3.6 -m deeppavlov download /app/sbrf_bot/skill.faq.json

EXPOSE 6040

ENV MODEL_NAME="demo_sber_faq"
ENV DEFAULT_POD_NODE="unknown_node"
ENV DEFAULT_POD_NAME="unknown_pod"

CMD if [ -z $POD_NODE ] || [ $POD_NODE = "" ]; then POD_NODE=$DEFAULT_POD_NODE; fi && \
    if [ -z $POD_NAME ] || [ $POD_NAME = "" ]; then POD_NAME=$DEFAULT_POD_NAME; fi && \
    DATE_TIME=$(date '+%Y-%m-%d_%H-%M-%S.%N') && \
    LOG_DIR="/logs/"$MODEL_NAME"/"$POD_NODE"/" && \
    LOG_FILE=$MODEL_NAME"_"$DATE_TIME"_"$POD_NAME".log" && \
    LOG_PATH=$LOG_DIR$LOG_FILE && \
    mkdir -p $LOG_DIR && \
    cd /app/sbrf_bot && \
    python3.6 server.py > $LOG_PATH 2>&1
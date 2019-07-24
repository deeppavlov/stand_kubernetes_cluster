FROM python:3.6.9-slim-stretch

VOLUME /logs
WORKDIR /app

ENV PYTHONPATH="${PYTHONPATH}:/app"

RUN apt-get update && \
    apt-get install -y git locales && \
    printf '%s\n%s\n' 'en_US.UTF-8 UTF-8' 'ru_RU.UTF-8 UTF-8' >> /etc/locale.gen && \
    locale-gen && \
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false && \
	rm -rf /var/lib/apt/lists/*

ENV LANG='en_US.UTF-8' LANGUAGE='en_US.UTF-8' LC_ALL='en_US.UTF-8'

RUN git clone https://github.com/deepmipt/convai_router_bot_poller.git . && \
    git checkout stand && \
    pip install -r requirements.txt && \
    rm -rf /root/.cache

ENV MODEL_NAME={{FULL_MODEL_NAME}}
ENV DEFAULT_POD_NODE="unknown_node"
ENV DEFAULT_POD_NAME="unknown_pod"

CMD if [ -z $POD_NODE ] || [ $POD_NODE = "" ]; then POD_NODE=$DEFAULT_POD_NODE; fi && \
    if [ -z $POD_NAME ] || [ $POD_NAME = "" ]; then POD_NAME=$DEFAULT_POD_NAME; fi && \
    DATE_TIME=$(date '+%Y-%m-%d_%H-%M-%S.%N') && \
    LOG_DIR="/logs/"$MODEL_NAME"/" && \
    LOG_FILE=$MODEL_NAME"_"$DATE_TIME"_"$POD_NODE"_"$POD_NAME".log" && \
    LOG_PATH=$LOG_DIR$LOG_FILE && \
    mkdir -p $LOG_DIR && \
    python poller.py {{MODEL_URL}} --host {{ROUTER_BOT_IP}} --port {{ROUTER_BOT_PORT}} --token {{BOT_TOKEN}} > $LOG_PATH 2>&1
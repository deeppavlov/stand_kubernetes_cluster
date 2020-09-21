FROM python:3.7-slim-stretch

ARG COMMIT
ARG FULL_MODEL_NAME

ENV COMMIT=$COMMIT
ENV LANG="C.UTF-8"
ENV LC_ALL="C.UTF-8"
ENV DEBIAN_FRONTEND="noninteractive"
ENV DPA_LAUNCHING_ENV="local"

RUN apt-get update -y --fix-missing && \
    apt-get install -y -q build-essential openssl git libssl-dev libffi-dev && \
    echo "stty iutf8" >> ~/.bashrc

WORKDIR /agent

RUN git clone https://github.com/deepmipt/dp-agent.git && \
    cd dp-agent && \
    if [ "$COMMIT" != "" ]; then \
        git checkout $COMMIT; \
    fi && \
    pip install -r requirements.txt && \
    python setup.py develop

ENV DEFAULT_POD_NODE="unknown_node"
ENV DEFAULT_POD_NAME="unknown_pod"
ENV MODEL_NAME=$FULL_MODEL_NAME

EXPOSE 5000

CMD if [ -z $POD_NODE ] || [ $POD_NODE = "" ]; then POD_NODE=$DEFAULT_POD_NODE; fi && \
    if [ -z $POD_NAME ] || [ $POD_NAME = "" ]; then POD_NAME=$DEFAULT_POD_NAME; fi && \
    DATE_TIME=$(date '+%Y-%m-%d_%H-%M-%S.%N') && \
    LOG_DIR="/logs/"$MODEL_NAME"/" && \
    LOG_FILE=$MODEL_NAME"_"$DATE_TIME"_"$POD_NODE"_"$POD_NAME".log" && \
    LOG_PATH=$LOG_DIR$LOG_FILE && \
    mkdir -p $LOG_DIR && \
    cd /agent/dp-agent && \
    mkdir -p http_api/static && \
    python -u run.py -ch http_client -p 5000 -d > $LOG_PATH 2>&1
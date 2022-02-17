#!/bin/sh
if [ -z $(ps aux | grep application.py | grep -v grep | awk '{print $2}') ]; then
    MODEL_NAME='{{MODEL_NAME}}'
    POD_NODE='{{POD_NODE}}'
    POD_NAME='{{POD_NAME}}'

    ROUTER_BOT_UPPER_DIR="/app/router_bot_volume/"${MODEL_NAME}
    ROUTER_BOT_DIR=$ROUTER_BOT_UPPER_DIR"/convai_router_bot"

    if [ ! -d ${ROUTER_BOT_DIR} ]; then \
        mkdir -p ${ROUTER_BOT_UPPER_DIR} && \
        cp -r /app/convai_router_bot ${ROUTER_BOT_DIR}; \
    fi && \

    if [ ! -d /root/convai_router_bot ]; then \
        ln -s ${ROUTER_BOT_DIR} /root/convai_router_bot ; \
    fi && \

    if [ ! -d /root/router_bot_settings ]; then \
        ln -s ${ROUTER_BOT_DIR}"/settings" /root/router_bot_settings ; \
    fi && \

    DATE_TIME=$(date '+%Y-%m-%d_%H-%M-%S.%N')
    LOG_DIR="/logs/"${MODEL_NAME}"/" && \
    LOG_FILE=${MODEL_NAME}"_"${DATE_TIME}"_"${POD_NODE}"_"${POD_NAME}".log" && \
    LOG_PATH=${LOG_DIR}${LOG_FILE}

    mkdir -p ${LOG_DIR}
    nohup python3.6 ${ROUTER_BOT_DIR}"/application.py" --port=80 > ${LOG_PATH} 2>&1 &
    echo 'Router bot started'
else
    echo 'Router bot is already running'
fi
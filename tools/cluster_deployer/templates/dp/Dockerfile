# Copyright 2017 Neural Networks and Deep Learning lab, MIPT
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

ARG BASE_IMAGE
FROM $BASE_IMAGE

ENV DEFAULT_POD_NODE="unknown_node"
ENV DEFAULT_POD_NAME="unknown_pod"

VOLUME /app

CMD if [ -d /app/$FULL_MODEL_NAME/venv ]; then \
        PATH=/app/$FULL_MODEL_NAME/venv/bin:$PATH; \
    else \
        if [ ! -z $COMMIT ]; then \
            cd /base/DeepPavlov && \
            git fetch --all --tags --prune && \
            git checkout $COMMIT;\
        fi && \
        cp /app/$FULL_MODEL_NAME/settings/* /base/DeepPavlov/deeppavlov/utils/settings/ && \
        pip install /base/DeepPavlov && \
        python -m deeppavlov install $CONFIG && \
        mkdir /app/$FULL_MODEL_NAME/venv && \
        cp -r /base/venv/ /app/$FULL_MODEL_NAME/; \
    fi && \
    if [ -z $POD_NODE ] || [ $POD_NODE = "" ]; then POD_NODE=$DEFAULT_POD_NODE; fi && \
    if [ -z $POD_NAME ] || [ $POD_NAME = "" ]; then POD_NAME=$DEFAULT_POD_NAME; fi && \
    DATE_TIME=$(date '+%Y-%m-%d_%H-%M-%S.%N') && \
    LOG_DIR="/logs/"$FULL_MODEL_NAME"/" && \
    LOG_FILE=$FULL_MODEL_NAME"_"$DATE_TIME"_"$POD_NODE"_"$POD_NAME".log" && \
    LOG_PATH=$LOG_DIR$LOG_FILE && \
    mkdir -p $LOG_DIR && \
    python -m deeppavlov $RUN_CMD $CONFIG -d > $LOG_PATH 2>&1

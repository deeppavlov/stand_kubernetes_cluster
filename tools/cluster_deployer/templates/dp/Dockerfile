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

ARG CONFIG
ARG COMMIT
ARG FULL_MODEL_NAME
ARG MODEL_ARGS
ARG RUN_CMD

ENV CONFIG=$CONFIG
ENV DEFAULT_POD_NODE="unknown_node"
ENV DEFAULT_POD_NAME="unknown_pod"
ENV MODEL_NAME=$FULL_MODEL_NAME
ENV RUN_CMD=$RUN_CMD

WORKDIR /app

RUN if [[ $COMMIT != "" ]]; then \
        cd /base/DeepPavlov && \
        git fetch --all --tags --prune && \
        git checkout $COMMIT && \
        python setup.py develop && \
        python -c 'import deeppavlov.models' && \
        rm -rf /root/.cache; \
    fi && \
    sed -i "/enabled/s/false/true/g" "/base/DeepPavlov/deeppavlov/utils/settings/dialog_logger_config.json" && \
    sed -i "/agent_name/s/dp_agent/dp_api/g" "/base/DeepPavlov/deeppavlov/utils/settings/dialog_logger_config.json" && \
    sed -i "s|~/.deeppavlov|/logs/"$FULL_MODEL_NAME"|g" "/base/DeepPavlov/deeppavlov/utils/settings/dialog_logger_config.json" && \
    sed -i -E "/model_endpoint/s/\"\/.+\"/\"\/answer\"/g" "/base/DeepPavlov/deeppavlov/utils/settings/server_config.json" && \
    sed -i -E "/model_args_names/s/\[.+\]/"$MODEL_ARGS"/g" "/base/DeepPavlov/deeppavlov/utils/settings/server_config.json" && \
    python -m deeppavlov install $CONFIG

CMD if [ -z $POD_NODE ] || [ $POD_NODE = "" ]; then POD_NODE=$DEFAULT_POD_NODE; fi && \
    if [ -z $POD_NAME ] || [ $POD_NAME = "" ]; then POD_NAME=$DEFAULT_POD_NAME; fi && \
    sed -i "s|dialog_logs|"$POD_NODE"|g" "/base/DeepPavlov/deeppavlov/utils/settings/dialog_logger_config.json" && \
    DATE_TIME=$(date '+%Y-%m-%d_%H-%M-%S.%N') && \
    LOG_DIR="/logs/"$MODEL_NAME"/" && \
    LOG_FILE=$MODEL_NAME"_"$DATE_TIME"_"$POD_NODE"_"$POD_NAME".log" && \
    LOG_PATH=$LOG_DIR$LOG_FILE && \
    mkdir -p $LOG_DIR && \
    python -m deeppavlov $RUN_CMD $CONFIG -d > $LOG_PATH 2>&1

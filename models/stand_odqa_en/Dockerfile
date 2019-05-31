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

FROM stand/docker_deeppavlov:cuda-9.0

VOLUME /logs
VOLUME /root/.deeppavlov
WORKDIR /app
ADD . /app

RUN cd /base/DeepPavlov && \
    git fetch --all --tags --prune && \
    git checkout master && \
    python3.6 setup.py develop

RUN pip install -r /base/DeepPavlov/deeppavlov/requirements/tf-gpu.txt && \
    python3.6 -m deeppavlov install /base/DeepPavlov/deeppavlov/configs/odqa/en_odqa_pop_infer_enwiki20180211.json && \
    cp /app/configs/*.json /base/DeepPavlov/deeppavlov/utils/settings

EXPOSE 5000

ENV MODEL_NAME=stand_odqa_en
ENV DEFAULT_POD_NODE="unknown_node"
ENV DEFAULT_POD_NAME="unknown_pod"

CMD if [ -z $POD_NODE ] || [ $POD_NODE = "" ]; then POD_NODE=$DEFAULT_POD_NODE; fi && \
    if [ -z $POD_NAME ] || [ $POD_NAME = "" ]; then POD_NAME=$DEFAULT_POD_NAME; fi && \
    sed -i "s/\/dialog_logs/\/"$POD_NODE"\/dialog_logs/g" "/base/DeepPavlov/deeppavlov/utils/settings/dialog_logger_config.json" && \
    DATE_TIME=$(date '+%Y-%m-%d_%H-%M-%S.%N') && \
    LOG_DIR="/logs/"$MODEL_NAME"/"$POD_NODE"/logs/" && \
    LOG_FILE=$MODEL_NAME"_"$DATE_TIME"_"$POD_NAME".log" && \
    LOG_PATH=$LOG_DIR$LOG_FILE && \
    mkdir -p $LOG_DIR && \
    python3.6 -m deeppavlov.deep  riseapi    /base/DeepPavlov/deeppavlov/configs/odqa/en_odqa_pop_infer_enwiki20180211.json -d > $LOG_PATH 2>&1
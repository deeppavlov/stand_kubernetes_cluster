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

FROM stand/docker_deeppavlov:cuda-{{CUDA_VERSION}}

VOLUME /logs
WORKDIR /app
ADD . /app

RUN cd /base/DeepPavlov && \
    git checkout {{BRANCH}} && \
    git fetch && \
    git pull origin {{BRANCH}} && \
    python3.6 setup.py develop && \
    pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-2.0.0/en_core_web_sm-2.0.0.tar.gz#en_core_web_sm

RUN python3.6 -m deeppavlov.deep download /base/DeepPavlov/deeppavlov/configs/{{CONFIG_FILE}} && \
    cp /app/configs/server_config.json /base/DeepPavlov/utils/server_utils/server_config.json

EXPOSE {{PORT}}

ENV MODEL_NAME={{FULL_MODEL_NAME}}
ENV DEFAULT_POD_NODE="unknown_node"
ENV DEFAULT_POD_NAME="unknown_pod"

CMD if [ -z $POD_NODE ] || [ $POD_NODE = "" ]; then POD_NODE=$DEFAULT_POD_NODE; fi && \
    if [ -z $POD_NAME ] || [ $POD_NAME = "" ]; then POD_NAME=$DEFAULT_POD_NAME; fi && \
    DATE_TIME=$(date '+%Y-%m-%d_%H-%M-%S.%N') && \
    LOG_DIR="/logs/"$MODEL_NAME"/"$POD_NODE"/" && \
    LOG_FILE=$MODEL_NAME"_"$DATE_TIME"_"$POD_NAME".log" && \
    LOG_PATH=$LOG_DIR$LOG_FILE && \
    mkdir -p $LOG_DIR && \
    python3.6 -m deeppavlov.deep {{RUN_CMD}} /base/DeepPavlov/deeppavlov/configs/{{CONFIG_FILE}} > $LOG_PATH 2>&1
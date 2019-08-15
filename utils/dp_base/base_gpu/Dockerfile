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

FROM nvidia/cuda:{{CUDA_VERSION}}-{{CUDA_DIST}}

ENV CUDNN_VERSION {{CUDNN_VERSION}}
ENV PYTHON_VERSION {{PYTHON_VERSION}}
LABEL com.nvidia.cudnn.version="${CUDNN_VERSION}"

VOLUME /logs
VOLUME /root/.deeppavlov
WORKDIR /app
ADD . /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends dpkg-dev gcc git	libbz2-dev libc6-dev \
        libcudnn7=$CUDNN_VERSION-1+cuda{{CUDA_VERSION}} libcudnn7-dev=$CUDNN_VERSION-1+cuda{{CUDA_VERSION}} \
        libexpat1-dev libffi-dev libgdbm-dev liblzma-dev libncursesw5-dev libreadline-dev libsqlite3-dev libssl-dev \
        locales make tk-dev wget xz-utils zlib1g-dev && \
    locale-gen en_US.UTF-8 && \
    locale-gen ru_RU.UTF-8 && \
    wget --no-check-certificate -O python.tar.xz https://www.python.org/ftp/python/$PYTHON_VERSION/Python-$PYTHON_VERSION.tar.xz && \
    mkdir -p /usr/src/python && \
	tar -xC /usr/src/python --strip-components=1 -f python.tar.xz && \
    rm python.tar.xz && \
    cd /usr/src/python && \
	./configure && \
	make -j "$(nproc)" altinstall && \
    cd /app && \
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false && \
	rm -rf /usr/src/python \
	    /var/lib/apt/lists/* && \
    ln -s /usr/local/bin/python${PYTHON_VERSION%.*} /usr/local/bin/python && \
    ln -s /usr/local/bin/pip${PYTHON_VERSION%.*} /usr/local/bin/pip

ENV LANG='en_US.UTF-8' LANGUAGE='en_US.UTF-8' LC_ALL='en_US.UTF-8'

RUN git clone https://github.com/deepmipt/DeepPavlov.git && \
    cd DeepPavlov && \
    git checkout {{BRANCH}} && \
    python setup.py develop && \
    python -c 'import deeppavlov.models' && \
    pip install -r deeppavlov/requirements/tf-gpu.txt && \
    rm -rf /root/.cache

RUN python -m deeppavlov install DeepPavlov/deeppavlov/configs/{{CONFIG_FILE}} && \
    cp configs/*.json DeepPavlov/deeppavlov/utils/settings

EXPOSE {{PORT}}

ENV MODEL_NAME={{FULL_MODEL_NAME}}
ENV DEFAULT_POD_NODE="unknown_node"
ENV DEFAULT_POD_NAME="unknown_pod"

CMD if [ -z $POD_NODE ] || [ $POD_NODE = "" ]; then POD_NODE=$DEFAULT_POD_NODE; fi && \
    if [ -z $POD_NAME ] || [ $POD_NAME = "" ]; then POD_NAME=$DEFAULT_POD_NAME; fi && \
    sed -i "s/\/dialog_logs/\/"$POD_NODE"\/dialog_logs/g" DeepPavlov/deeppavlov/utils/settings/dialog_logger_config.json && \
    DATE_TIME=$(date '+%Y-%m-%d_%H-%M-%S.%N') && \
    LOG_DIR="/logs/"$MODEL_NAME"/"$POD_NODE"/logs/" && \
    LOG_FILE=$MODEL_NAME"_"$DATE_TIME"_"$POD_NAME".log" && \
    LOG_PATH=$LOG_DIR$LOG_FILE && \
    mkdir -p $LOG_DIR && \
    python -m deeppavlov {{RUN_CMD}} DeepPavlov/deeppavlov/configs/{{CONFIG_FILE}} -d > $LOG_PATH 2>&1

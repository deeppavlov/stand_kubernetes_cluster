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

ARG NVIDIA_BASE_IMAGE
FROM $NVIDIA_BASE_IMAGE

ARG COMMIT=master
ARG CUDNN_VERSION
ARG PYTHON_VERSION

EXPOSE 5000

WORKDIR /base

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        dpkg-dev \
        gcc \
        git	\
        libbz2-dev \
        libc6-dev \
        libcudnn7=$CUDNN_VERSION-1+cuda${CUDA_VERSION%.*} \
        libcudnn7-dev=$CUDNN_VERSION-1+cuda${CUDA_VERSION%.*} \
        libexpat1-dev \
        libffi-dev \
        libgdbm-dev \
        liblzma-dev \
        libncursesw5-dev \
        libreadline-dev \
        libsqlite3-dev \
        libssl-dev \
        locales \
        make \
        tk-dev \
        wget \
        xz-utils \
        zlib1g-dev && \
    locale-gen en_US.UTF-8 && \
    locale-gen ru_RU.UTF-8 && \
    wget --no-check-certificate -O python.tar.xz https://www.python.org/ftp/python/$PYTHON_VERSION/Python-$PYTHON_VERSION.tar.xz && \
    mkdir -p /usr/src/python && \
	tar -xC /usr/src/python --strip-components=1 -f python.tar.xz && \
    rm python.tar.xz && \
    cd /usr/src/python && \
	./configure && \
	make -j "$(nproc)" altinstall && \
	ln -s /usr/local/bin/python${PYTHON_VERSION%.*} /usr/local/bin/python && \
    ln -s /usr/local/bin/pip${PYTHON_VERSION%.*} /usr/local/bin/pip && \
    pip install virtualenv==16.7.5 && \
    virtualenv /base/venv && \
	mkdir -p /venv/dp_internal_token_dir && \
    cd /base && \
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false && \
	rm -rf /usr/src/python \
	    /var/lib/apt/lists/*

ENV PATH=/base/venv/bin:$PATH
ENV LANG='en_US.UTF-8' LANGUAGE='en_US.UTF-8' LC_ALL='en_US.UTF-8'

RUN git clone https://github.com/deepmipt/DeepPavlov.git && \
    cd DeepPavlov && \
    git checkout $COMMIT && \
    python setup.py develop && \
    python -c 'import deeppavlov.models' && \
    pip install -r deeppavlov/requirements/tf-gpu.txt && \
    rm -rf /root/.cache

ENV DP_SKIP_NLTK_DOWNLOAD='True'

CMD if [ -d /venv/$CONFIG ]; then \
        PATH=/venv/$CONFIG/bin:$PATH; \
    else \
        if [ ! -z $COMMIT ]; then \
            cd /base/DeepPavlov && \
            git fetch --all --tags --prune && \
            git checkout $COMMIT && \
            python setup.py develop; \
        fi && \
        python -m deeppavlov install $CONFIG && \
        if [ ! -d /venv/dp_internal_token_dir ]; then \
            mkdir /venv/$CONFIG && \
            cp -R /base/venv/* /venv/$CONFIG; \
        fi; \
    fi && \
    python -m deeppavlov riseapi $CONFIG -p 5000 -d
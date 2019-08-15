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

ARG PYTHON_BASE_IMAGE=${PYTHON_BASE_IMAGE}
FROM ${PYTHON_BASE_IMAGE}

ARG COMMIT=master

EXPOSE 5000

VOLUME /logs
VOLUME /root/.deeppavlov

WORKDIR /base

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        git \
        locales && \
    printf '%s\n%s\n' 'en_US.UTF-8 UTF-8' 'ru_RU.UTF-8 UTF-8' >> /etc/locale.gen && \
    locale-gen && \
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false && \
	rm -rf /var/lib/apt/lists/*

ENV LANG='en_US.UTF-8' LANGUAGE='en_US.UTF-8' LC_ALL='en_US.UTF-8'

RUN git clone https://github.com/deepmipt/DeepPavlov.git && \
    cd DeepPavlov && \
    git checkout $COMMIT && \
    python setup.py develop && \
    python -c 'import deeppavlov.models' && \
    rm -rf /root/.cache

CMD if [ ! -z $COMMIT ]; then \
        cd /base/DeepPavlov && \
        git fetch --all --tags --prune && \
        git checkout $COMMIT && \
        python setup.py develop && \
        python -c 'import deeppavlov.models'; \
    fi && \
    python -m deeppavlov install $CONFIG && \
    python -m deeppavlov riseapi $CONFIG -p 5000 -d > "/logs"/${CONFIG}".log" 2>&1

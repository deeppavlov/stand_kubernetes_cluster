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

ARG CUDNN_VERSION
ARG PYTHON_VERSION

VOLUME /logs
VOLUME /.storage

ENV DEFAULT_USER default
ENV DEBIAN_FRONTEND noninteractive

WORKDIR /root

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
        openssh-server \
        make \
        sudo \
        tk-dev \
        wget \
        xz-utils \
        zlib1g-dev && \
    locale-gen en_US.UTF-8 && \
    locale-gen ru_RU.UTF-8 && \
    # Install python
    wget --no-check-certificate -O python.tar.xz https://www.python.org/ftp/python/$PYTHON_VERSION/Python-$PYTHON_VERSION.tar.xz && \
    mkdir -p /usr/src/python && \
	tar -xC /usr/src/python --strip-components=1 -f python.tar.xz && \
    rm python.tar.xz && \
    cd /usr/src/python && \
	./configure && \
	make -j "$(nproc)" altinstall && \
	ln -s /usr/local/bin/python${PYTHON_VERSION%.*} /usr/local/bin/python && \
    ln -s /usr/local/bin/pip${PYTHON_VERSION%.*} /usr/local/bin/pip && \
    # Enable ssh
    mkdir /var/run/sshd && \
    sed -ri 's/UsePAM yes/#UsePAM yes/g' /etc/ssh/sshd_config && \
    mkdir /root/.ssh && \
    # Cleanup
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false && \
	rm -rf /usr/src/python \
	    /var/lib/apt/lists/*

ENV LANG='en_US.UTF-8' LANGUAGE='en_US.UTF-8' LC_ALL='en_US.UTF-8'

CMD if [ -d /.storage/internal_token_dir ]; then \
        if [ -z $USER_NAME ]; then \
            USER_NAME=$DEFAULT_USER; \
        fi && \
        useradd -ms /bin/bash -p $(openssl passwd -1 $USER_NAME) $USER_NAME && \
        usermod -aG sudo $USER_NAME && \
        if [ ! -d "/.storage/${USER_NAME}" ]; then \
            mkdir "/.storage/${USER_NAME}" && \
            cp -r /usr /var/lib/apt/lists "/home/${USER_NAME}" "/.storage/${USER_NAME}"; \
        fi && \
        rm -rf /usr \
               /var/lib/apt/lists \
               "/home/${USER_NAME}" \
               "/.storage/${USER_NAME}/lists/lock" && \
        ln -s "/.storage/${USER_NAME}/${USER_NAME}" "/home/${USER_NAME}" && \
        ln -s "/.storage/${USER_NAME}/usr" /usr && \
        ln -s "/.storage/${USER_NAME}/lists" /var/lib/apt/lists && \
        chmod 4755 /usr/bin/sudo; \
    fi && \
    /usr/sbin/sshd -D
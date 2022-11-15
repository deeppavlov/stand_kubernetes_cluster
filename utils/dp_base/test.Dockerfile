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

RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    pip --no-cache-dir install pytest pexpect && \
    DP_VERSION=$(python -c 'import deeppavlov; print(deeppavlov.__version__)') && \
    git clone --depth 1 --branch $DP_VERSION https://github.com/deeppavlov/DeepPavlov && \
    mv DeepPavlov/tests/* ./ && \
    sed -i '/install_config(config_file_path)/d' ./test_quick_start.py && \
    rm -r DeepPavlov && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

ENV DP_PYTEST_NO_CACHE=True

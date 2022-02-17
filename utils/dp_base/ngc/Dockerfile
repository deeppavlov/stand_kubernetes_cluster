# Copyright 2020 Neural Networks and Deep Learning lab, MIPT
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

ARG NGC_BASE_IMAGE
FROM $NGC_BASE_IMAGE

ARG COMMIT=master

EXPOSE 5000

RUN git clone https://github.com/deepmipt/DeepPavlov.git && \
    cd DeepPavlov && \
    git checkout $COMMIT && \
    pip install -e . && \
    python -c 'import deeppavlov.models' && \
    ls deeppavlov/requirements -I tf.txt -I tf-gpu.txt | while read filename; do pip install -r deeppavlov/requirements/$filename; done && \
    pip install -r deeppavlov/requirements/nemo-pytorch.txt && \
    rm -rf /root/.cache

ENV DP_SKIP_NLTK_DOWNLOAD='True'

CMD python -m deeppavlov riseapi $CONFIG -p 5000 -d
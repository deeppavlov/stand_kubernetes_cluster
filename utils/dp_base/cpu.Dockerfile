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

WORKDIR /app

ARG DP_VERSION

RUN pip --no-cache-dir install deeppavlov==$DP_VERSION && \
    SP_PATH=$(pip show deeppavlov | grep Location | awk '{print $2}') && \
    cat $SP_PATH/deeppavlov/requirements/*.txt | xargs pip install --no-cache-dir && \
    python -c 'import deeppavlov.models'

ENV DP_SKIP_NLTK_DOWNLOAD='True'

EXPOSE 5000

CMD python -m deeppavlov riseapi $CONFIG -p 5000 $([ -z $SKIP_DOWNLOAD ] && echo -d)

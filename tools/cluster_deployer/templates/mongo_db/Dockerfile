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

FROM mongo:{{MONGO_DOCKER_TAG}}

VOLUME /db_data

ENV MODEL_NAME={{FULL_MODEL_NAME}}

EXPOSE 27017

ENTRYPOINT ["docker-entrypoint.sh"]

CMD DB_DATA_DIR="/db_data/"$MODEL_NAME"/mongo_db_data" && \
    mkdir -p $DB_DATA_DIR && \
    chown -R mongodb:mongodb $DB_DATA_DIR && \
    docker-entrypoint.sh --dbpath $DB_DATA_DIR
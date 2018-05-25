FROM stand/docker_deeppavlov:cuda-8.0

VOLUME /logs
WORKDIR /app
ADD . /app

RUN python3.6 -m deeppavlov.deep download /base/DeepPavlov/deeppavlov/configs/odqa/ru_odqa_infer_prod.json && \
    cp /app/configs/server_config.json /base/DeepPavlov/utils/server_utils/server_config.json && \
    pip install tensorflow-gpu==1.4.0

RUN mkdir -p /base/DeepPavlov/download/odqa && \
    mkdir -p /base/DeepPavlov/download/embeddings && \
    cd /base/DeepPavlov/download/odqa && \
    wget http://lnsigo.mipt.ru/export/datasets/wikipedia/ruwiki.db && \
    cd /base/DeepPavlov/download/embeddings && \
    wget http://lnsigo.mipt.ru/export/embeddings/ft_native_300_ru_wiki_lenta_nltk_word_tokenize/ft_native_300_ru_wiki_lenta_nltk_word_tokenize.vec && \
    wget http://lnsigo.mipt.ru/export/embeddings/ft_native_300_ru_wiki_lenta_nltk_word_tokenize-char.vec

EXPOSE 6012

ENV MODEL_NAME="stand_odqa_en"
ENV DEFAULT_POD_NODE="unknown_node"
ENV DEFAULT_POD_NAME="unknown_pod"

CMD if [ -z $POD_NODE ] || [ $POD_NODE = "" ]; then POD_NODE=$DEFAULT_POD_NODE; fi && \
    if [ -z $POD_NAME ] || [ $POD_NAME = "" ]; then POD_NAME=$DEFAULT_POD_NAME; fi && \
    DATE_TIME=$(date '+%Y-%m-%d_%H-%M-%S.%N') && \
    LOG_DIR="/logs/"$MODEL_NAME"/"$POD_NODE"/" && \
    LOG_FILE=$MODEL_NAME"_"$DATE_TIME"_"$POD_NAME".log" && \
    LOG_PATH=$LOG_DIR$LOG_FILE && \
    mkdir -p $LOG_DIR && \
    python3.6 -m deeppavlov.deep riseapi /base/DeepPavlov/deeppavlov/configs/odqa/ru_odqa_infer_prod.json > $LOG_PATH 2>&1
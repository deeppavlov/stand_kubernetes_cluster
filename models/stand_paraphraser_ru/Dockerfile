FROM stand/docker_cuda:8.0

VOLUME /logs
WORKDIR /app
ADD . /app

RUN pip install pip==9.0.1 && \
    git clone https://github.com/deepmipt/kpi2017.git && \
    cd /app/kpi2017 && \
    cp /app/configs/requirements.txt . && \
    pip install Cython==0.26.0 && \
    pip install -r requirements.txt && \
    python3.6 setup.py develop && \
    printf "import nltk\nnltk.download('punkt')" | python3.6 && \
    cd /app && \
    git clone https://github.com/deepmipt/deepreply.git && \
    cd /app/deepreply && \
    git checkout api2 && \
    cp /app/configs/api.py . && \
    cp /app/configs/tester_base.py . && \
    cp /app/configs/config.json . && \
    pip install -r requirements.txt && \
    mkdir build && \
    cd build && \
    wget http://lnsigo.mipt.ru/export/embeddings/ft_0.8.3_nltk_yalen_sg_300.bin && \
    wget http://lnsigo.mipt.ru/export/models/paraphraser.tar.gz

EXPOSE 6003

ENV MODEL_NAME="stand_paraphraser_ru"
ENV DEFAULT_POD_NODE="unknown_node"
ENV DEFAULT_POD_NAME="unknown_pod"

CMD if [ -z $POD_NODE ] || [ $POD_NODE = "" ]; then POD_NODE=$DEFAULT_POD_NODE; fi && \
    if [ -z $POD_NAME ] || [ $POD_NAME = "" ]; then POD_NAME=$DEFAULT_POD_NAME; fi && \
    DATE_TIME=$(date '+%Y-%m-%d_%H-%M-%S.%N') && \
    LOG_DIR="/logs/"$MODEL_NAME"/"$POD_NODE"/" && \
    LOG_FILE=$MODEL_NAME"_"$DATE_TIME"_"$POD_NAME".log" && \
    LOG_PATH=$LOG_DIR$LOG_FILE && \
    mkdir -p $LOG_DIR && \
    cd /app/deepreply && \
    python3.6 api.py > $LOG_PATH 2>&1
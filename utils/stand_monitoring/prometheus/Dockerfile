FROM ubuntu:16.04

VOLUME /logs
WORKDIR /prometheus

ADD configs/prometheus_kubernetes.yml /prometheus

ENV PROMETHEUS_URL="https://github.com/prometheus/prometheus/releases/download/v2.2.1/prometheus-2.2.1.linux-amd64.tar.gz"
ENV GRAFANA_URL="https://s3-us-west-2.amazonaws.com/grafana-releases/release/grafana_5.2.1_amd64.deb"

RUN apt-get update && \
    apt-get -y install wget && \
    wget $PROMETHEUS_URL -O prometheus.tar.gz && \
    tar xvfz prometheus.tar.gz && \
    rm prometheus.tar.gz && \
    mv prometheus-* prometheus

WORKDIR /grafana

ADD configs/grafana_cluster_dashboard.json /grafana

RUN apt-get -y install libfontconfig && \
    wget $GRAFANA_URL -O grafana.deb && \
    dpkg -i grafana.deb

EXPOSE 3000
EXPOSE 9090

ENV MODEL_NAME="utils_monitoring"
ENV DEFAULT_POD_NODE="unknown_node"
ENV DEFAULT_POD_NAME="unknown_pod"

CMD if [ -z $POD_NODE ] || [ $POD_NODE = "" ]; then POD_NODE=$DEFAULT_POD_NODE; fi && \
    if [ -z $POD_NAME ] || [ $POD_NAME = "" ]; then POD_NAME=$DEFAULT_POD_NAME; fi && \
    DATE_TIME=$(date '+%Y-%m-%d_%H-%M-%S.%N') && \
    LOG_DIR="/logs/"$MODEL_NAME"/"$POD_NODE"/" && \
    LOG_FILE=$MODEL_NAME"_"$DATE_TIME"_"$POD_NAME".log" && \
    LOG_PATH=$LOG_DIR$LOG_FILE && \
    mkdir -p $LOG_DIR && \
    service grafana-server start && \
    /prometheus/prometheus/prometheus --config.file=/prometheus/prometheus_kubernetes.yml > $LOG_PATH 2>&1
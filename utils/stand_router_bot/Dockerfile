FROM ubuntu:18.04

WORKDIR /app
VOLUME /logs
VOLUME /app/router_bot_volume

EXPOSE 22
EXPOSE 80

ENV DEBIAN_FRONTEND=noninteractive
ENV PROXYCHAINS_CONF_FILE="/app/proxychains.conf"
ENV DEFAULT_POD_NODE="unknown_node"
ENV DEFAULT_POD_NAME="unknown_pod"
ENV NOTVISIBLE="in users profile"

# Install basic dependencies
RUN apt-get update && \
    apt-get install -y tzdata && \
    apt-get -y install systemd && \
    apt-get -y install locales && locale-gen en_US.UTF-8 && locale-gen ru_RU.UTF-8 && \
    apt-get -y install git && \
    git config --global user.email "litinsky@ipavlov.ai" && \
    git config --global user.name "litinsky" && \
    # Enable ssh
    apt-get -y install openssh-server && \
    mkdir /var/run/sshd && \
    echo 'root:root' | chpasswd && \
    sed -ri 's/^#?PermitRootLogin\s+.*/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -ri 's/UsePAM yes/#UsePAM yes/g' /etc/ssh/sshd_config && \
    mkdir /root/.ssh && \
    # Install Python
    apt-get -y install wget && \
    apt-get -y install tar && \
    apt-get -y install gcc-6 g++-6 && \
    apt-get -y install build-essential libssl-dev zlib1g-dev libncurses5-dev libreadline-dev libgdbm-dev libdb5.3-dev libbz2-dev liblzma-dev libsqlite3-dev libffi-dev tcl-dev tk tk-dev && \
    wget https://www.python.org/ftp/python/3.6.5/Python-3.6.5.tar.xz && \
    tar xf Python-3.6.5.tar.xz && \
    cd Python-3.6.5 && \
    ./configure && \
    make altinstall && \
    #Install pip
    cd /app && \
    wget https://bootstrap.pypa.io/get-pip.py && \
    python3.6 get-pip.py

ENV LANG='en_US.UTF-8' LANGUAGE='en_US.UTF-8' LC_ALL='en_US.UTF-8'

# Install proxychains-ng
RUN cd /app && \
    git clone https://github.com/rofl0r/proxychains-ng.git && \
    cd /app/proxychains-ng && \
    make

# Install RouterBot
RUN cd /app && \
    git clone https://github.com/deepmipt/convai_router_bot.git && \
    cd /app/convai_router_bot && \
    pip install -r requirements.txt

ADD ./config.yml /app/convai_router_bot/settings/config.yml
ADD ./proxychains.conf /app
ADD ./run_routerbot.sh /app
ADD ./stop_routerbot.sh /app

RUN chmod +x /app/run_routerbot.sh
RUN chmod +x /app/stop_routerbot.sh

CMD sed -i 's|{{MONGO_PROTOCOL}}|'${MONGO_PROTOCOL}'|g' '/app/convai_router_bot/settings/config.yml' && \
    sed -i 's|{{MONGO_HOST}}|'${MONGO_HOST}'|g' '/app/convai_router_bot/settings/config.yml' && \
    sed -i 's|{{MONGO_PORT}}|'${MONGO_PORT}'|g' '/app/convai_router_bot/settings/config.yml' && \
    sed -i 's|{{FB_PAGE_ACCESS_TOKEN}}|'${FB_PAGE_ACCESS_TOKEN}'|g' '/app/convai_router_bot/settings/config.yml' && \
    sed -i 's|{{FB_WEBHOOK}}|'${FB_WEBHOOK}'|g' '/app/convai_router_bot/settings/config.yml' && \
    sed -i 's|{{FB_WEBHOOK_SECRET}}|'${FB_WEBHOOK_SECRET}'|g' '/app/convai_router_bot/settings/config.yml' && \
    sed -i 's|{{TG_WEBHOOK}}|'${TG_WEBHOOK}'|g' '/app/convai_router_bot/settings/config.yml' && \
    sed -i 's|{{TG_TOKEN}}|'${TG_TOKEN}'|g' '/app/convai_router_bot/settings/config.yml' && \
    echo ${PROXYCHAINS_CONFIG_STRING} >> ${PROXYCHAINS_CONF_FILE} && \
    MONGO_URI=${MONGO_PROTOCOL}'://'${MONGO_HOST}':'${MONGO_PORT}'/convai' && \
    if [ -z ${POD_NODE} ] || [ ${POD_NODE} = "" ]; then POD_NODE=${DEFAULT_POD_NODE}; fi && \
    if [ -z ${POD_NAME} ] || [ ${POD_NAME} = "" ]; then POD_NAME=${DEFAULT_POD_NAME}; fi && \
    sed -i 's|{{MODEL_NAME}}|'${MODEL_NAME}'|g' '/app/run_routerbot.sh' && \
    sed -i 's|{{POD_NODE}}|'${POD_NODE}'|g' '/app/run_routerbot.sh' && \
    sed -i 's|{{POD_NAME}}|'${POD_NAME}'|g' '/app/run_routerbot.sh' && \
    /app/run_routerbot.sh && \
    /usr/sbin/sshd -D
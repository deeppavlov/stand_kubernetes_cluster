FROM nginx:1.13.12

RUN rm /etc/nginx/conf.d/*.conf

WORKDIR /usr/src

ADD start.sh /usr/src/
ADD http_proxy.conf /etc/nginx/conf.d/

RUN chmod +x start.sh

ENTRYPOINT ./start.sh
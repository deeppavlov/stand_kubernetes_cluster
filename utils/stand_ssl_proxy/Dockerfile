FROM nginx:1.13.12

RUN rm /etc/nginx/conf.d/*.conf

WORKDIR /usr/src

RUN mkdir -p /etc/certs
ADD certs/* /etc/certs/
ADD start.sh /usr/src/
ADD ssl_proxy.conf /etc/nginx/conf.d/

RUN chmod +x start.sh

ENTRYPOINT ./start.sh
#!/bin/bash

CERT_PATH="/etc/certs/nginx.crt"
KEY_PATH="/etc/certs/nginx.key"

DEFAULT_LISTENED_PORT="443"
DEFAULT_PROXYED_HOST="0.0.0.0"
DEFAULT_PROXYED_PORT="5000"

if [ -n "$USE_SECRET" ] && [ "$USE_SECRET" = "true" ]; then
    CERT_PATH="/etc/secret/proxycert" && \
    KEY_PATH="/etc/secret/proxykey";
fi

CERT_PATH=$(echo $CERT_PATH | sed 's/\//\\\//g')
KEY_PATH=$(echo $KEY_PATH | sed 's/\//\\\//g')

if [ -z $LISTENED_PORT ]; then LISTENED_PORT=$DEFAULT_LISTENED_PORT; fi
if [ -z $PROXYED_HOST ]; then PROXYED_HOST=$DEFAULT_PROXYED_HOST; fi
if [ -z $PROXYED_PORT ]; then PROXYED_PORT=$DEFAULT_PROXYED_PORT; fi

sed -i "s/{{TARGET_SERVICE}}/${PROXYED_HOST}:${PROXYED_PORT}/g" /etc/nginx/conf.d/ssl_proxy.conf
sed -i "s/{{LISTENED_PORT}}/${LISTENED_PORT}/g" /etc/nginx/conf.d/ssl_proxy.conf
sed -i "s/{{CERT_PATH}}/${CERT_PATH}/g" /etc/nginx/conf.d/ssl_pod_proxy.conf
sed -i "s/{{KEY_PATH}}/${KEY_PATH}/g" /etc/nginx/conf.d/ssl_pod_proxy.conf

nginx -g 'daemon off;'
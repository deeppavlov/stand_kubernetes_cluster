#!/bin/bash

DEFAULT_LISTENED_PORT="5000"
DEFAULT_PROXYED_HOST="0.0.0.0"
DEFAULT_PROXYED_PORT="5000"

if [ -z $LISTENED_PORT ]; then LISTENED_PORT=$DEFAULT_LISTENED_PORT; fi
if [ -z $PROXYED_HOST ]; then PROXYED_HOST=$DEFAULT_PROXYED_HOST; fi
if [ -z $PROXYED_PORT ]; then PROXYED_PORT=$DEFAULT_PROXYED_PORT; fi

sed -i "s/{{TARGET_SERVICE}}/${PROXYED_HOST}:${PROXYED_PORT}/g" /etc/nginx/conf.d/http_proxy.conf
sed -i "s/{{LISTENED_PORT}}/${LISTENED_PORT}/g" /etc/nginx/conf.d/http_proxy.conf

nginx -g 'daemon off;'
#!/bin/bash

SOURCE_CERT_PATH="certs/nginx.crt"
SOURCE_KEY_PATH="certs/nginx.key"
SECRET_CONFIG_TEMPLATE_PATH="../../kuber_configs/common/secrets/ssl_proxy/stand_ssl_proxy_st_template.yaml"
SECRET_CONFIG_PATH="../../kuber_configs/common/secrets/ssl_proxy/secret/stand_ssl_proxy_st.yaml"

cp $SECRET_CONFIG_TEMPLATE_PATH $SECRET_CONFIG_PATH

CERT=$(echo $(cat $SOURCE_CERT_PATH | base64) | sed 's/[[:space:]]//g')
KEY=$(echo $(cat $SOURCE_KEY_PATH | base64) | sed 's/[[:space:]]//g')

sed -i "s/proxycert:.*/proxycert: ${CERT}/g" $SECRET_CONFIG_PATH
sed -i "s/proxykey:.*/proxykey: ${KEY}/g" $SECRET_CONFIG_PATH
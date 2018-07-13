#!/bin/bash

openssl req -x509 -nodes -newkey rsa:2048 -keyout certs/nginx.key -out certs/nginx.crt -subj "/C=RU/ST=Moscow/L=Moscow/O=DeepPavlov/CN=demo"

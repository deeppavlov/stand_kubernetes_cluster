#!/bin/bash
source ./env/bin/activate &&
nohup python3.6 poller.py > ./poller.log 2>&1 &
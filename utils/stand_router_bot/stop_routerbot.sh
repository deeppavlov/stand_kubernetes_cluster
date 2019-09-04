#!/bin/sh
ROUTER_PID=$(ps aux | grep application.py | grep -v grep | awk '{print $2}')

if [ ${ROUTER_PID} ]; then
    kill -9 ${ROUTER_PID}
    echo 'Router bot with PID '${ROUTER_PID}' stopped'
else
    echo 'Router bot is not running'
fi
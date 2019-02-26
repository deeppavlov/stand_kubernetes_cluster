#!/bin/bash
source ./env/bin/activate &&
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/cuda/lib64/ &&
nohup python3.6 -m deeppavlov.deep {{RUN_CMD}} DeepPavlov/deeppavlov/configs/{{CONFIG_FILE}} > ./{{LOG_FILE}} 2>&1 &
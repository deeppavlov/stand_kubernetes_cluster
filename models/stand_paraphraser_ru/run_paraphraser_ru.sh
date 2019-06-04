#!/bin/bash
source ./env/bin/activate &&
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/cuda/lib64/ &&
nohup python3.6 -m deeppavlov.deep  riseapi    DeepPavlov/deeppavlov/configs/classifiers/paraphraser_bert.json > ./stand_paraphraser_ru.log 2>&1 &
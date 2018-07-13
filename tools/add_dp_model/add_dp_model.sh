#!/bin/bash

# USER INPUT
# =============================================================================
TEMPLATE='gpu'
BRANCH='dev'

MODEL_NAME='model_ru'
CONFIG_FILE='model/model.json'
CUDA_VERSION='8.0'
TF_VERSION='1.4.0'

PORT='6001'
CLUSTER_PORT='7001'
MODEL_ARGS='["text1"]'

PREFIX='stand'
DOCKER_REGISTRY='kubeadm.ipavlov.mipt.ru:5000'
# =============================================================================

# Tech
TEMPLATES_FOLDER='tools/add_dp_model/templates/'"$TEMPLATE"'/'
TEMP_FOLDER='tools/add_dp_model/temp/'
MODELS_FOLDER='models/'
KUBER_CONFIGS_FOLDER='kuber_configs/models/'

# Generated
FULL_MODEL_NAME="$PREFIX"'_'"$MODEL_NAME"
LOG_FILE="$PREFIX"'_'"$MODEL_NAME"'.log'
RUN_FILE='run_'"$MODEL_NAME"'.sh'

KUBER_DP_FILE="$PREFIX"'_'"$MODEL_NAME"'_dp.yaml'
KUBER_LB_FILE="$PREFIX"'_'"$MODEL_NAME"'_lb.yaml'

FULL_MODEL_NAME_DASHED=$(echo "$FULL_MODEL_NAME" | sed 's/_/-/g')

KUBER_DP_NAME="$FULL_MODEL_NAME_DASHED"'-dp'
KUBER_LB_NAME="$FULL_MODEL_NAME_DASHED"'-lb'
KUBER_IMAGE_TAG="$DOCKER_REGISTRY"'/'"$PREFIX"'/'"$MODEL_NAME"
KUBER_CONTAINER_PORT_NAME='cp'"$PORT"

# Generate
cd ../..

rm -rf "$TEMP_FOLDER"
cp -r "$TEMPLATES_FOLDER" "$TEMP_FOLDER"

for file in $(find "$TEMP_FOLDER" -type f -print0 | xargs -0 -I{} printf "%s\n" {}); do
    for slot in $(grep -oP "[\{][\{][A-Z_]*[\}][\}]" "$file"); do
        varname=$(echo "$slot" | sed 's/{//g')
        varname=$(echo "$varname" | sed 's/}//g')
        eval varvalue='$'$varname
        varvaluep=$(echo "$varvalue" | sed 's/\//\\\//g')
        sed -i "s/$slot/$varvaluep/g" "$file"
    done;
done

rm -rf "$MODELS_FOLDER"'/'"$FULL_MODEL_NAME"
mkdir -p "$MODELS_FOLDER"'/'"$FULL_MODEL_NAME"

cp -r "$TEMP_FOLDER"'/configs' "$MODELS_FOLDER"'/'"$FULL_MODEL_NAME"'/configs'
cp "$TEMP_FOLDER"'/Dockerfile' "$MODELS_FOLDER"'/'"$FULL_MODEL_NAME"'/Dockerfile'
cp "$TEMP_FOLDER"'/dockerignore' "$MODELS_FOLDER"'/'"$FULL_MODEL_NAME"'/.dockerignore'
cp "$TEMP_FOLDER"'/README.MD' "$MODELS_FOLDER"'/'"$FULL_MODEL_NAME"'/README.MD'
cp "$TEMP_FOLDER"'/run_model.sh' "$MODELS_FOLDER"'/'"$FULL_MODEL_NAME"'/'"$RUN_FILE"

rm -rf "$KUBER_CONFIGS_FOLDER"'/'"$FULL_MODEL_NAME"
mkdir -p "$KUBER_CONFIGS_FOLDER"'/'"$FULL_MODEL_NAME"

cp "$TEMP_FOLDER"'/kuber_dp.yaml' "$KUBER_CONFIGS_FOLDER"'/'"$FULL_MODEL_NAME"'/'"$KUBER_DP_FILE"
cp "$TEMP_FOLDER"'/kuber_lb.yaml' "$KUBER_CONFIGS_FOLDER"'/'"$FULL_MODEL_NAME"'/'"$KUBER_LB_FILE"

rm -rf "$TEMP_FOLDER"
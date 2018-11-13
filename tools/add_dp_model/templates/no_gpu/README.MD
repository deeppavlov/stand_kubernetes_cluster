# Demo stand. Model: {{MODEL_NAME}}

## Installation and start
1. Go to the `stand_kubernetes_cluster/{{MODELS_FOLDER}}{{FULL_MODEL_NAME}}` directory
2. Create a virtual environment with `Python 3.6`:
    ```
    virtualenv env -p python3.6
    ```
3. Activate the environment:
    ```
    source ./env/bin/activate
    ```
4. Install DeepPavlov:
    1. Clone the repo and `cd` to project root
        ```
        git clone https://github.com/deepmipt/DeepPavlov.git
        cd DeepPavlov
        ```
    2. Install DeepPavlov:
        ```
        python setup.py develop
        ```
    3. Download model components:
        ```
        python3.6 -m deeppavlov download deeppavlov/configs/{{CONFIG_FILE}}
        ```
    4. Install model dependencies:
        ```
        python3.6 -m deeppavlov install deeppavlov/configs/{{CONFIG_FILE}}
        ```
    5. Return to the `{{FULL_MODEL_NAME}}` dir:
        ```
        cd ..
        ```
5. Specify model endpoint host (`host`) and port (`port`) in `common_defaults` or corresponding model section of `DeepPavlov/utils/server_utils/server_config.json`
6. Specify virtual environment path (if necessary) in `{{RUN_FILE}}`
7. Run model:
    ```
    ./{{RUN_FILE}}
    ```

## Building and running with Docker:
1. If necessary, build base docker_cuda and docker_deeppavlov images for CUDA {{CUDA_VERSION}} from:

   https://github.com/deepmipt/stand_docker_base
  
2. Go to the `stand_kubernetes_cluster/models/{{FULL_MODEL_NAME}}` directory

3. Build Docker image:
   ```
   sudo docker build -t {{PREFIX}}/{{MODEL_NAME}} .
   ```
4. Run Docker image:
   ```
   sudo docker run -p <host_port>:{{PORT}} -v /path/to/host/vol/map/dir:/logs {{PREFIX}}/{{MODEL_NAME}}
   ```
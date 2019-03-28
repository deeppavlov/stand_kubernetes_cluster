# Demo stand. Model: odqa_ru

## Installation and start
1. Go to the `stand_kubernetes_cluster/models/stand_odqa_ru` directory
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
    2. Switch to branch master and update it:
        ```
        git checkout master
        git pull origin master
        ```
    3. Install DeepPavlov:
        ```
        python setup.py develop
        ```
    4. Download model components:
        ```
        python3.6 -m deeppavlov download deeppavlov/configs/odqa/ru_odqa_infer_wiki_retr_noans.json
        ```
    5. Install model dependencies:
        ```
        python3.6 -m deeppavlov install deeppavlov/configs/odqa/ru_odqa_infer_wiki_retr_noans.json
        ```
    6. Return to the `stand_odqa_ru` dir:
        ```
        cd ..
        ```
5. Specify model endpoint host (`host`) and port (`port`) in `common_defaults` or corresponding model section of `DeepPavlov/utils/server_utils/server_config.json`
6. Specify `CUDA_VISIBLE_DEVICES` and virtual environment path (if necessary) in `run_odqa_ru.sh`
7. Run model:
    ```
    ./run_odqa_ru.sh
    ```

## Building and running with Docker:
1. If necessary, build base docker_cuda and docker_deeppavlov images for CUDA 9.0 from:

   https://github.com/deepmipt/stand_docker_base
  
2. Go to the `stand_kubernetes_cluster/models/stand_odqa_ru` directory

3. Build Docker image:
   ```
   sudo docker build -t stand/odqa_ru .
   ```
4. Run Docker image:
   ```
   sudo docker run -p <host_port>:5000 --runtime=nvidia --device=/dev/nvidia<gpu_unit_int_id> -v /path/to/host/vol/map/dir:/logs stand/odqa_ru
   ```

# License

Apache 2.0 - licensed.
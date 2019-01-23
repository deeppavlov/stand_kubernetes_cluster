# Demo stand. Model: odqa_en

## Installation and start
1. Go to the `stand_kubernetes_cluster/models/stand_odqa_en` directory
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
        python3.6 -m deeppavlov download deeppavlov/configs/odqa/en_odqa_pop_infer_enwiki20180211.json
        ```
    4. Install model dependencies:
        ```
        python3.6 -m deeppavlov install deeppavlov/configs/odqa/en_odqa_pop_infer_enwiki20180211.json
        ```
    5. Return to the `stand_odqa_en` dir:
        ```
        cd ..
        ```
5. Specify model endpoint host (`host`) and port (`port`) in `common_defaults` or corresponding model section of `DeepPavlov/utils/server_utils/server_config.json`
6. Specify `CUDA_VISIBLE_DEVICES` and virtual environment path (if necessary) in `run_odqa_en.sh`
7. Run model:
    ```
    ./run_odqa_en.sh
    ```

## Building and running with Docker:
1. If necessary, build base docker_cuda and docker_deeppavlov images for CUDA 9.0 from:

   https://github.com/deepmipt/stand_docker_base
  
2. Go to the `stand_kubernetes_cluster/models/stand_odqa_en` directory

3. Build Docker image:
   ```
   sudo docker build -t stand/odqa_en .
   ```
4. Run Docker image:
   ```
   sudo docker run -p <host_port>:6011 --runtime=nvidia --device=/dev/nvidia<gpu_unit_int_id> -v /path/to/host/vol/map/dir:/logs stand/odqa_en
   ```
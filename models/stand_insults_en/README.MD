# Demo stand. Model: insults_en

## Installation and start
1. Go to the `stand_kubernetes_cluster/models/stand_insults_en` directory
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
        python3.6 -m deeppavlov download deeppavlov/configs/classifiers/insults_kaggle.json
        ```
    4. Install model dependencies:
        ```
        python3.6 -m deeppavlov install deeppavlov/configs/classifiers/insults_kaggle.json
        ```
    5. Return to the `stand_insults_en` dir:
        ```
        cd ..
        ```
5. Specify model endpoint host (`host`) and port (`port`) in `common_defaults` or corresponding model section of `DeepPavlov/utils/server_utils/server_config.json`
6. Specify virtual environment path (if necessary) in `run_insults_en.sh`
7. Run model:
    ```
    ./run_insults_en.sh
    ```

## Building and running with Docker:
1. If necessary, build base docker_cuda and docker_deeppavlov images for CUDA 9.0 from:

   https://github.com/deepmipt/stand_docker_base
  
2. Go to the `stand_kubernetes_cluster/models/stand_insults_en` directory

3. Build Docker image:
   ```
   sudo docker build -t stand/insults_en .
   ```
4. Run Docker image:
   ```
   sudo docker run -p <host_port>:6006 -v /path/to/host/vol/map/dir:/logs stand/insults_en
   ```
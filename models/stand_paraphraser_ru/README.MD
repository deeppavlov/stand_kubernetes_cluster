# Demo stand. Model: paraphraser_ru

## Installation and start
1. Go to the `stand_kubernetes_cluster/models/stand_paraphraser_ru` directory
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
        python3.6 -m deeppavlov download deeppavlov/configs/classifiers/paraphraser_bert.json
        ```
    5. Install model dependencies:
        ```
        python3.6 -m deeppavlov install deeppavlov/configs/classifiers/paraphraser_bert.json
        ```
    6. Return to the `stand_paraphraser_ru` dir:
        ```
        cd ..
        ```
5. Specify model endpoint host (`host`) and port (`port`) in `common_defaults` or corresponding model section of `DeepPavlov/utils/server_utils/server_config.json`
6. Specify virtual environment path (if necessary) in `run_paraphraser_ru.sh`
7. Run model:
    ```
    ./run_paraphraser_ru.sh
    ```

## Building and running with Docker:
1. If necessary, build base docker_cuda and docker_deeppavlov images for CUDA 9.0 from:

   https://github.com/deepmipt/stand_docker_base
  
2. Go to the `stand_kubernetes_cluster/models/stand_paraphraser_ru` directory

3. Build Docker image:
   ```
   sudo docker build -t stand/paraphraser_ru .
   ```
4. Run Docker image:
   ```
   sudo docker run -p <host_port>:5000 -v /path/to/host/vol/map/dir:/logs stand/paraphraser_ru
   ```

# License

Apache 2.0 - licensed.
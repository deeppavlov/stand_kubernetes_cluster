# Demo stand. Model: 

## Installation and start
1. Go to the `stand_kubernetes_cluster/models/demo_squad_ru_confidence` directory
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
    2. Install the requirements:
        ```
        python setup.py develop
        ```
    3. Install `spacy` dependencies:
        ```
        pip install http://lnsigo.mipt.ru/export/en_core_web_sm-2.0.0.tar.gz
        python3.6 -m spacy link en_core_web_sm en --force
        ```
    4. Download NLTK data:
        ```
        $ python3
        >>> import nltk
        >>> nltk.download('punkt')
        >>> exit()
        ```
    5. Download model components:
        ```
        python3.6 -m deeppavlov.deep download deeppavlov/configs/squad/squad_ru.json
        ```
    6. Return to the `demo_squad_ru_confidence` dir:
        ```
        cd ..
        ```
5. Specify model endpoint host (`host`) and port (`port`) in `common_defaults` or corresponding model section of `DeepPavlov/utils/server_utils/server_config.json`
6. Specify `CUDA_VISIBLE_DEVICES` and virtual environment path (if necessary) in `run_squad_ru_confidence.sh`
7. Run model:
    ```
    ./run_squad_ru_confidence.sh
    ```

## Building and running with Docker:
1. If necessary, build base docker_cuda and docker_deeppavlov images for CUDA 8.0 from:

   https://github.com/deepmipt/stand_docker_base
  
2. Go to the `stand_kubernetes_cluster/models/demo_squad_ru_confidence` directory

3. Build Docker image:
   ```
   sudo docker build -t demo/squad_ru_confidence .
   ```
4. Run Docker image:
   ```
   sudo docker run -p <host_port>:6019 --runtime=nvidia --device=/dev/nvidia<gpu_unit_int_id> -v /path/to/host/vol/map/dir:/logs demo/squad_ru_confidence
   ```
# Demo stand. Model: bhge_odqa_en

## Installation and start
This model is based upon obsolete DeepPavlov version and requires custom installation. Please, refer `Dockerfile` for installation sequence. Don't forget about setting `CUDA_VISIBLE_DEVICES` environment variable or the same named param in run file.   

## Building and running with Docker:
1. If necessary, build base docker_cuda and docker_deeppavlov images for CUDA 9.0 from:

   https://github.com/deepmipt/stand_docker_base
  
2. Go to the `stand_kubernetes_cluster/models/demo_bhge_odqa_en` directory

3. Build Docker image:
   ```
   sudo docker build -t demo/bhge_odqa_en .
   ```
4. Run Docker image:
   ```
   sudo docker run -p <host_port>:6022 --runtime=nvidia --device=/dev/nvidia<gpu_unit_int_id> -v /path/to/host/vol/map/dir:/logs demo/bhge_odqa_en
   ```
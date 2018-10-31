## Building and running with Docker:
1. If necessary, build base docker_cuda and docker_deeppavlov images for CUDA 9.0 from:

   https://github.com/deepmipt/stand_docker_base
  
2. Go to the `stand_kubernetes_cluster/models/demo_bhge_retrieval_lists_ensemble` directory

3. Build Docker image:
   ```
   sudo docker build -t demo/bhge_retrieval_lists_ensemble .
   ```
4. Run Docker image:
   ```
   sudo docker run -p <host_port>:6024 -v /path/to/host/vol/map/dir:/logs demo/bhge_retrieval_lists_ensemble
   ```

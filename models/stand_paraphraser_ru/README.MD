# Demo stand. Model: Paraphraser (Russian, ParlAI based)

## Building and running with Docker:
1. If necessary, build base docker_cuda image for CUDA 8.0 from:

   https://github.com/deepmipt/stand_docker_base
  
2. Go to the `stand_kubernetes_cluster/models/stand_paraphraser_ru` directory

3. Build Docker image:
   ```
   sudo docker build -t stand/paraphraser_ru .
   ```
4. Run Docker image:
   ```
   sudo docker run -p <host_port>:6003 -v /path/to/host/vol/map/dir:/logs stand/paraphraser_ru
   ```
# Demo stand. Model: ranking_en

## Building and running with Docker:
1. If necessary, build base docker_cuda and docker_deeppavlov images for CUDA 9.0 from:

   https://github.com/deepmipt/stand_docker_base
  
2. Go to the `stand_kubernetes_cluster/models/stand_ranking_en` directory

3. Build Docker image:
   ```
   sudo docker build -t stand/ranking_en .
   ```
4. Run Docker image:
   ```
   sudo docker run -p <host_port>:5000 -v /path/to/host/vol/map/dir:/logs stand/ranking_en
   ```

# License

Apache 2.0 - licensed.
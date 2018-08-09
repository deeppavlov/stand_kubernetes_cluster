## Building and running with Docker:
1. If necessary, build base docker_cuda and docker_deeppavlov images for CUDA 9.0 from:

   https://github.com/deepmipt/stand_docker_base
  
2. Go to the `stand_kubernetes_cluster/models/demo_sber_faq` directory

3. Build Docker image:
   ```
   sudo docker build -t demo/sber_faq .
   ```
4. Run Docker image:
   ```
   sudo docker run -e "MS_APP_ID=<ms_app_id>" -e "MS_APP_SECRET=<ms_app_secret>" -p <host_port>:6040 -v /path/to/host/vol/map/dir:/logs demo/sber_faq
   ```
# Demo stand. Kubernetes cluster

## Components deployment

Demo stand Kubernetes cluster is based on following components:

1. **Docker**
2. Kubernetes packeges: **kubeadm**, **kubelet**, **kubectl**
3. **Docker registry** 

Components 1. and 2. should be deployed both on master and each slave node.

### Docker installation
1. Run:
    ```
    sudo apt-get update
    sudo apt-get install -y docker.io
    ```
    
### Kubernetes installation
1. Run:
    ```
    sudo apt-get update && apt-get install -y apt-transport-https
    curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
    sudo cat <<EOF >/etc/apt/sources.list.d/kubernetes.list
    deb http://apt.kubernetes.io/ kubernetes-xenial main
    EOF
    sudo apt-get update
    sudo apt-get install -y kubelet kubeadm kubectl
    ```
2. Kubernetes can't operate with swap enabled on host machine. Disable swap on master and each slave node:
    ```
    sudo swapoff -a
    ```

Reference resources:
1. Kubernetes docs, kubeadm installation: https://kubernetes.io/docs/setup/independent/install-kubeadm/
 
### Docker registry deployment
For now plain insecure HTTP registry is assumed to be used. 

1. If required, install Docker on Docker registry host machine:
    ```
    sudo apt-get update
    sudo apt-get install -y docker.io
    ```
2. Deploy Docker registry:
    ```
    docker run -d -p <registry port, default=5000>:5000 --restart=always --name registry registry:2
    ```
3. To enable insecure access to registry, follow these steps on master and each slave node (as well as each host that wants to access the regestry):
    
    3.1 Edit or create `/etc/docker/daemon.json` file with updating it with following contents:
    ```
    {
        "insecure-registries" : ["<registry domain or IP>:<registry port>"]
    }
    ```
    3.2 Restart Docker for the changes to take effect:
    ```
    sudo systemctl restart docker
    ```
    
Reference resources:
1. Docker docs, docker registry: https://docs.docker.com/registry/
2. Docker docs, insecure registry deployment: https://docs.docker.com/registry/insecure/
3. Docker docs, secure registry deployment: https://docs.docker.com/registry/deploying/


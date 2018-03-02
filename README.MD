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
For now plain insecure HTTP registry is be used. 

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
    
    1. Edit or create `/etc/docker/daemon.json` file with updating it with following contents:
    ```
    {
        "insecure-registries" : ["<registry domain or IP>:<registry port>"]
    }
    ```
    2. Restart Docker for the changes to take effect:
    ```
    sudo systemctl restart docker
    ```
    
Reference resources:
1. Docker docs, docker registry: https://docs.docker.com/registry/
2. Docker docs, insecure registry deployment: https://docs.docker.com/registry/insecure/
3. Docker docs, secure registry deployment: https://docs.docker.com/registry/deploying/

## Cluster deployment
From here all commands are assumed to be executed on the master node if other is not stated.

For now **Kube-router** pod-network is used.

1. Clone the repo and `cd` to project root:
    ```
    https://github.com/deepmipt/stand_kubernetes_cluster.git
    cd stand_kubernetes_cluster
    ```
2. Make **cubectl** work for non-root users:
    ```
    mkdir -p $HOME/.kube
    sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
    sudo chown $(id -u):$(id -g) $HOME/.kube/config
    export KUBECONFIG=$HOME/admin.conf   
    ```
    It can be also useful to add `KUBECONFIG=$HOME/admin.conf` to the `.bashrc` file.
     
3. Initiate master node with **kubeadm**:
    ```
    sudo sysctl net.bridge.bridge-nf-call-iptables=1
    sudo kubeadm init --pod-network-cidr=<pod network IP range, we use 192.168.0.0/16>
    ```
   If succeeded, `kubeadm join` will be printed at the end of init process:
    ```
    kubeadm join --token <token> <master-ip>:<master-port> --discovery-token-ca-cert-hash sha256:<hash>
    ```
    Save it to run while nodes joining.
    
4. Install Kube-router pod network to the master node:
    ```
    kubectl apply -f https://raw.githubusercontent.com/cloudnativelabs/kube-router/master/daemonset/kubeadm-kuberouter.yaml
    ```
5. To add new nodes to the cluster run on each machine:
    ```
    sudo kubeadm join --token <token> <master-ip>:<master-port> --discovery-token-ca-cert-hash sha256:<hash>
    ```
6. To tear down the node:
    1. Run on master:
        ```
        kubectl drain <node name> --delete-local-data --force --ignore-daemonsets
        kubectl delete node <node name>
        ```
    2. Run on node:
        ```
        sudo kubeadm reset
        ```
7. To dismantle cluster run on master:
    ```
    sudo kubeadm reset
    ```

Reference resources:
1. Kubernetes docs, crating cluster: https://kubernetes.io/docs/setup/independent/create-cluster-kubeadm/
2. GitHub, Kube-router deployment: https://github.com/cloudnativelabs/kube-router/blob/master/Documentation/kubeadm.md
3. Habrahabr, Kubernetes deplyment: https://habrahabr.ru/company/southbridge/blog/334846/

## Docker images deployment
Make Docker images and push them to registry. Here is the basic reference:
1. Docker docs, push/pull operations: https://docs.docker.com/registry/
2. Docker docs, image naming: https://docs.docker.com/registry/introduction/#understanding-image-naming

## Cluster payload deployment
For now stand cluster solution presumes following deployment of stand skills and services (payload):
```
Image => Deployment => Pod => Service
```

**Pods** are defined in **deployments** .yaml defenitions as well as initiated and stopped also by **deployments**.
So far, payload deployment includes following steps:
1. Building of **image** and pushing it to the registry
2. **Deployment** definition and launching
3. **Service** definition and launching

For **deployments** and **services** definition you can reference:
1. Kubernetes docs, deployments: https://kubernetes.io/docs/concepts/workloads/controllers/deployment/
2. Kubernetes docs, deployments API:
3. Kubernetes docs, services: https://kubernetes.io/docs/concepts/services-networking/service/
4. Kubernetes docs, services API:
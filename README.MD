# Demo stand. Kubernetes cluster

## Components deployment

Demo stand Kubernetes cluster is based on following components:

1. **Docker** with **NVIDIA Container Runtime for Docker**
2. Kubernetes packages: **kubeadm**, **kubelet**, **kubectl**, **kubernetes-cni**
3. **Docker registry**

Docker and all Kubernetes packages should be deployed both on master and each worker node.
NVIDIA Container Runtime for Docker should be deployed on each worker node with GPUs.

This docs are tested for following versions of demo stand components:
* Docker `19.03.1`
* Kubelet `v1.15.3`
* Kubeadm: `v1.15.3`

### Docker installation
1. Install Docker:
    ```
    sudo apt-get update
    sudo apt-get install docker-ce
    ```

2. Install NVIDIA Container Runtime for Docker:

    1. Add package repositories:
        ```
        curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | \
        sudo apt-key add -

        distribution=$(. /etc/os-release;echo $ID$VERSION_ID)

        curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
        sudo tee /etc/apt/sources.list.d/nvidia-docker.list

        sudo apt-get update
        ```
    2. Install nvidia-docker2 and reload the Docker daemon configuration:
        ```
        sudo apt-get install -y nvidia-docker2
        sudo pkill -SIGHUP dockerd
        ```

Reference resources:
1. Docker installation: https://docs.docker.com/install/linux/docker-ce/ubuntu/#install-docker-ce-1
2. NVIDIA Docker installation: https://github.com/NVIDIA/nvidia-docker

### Kubernetes installation
1. Kubernetes can't operate with swap enabled on host machine. Disable swap on master and each slave node:
    ```
    sudo swapoff -a
    ```
2. Install Kubernetes:

    1. Add package repositories:
        ```
        sudo apt-get update && sudo apt-get install -y apt-transport-https
        curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
        echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee -a /etc/apt/sources.list.d/kubernetes.list
        ```
    2. Install Kubernetes packages:
        ```
        sudo apt-get update
        sudo apt-get install -y kubelet kubeadm kubectl kubernetes-cni
        ```

Reference resources:
1. Kubernetes docs, kubeadm installation: https://kubernetes.io/docs/setup/independent/install-kubeadm/

### Docker registry deployment
For now plain insecure HTTP registry is used.

1. If required, install Docker on Docker registry host machine:
    ```
    sudo apt-get update
    sudo apt-get install docker-ce
    ```
2. Deploy Docker registry:
    ```
    docker run -d -p <registry port, default=5000>:5000 --restart=always --name registry registry:2
    ```
3. To enable insecure access to registry, follow these steps on master and each slave node (as well as each host that wants to access the registry):

    1. Edit or create `/etc/docker/daemon.json` file with updating it with following contents:
        ```
        {
            "insecure-registries" : ["<registry domain or IP>:<registry port>"]
        }
        ```
    2. Restart Docker for the changes to take effect:
        ```
        sudo systemctl daemon-reload
        sudo systemctl restart docker
        ```

Reference resources:
1. Docker docs, docker registry: https://docs.docker.com/registry/
2. Docker docs, insecure registry deployment: https://docs.docker.com/registry/insecure/
3. Docker docs, secure registry deployment: https://docs.docker.com/registry/deploying/

## Cluster deployment

### Master node deployment:
All commands are assumed to be executed on the master node. We use **Flannel** as pod network driver.

1. Clone the repo and `cd` to the `kube_scripts` dir:
    ```
    git clone https://github.com/deepmipt/stand_kubernetes_cluster.git
    cd stand_kubernetes_cluster/tools/kube_scripts
    ```
2. Initiate cluster master node:
    ```
    sudo sysctl net.bridge.bridge-nf-call-iptables=1
    sudo kubeadm init --pod-network-cidr=10.244.0.0/16
    ```
   If succeeded, `kubeadm join` will be printed at the end of init process:
    ```
    kubeadm join --token <token> <master-ip>:<master-port> --discovery-token-ca-cert-hash sha256:<hash>
    ```
    Save it to run while nodes joining.
3. Make **cubectl** work for your user:
    ```
    mkdir -p $HOME/.kube
    sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
    sudo chown $(id -u):$(id -g) $HOME/.kube/config
    ```
4. Deploy Flannel network driver:
    ```
    kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/2140ac876ef134e0ed5af15c65e414cf26827915/Documentation/kube-flannel.yml
    ```
5. Or you can simply run `kubeadm_init_flannel.sh` script from `stand_kubernetes_cluster/tools/kube_scripts` instead of steps 2-4:
    ```
    sudo sh kubeadm_init_flannel.sh
    ```
6. Deploy NVIDIA device plugin for Kubernetes with running `deploy_nvidia_plugin.sh` script from `stand_kubernetes_cluster/tools/kube_scripts`:
    ```
    sudo sh deploy_nvidia_plugin.sh
    ```

Reference resources:
1. NVIDIA device plugin for Kubernetes: https://github.com/NVIDIA/k8s-device-plugin

### Worker nodes deployment:
1. To add worker nodes to the cluster run with `--ignore-preflight-errors=all` option saved `kubeadm join` as sudo on each worker node and restart kubelet:
    ```
    sudo kubeadm join <master-ip>:<master-port> --token <token> --discovery-token-ca-cert-hash sha256:<hash>
    ```

### Cluster operations:
1. Check all system pods are running:
    ```
    kubectl get all --namespace=kube-system
    ```
2. List all nodes to check their availability:
    ```
    kubectl -n kube-system get nodes
    ```
3. To get `kubeadm join` run on master node:
    ```
    sudo kubeadm token create --print-join-command
    ```
4. To tear down the node:
    1. Run on master:
        ```
        kubectl drain <node name> --delete-local-data --force --ignore-daemonsets
        kubectl delete node <node name>
        ```
    2. Run on node `reset_node.sh` script from `stand_kubernetes_cluster/tools/kube_scripts`:
        ```
        sudo sh reset_node.sh
        ```
5. To totally dismantle cluster first tear down all worker nodes then tear down master node as written above.

Reference resources:
1. Kubernetes docs, creating cluster: https://kubernetes.io/docs/setup/independent/create-cluster-kubeadm/
2. GitHub, Kube-router deployment: https://github.com/cloudnativelabs/kube-router/blob/master/Documentation/kubeadm.md
3. Habrahabr, Kubernetes deployment: https://habrahabr.ru/company/southbridge/blog/334846/
4. Habrahabr, Kubernetes deployment: https://habr.com/post/348688/

## Docker images deployment
Build Docker images and push them to registry. Here is the basic reference:
1. Docker docs, push/pull operations: https://docs.docker.com/registry/
2. Docker docs, image naming: https://docs.docker.com/registry/introduction/#understanding-image-naming

## Cluster payload deployment and management

### Common stand components deployment
For now demo stand solution requires some Kubernetes objects like **Namespaces**, **PersistentVolumes** and so on to be created before stand skills and services (payload) are deployed.
Yaml configs for these objects are located in `stand_kubernetes_cluster/kuber_configs/common`.

To create these objects:

1. `cd` to `stand_kubernetes_cluster/kuber_configs/common`
2. We run demo stand payload in `stand-demo` **Namespace**. To create in run:
    ```
    kubectl create -f namespaces/stand_demo_ns.yaml
    ```
3. Create hostpath volumes for stand component and logs:
    ```
    kubectl create -f volumes/logs_hostpath
    kubectl create -f volumes/components_hostpath
    kubectl create -f volumes/db_hostpath
    kubectl create -f volumes/rb_hostpath
    kubectl create -f volumes/tfhub_hostpath
    ```

For Kubernetes storaging and **Volumes** you can reference:
1. Kubernetes docs, **Volumes**: https://kubernetes.io/docs/concepts/storage/volumes/
2. Kubernetes docs, **PersistentVolumes** manual: https://kubernetes.io/docs/tasks/configure-pod-container/configure-persistent-volume-storage/

### Stand payload deployment
So far, payload deployment includes following steps:
1. Building of **Docker image** and pushing it to the registry
2. **Deployment** definition and launching
3. **Service** definition and launching

Yaml configs for payload **Deployments** and **Services** are located in `stand_kubernetes_cluster/kuber_configs/models`.

To deploy stand payload:

1. Push  payload **Docker image** to the cluster registry (Russian NER example):
    ```
    sudo docker push kubeadm.ipavlov.mipt.ru:5000/stand/ner_ru
    ```
2. `cd` to `stand_kubernetes_cluster/kuber_configs/models`
3. Create payload **Deployment** (Russian NER example):
    ```
    kubectl create -f stand_ner_ru/stand_ner_ru_dp.yaml
    ```
4. Create payload **Service** (Russian NER example):
    ```
    kubectl create -f stand_ner_ru/stand_ner_ru_lb.yaml
    ```
5. Or you can simply run following instead of steps 3-4:
    ```
    kubectl create -f stand_ner_ru
    ```

For **Deployments** and **Services** definition you can reference:
1. Kubernetes docs, deployments: https://kubernetes.io/docs/concepts/workloads/controllers/deployment/
2. Kubernetes docs, deployments API: https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.9/#deployment-v1-apps
3. Kubernetes docs, services: https://kubernetes.io/docs/concepts/services-networking/service/
4. Kubernetes docs, services API: https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.9/#service-v1-core

### Logs and metrics deployment

- Create `monitoring` namespace
  ```
  kubectl create -f kuber_configs/common/namespaces/monitoring_ns.yaml
  ```
- Create hostpath volumes
  ```
  kubectl create -f kuber_configs/common/volumes/loki_hostpath
  kubectl create -f kuber_configs/common/volumes/prometheus_hostpath
  kubectl create -f kuber_configs/common/volumes/grafana_hostpath
  ```

- Make sure you have Helm [installed](https://helm.sh/docs/intro/install/)
- Add helm repos:
  ```
  helm repo add grafana https://grafana.github.io/helm-charts
  helm repo add loki https://grafana.github.io/loki/charts
  helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
  helm repo add stable https://kubernetes-charts.storage.googleapis.com/
  ```
- Change adminPassword and service.externalIPs keys in `kuber_configs/common/charts/grafana/values.yml`
- Install:
  ```
  helm upgrade --install loki --namespace=monitoring loki/loki-stack -f kuber_configs/common/charts/loki/values.yml
  helm upgrade --install prometheus --namespace=monitoring prometheus-community/prometheus -f kuber_configs/common/charts/prometheus/values.yml
  helm upgrade --install grafana --namespace=monitoring grafana/grafana -f kuber_configs/common/charts/grafana/values.yml
  ```
- Make sure that grafana web UI is available service.externalIPs address

### Stand payload operations

We run demo stand payload in `stand-demo` **Namespace**. So we should use `-n stand-demo` flag in all `kubectl` operations with demo stand objects.

Demo stand objects listing:
1. List **Services**:
    ```
    kubectl -n stand-demo get services
    ```
2. List **Deployments**:
    ```
    kubectl -n stand-demo get deployments
    ```
3. List **Pods**:
    ```
    kubectl -n stand-demo get pods
    ```

Get detailed information about object:
1. **Service**:
    ```
    kubectl -n stand-demo describe service <service_name>
    ```
2. **Deployment**:
    ```
    kubectl -n stand-demo describe deployment <deployment_name>
    ```
3. **Pod**:
    ```
    kubectl -n stand-demo describe pod <pod_name>
    ```

Delete object:
1. **Service**:
    ```
    kubectl -n stand-demo delete service <service_name>
    ```
    Or:
    ```
    kubectl delete -f <service_config.yaml>
    ```
2. **Deployment**:
    ```
    kubectl -n stand-demo delete deployment <deployment_name>
    ```
    Or:
    ```
    kubectl delete -f <deployment_config.yaml>
    ```
3. **Pod** (new pod will be instantly created instead of deleted):
    ```
    kubectl -n stand-demo delete pod <pod_name>
    ```


## DeepPavlov DREAM

Change .env and pipeline_conf.json services hosts to 10.11.1.251, add necessary secrets for news, games, weather,
db host, port, name. Add FLASK_APP=server.

DB name - dream-demo
HOST - 10.11.1.251
PORT - 10042

Create secrets

```commandline
kubectl -n stand-demo delete secret dream-secret
kubectl -n stand-demo create secret generic dream-secret --from-env-file=.env
```

Generate models config
```commandline
python tools/cluster_deployer/dream_generator.py
```

## DREAM GOALS

docker-compose -f docker-compose.yml -f assistant_dists/dream/docker-compose.override.yml -p goals build human-goals-detector dff-share-problems-skill dff-book-recommendation-skill dff-series-recommendation-skill dff-get-book-information-skill dff-test-bot-skill dff-travel-recommendation-skill dff-have-fun-skill goals-tracker agent
db name dream-goals
Add TG_TOKEN=forth bot token
Dockerfile agent hash c2bd03b970b7016f24e48db4d0c10a1d7ca4b6f8

# EE

ee-secret delete and create
don't forget to add FLASK_APP=server variable to .env

## DREAM TG

dream-tg-secret 

# License

Apache 2.0 - licensed.

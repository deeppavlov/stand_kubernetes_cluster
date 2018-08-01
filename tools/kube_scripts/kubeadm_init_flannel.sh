#!/bin/bash
kubeadm init --pod-network-cidr=10.244.0.0/16 && \

mkdir -p $HOME/.kube && \
cp /etc/kubernetes/admin.conf $HOME/.kube/config && \
chown $(id -u):$(id -g) $HOME/.kube/config && \

mkdir -p ~kube/.kube && \
cp /etc/kubernetes/admin.conf ~kube/.kube/config && \
chown kube ~kube/.kube/config && \

kubectl create clusterrolebinding add-on-cluster-admin --clusterrole=cluster-admin --serviceaccount=kube-system:default && \
#kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml && \
kubectl apply -f flannel.yaml && \

kubectl -n kube-system get nodes

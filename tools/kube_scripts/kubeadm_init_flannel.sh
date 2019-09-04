#!/bin/bash
kubeadm init --pod-network-cidr=10.244.0.0/16 && \

mkdir -p $HOME/.kube && \
cp /etc/kubernetes/admin.conf $HOME/.kube/config && \
chown $(id -u):$(id -g) $HOME/.kube/config && \

mkdir -p ~kube/.kube && \
cp /etc/kubernetes/admin.conf ~kube/.kube/config && \
chown kube ~kube/.kube/config && \

kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/62e44c867a2846fefb68bd5f178daf4da3095ccb/Documentation/kube-flannel.yml && \

kubectl -n kube-system get nodes

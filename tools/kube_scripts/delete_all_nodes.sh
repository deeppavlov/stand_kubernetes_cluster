#!/bin/bash
kubectl drain gpu1 --delete-local-data --force --ignore-daemonsets && \
kubectl delete node gpu1 ; \

kubectl drain gpu9 --delete-local-data --force --ignore-daemonsets && \
kubectl delete node gpu9 ; \

kubectl drain kubeadm.ipavlov.mipt.ru --delete-local-data --force --ignore-daemonsets && \
kubectl delete node kubeadm.ipavlov.mipt.ru

#!/bin/bash
cp /etc/kubernetes/admin.conf ~kube/.kube/config && \
chown kube ~kube/.kube/config && \

cp /etc/kubernetes/admin.conf ~litinsky/.kube/config && \
chown litinsky ~litinsky/.kube/config

#!/bin/bash
kubeadm reset ; \
systemctl stop kubelet ; \
systemctl stop docker ; \
rm -rf /var/lib/cni/ ; \
rm -rf /var/lib/kubelet/* ; \
rm -rf /etc/cni/ ; \
#ifconfig cni0 down ; \
#ifconfig flannel.1 down ; \
#ifconfig docker0 down ; \
ip link delete docker0 ; \
ip link delete flannel.1 ; \
ip link delete cni0 ; \
ip link delete kube-bridge ; \
#iptables --flush ; \
#iptables -tnat --flush ; \
systemctl daemon-reload ; \
systemctl start docker ; \
systemctl start kubelet

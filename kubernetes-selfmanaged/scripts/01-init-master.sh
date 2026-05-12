#!/usr/bin/env bash
# Run on the MASTER node after Terraform finishes and cloud-init has installed
# kubeadm/kubelet/kubectl/containerd. Idempotent-ish; safe to re-read.
set -euo pipefail

POD_CIDR="192.168.0.0/16"   # Calico default
APISERVER_ADVERTISE_IP="${1:-}"

if [[ -z "$APISERVER_ADVERTISE_IP" ]]; then
  APISERVER_ADVERTISE_IP="$(hostname -I | awk '{print $1}')"
fi

echo "==> Initializing control plane on ${APISERVER_ADVERTISE_IP}"
sudo kubeadm init \
  --apiserver-advertise-address="${APISERVER_ADVERTISE_IP}" \
  --pod-network-cidr="${POD_CIDR}" \
  --cri-socket=unix:///run/containerd/containerd.sock

echo "==> Configuring kubectl for ${USER}"
mkdir -p "$HOME/.kube"
sudo cp -f /etc/kubernetes/admin.conf "$HOME/.kube/config"
sudo chown "$(id -u):$(id -g)" "$HOME/.kube/config"

echo "==> Installing Calico CNI"
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.27.3/manifests/calico.yaml

echo "==> Waiting for control-plane to become Ready"
for i in {1..30}; do
  if kubectl get nodes | grep -q " Ready "; then break; fi
  sleep 10
done

echo "==> Installing ingress-nginx controller (bare-metal manifest, NodePort)"
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.10.1/deploy/static/provider/baremetal/deploy.yaml

# Pin ingress controller's NodePort so the Azure NSG rule is predictable.
echo "==> Patching ingress-nginx service to fixed NodePort 30080 (HTTP)"
kubectl -n ingress-nginx patch svc ingress-nginx-controller \
  --type='json' \
  -p='[{"op":"replace","path":"/spec/ports/0/nodePort","value":30080}]' || true

echo
echo "==> Cluster up. Run this on the WORKER to join:"
echo "------------------------------------------------------------"
sudo kubeadm token create --print-join-command
echo "------------------------------------------------------------"
echo
echo "Master public IP   : $(curl -s ifconfig.me || echo 'unknown')"
echo "Ingress HTTP port  : 30080  (NodePort on every node)"

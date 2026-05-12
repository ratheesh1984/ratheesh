#!/usr/bin/env bash
# Run on the WORKER node. Pass the kubeadm join command (from master) as args
# OR export it via $JOIN_CMD. Examples:
#   sudo ./02-join-worker.sh kubeadm join 10.10.1.4:6443 --token ... --discovery-token-ca-cert-hash sha256:...
#   JOIN_CMD="kubeadm join ..." sudo -E ./02-join-worker.sh
set -euo pipefail

if [[ -n "${JOIN_CMD:-}" ]]; then
  CMD="$JOIN_CMD"
elif [[ $# -gt 0 ]]; then
  CMD="$*"
else
  echo "Usage: sudo $0 <full kubeadm join command>"
  echo "   or: JOIN_CMD='kubeadm join ...' sudo -E $0"
  exit 1
fi

# Make sure CRI socket is explicit so kubeadm picks containerd.
if [[ "$CMD" != *"--cri-socket"* ]]; then
  CMD="$CMD --cri-socket=unix:///run/containerd/containerd.sock"
fi

echo "==> Joining cluster:"
echo "    $CMD"
sudo $CMD

echo "==> Done. From the master, run: kubectl get nodes"

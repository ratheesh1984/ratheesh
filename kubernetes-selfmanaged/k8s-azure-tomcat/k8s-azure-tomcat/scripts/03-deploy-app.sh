#!/usr/bin/env bash
# Run on the MASTER (or anywhere with kubectl pointed at the cluster).
# Applies all manifests in order and waits for rollout.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST_DIR="${SCRIPT_DIR}/../kubernetes"

echo "==> Applying manifests from ${MANIFEST_DIR}"
kubectl apply -f "${MANIFEST_DIR}/01-namespace.yaml"
kubectl apply -f "${MANIFEST_DIR}/02-configmap.yaml"
kubectl apply -f "${MANIFEST_DIR}/03-deployment.yaml"
kubectl apply -f "${MANIFEST_DIR}/04-service.yaml"
kubectl apply -f "${MANIFEST_DIR}/05-ingress.yaml"

echo "==> Waiting for tomcat rollout"
kubectl -n tomcat-app rollout status deployment/tomcat-deployment --timeout=300s

echo "==> Resources in tomcat-app namespace:"
kubectl -n tomcat-app get all,ingress,configmap

echo
echo "==> Test from inside the cluster:"
echo "    kubectl -n tomcat-app run curltest --rm -it --image=curlimages/curl --restart=Never -- curl -s http://tomcat-service/"
echo
echo "==> Test from outside (after NSG allows 30080 — already covered by NodePort rule):"
WORKER_IP="$(kubectl get node -l '!node-role.kubernetes.io/control-plane' -o jsonpath='{.items[0].status.addresses[?(@.type=="ExternalIP")].address}' 2>/dev/null || true)"
if [[ -z "$WORKER_IP" ]]; then
  echo "    curl http://<any-node-public-ip>:30080/"
else
  echo "    curl http://${WORKER_IP}:30080/"
fi

#!/usr/bin/env bash
# Deploy Gateway API resources with NGINX Gateway Fabric controller
# Run on the MASTER (or anywhere with kubectl pointed at the cluster)
# This is an optional step after 03-deploy-app.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST_DIR="${SCRIPT_DIR}/../kubernetes"

echo "==> Installing Gateway API CRDs (standard channel)"
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.1.0/standard-install.yaml

echo "==> Installing NGINX Gateway Fabric"
kubectl apply -f https://raw.githubusercontent.com/nginxinc/nginx-gateway-fabric/v1.4.0/deploy/default/deploy.yaml

echo "==> Waiting for nginx-gateway controller to be ready"
kubectl -n nginx-gateway wait --for=condition=Ready pod -l app.kubernetes.io/name=nginx-gateway-fabric --timeout=300s 2>/dev/null || true

echo "==> Applying Gateway API manifests"
kubectl apply -f "${MANIFEST_DIR}/06-gatewayclass.yaml"
kubectl apply -f "${MANIFEST_DIR}/07-gateway.yaml"
kubectl apply -f "${MANIFEST_DIR}/08-httproute.yaml"

echo "==> Waiting for Gateway to be ready"
kubectl -n tomcat-app wait --for=condition=Programmed gateway/tomcat-gateway --timeout=300s 2>/dev/null || true

echo "==> Gateway API Resources:"
kubectl get gatewayclasses
kubectl -n tomcat-app get gateways,httproutes

echo
echo "==> Checking Gateway status and assigned IP/Port:"
kubectl -n tomcat-app describe gateway tomcat-gateway

echo
echo "==> NGINX Gateway Fabric service (external IP):"
kubectl -n nginx-gateway get svc

echo
echo "==> Test the Gateway API route (from inside the cluster):"
echo "    kubectl -n tomcat-app run curltest --rm -it --image=curlimages/curl --restart=Never -- curl -s http://tomcat-service/"

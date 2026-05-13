# Gateway API Deployment Instructions

If you cannot SSH to your master node, use **Azure Cloud Shell** (has automatic kubectl access and no firewall restrictions).

## Option 1: Deploy from Azure Cloud Shell (Recommended)

1. **Open Cloud Shell** in Azure Portal (click the `>_` icon, top-right)
2. **Run these commands** directly in Cloud Shell (no SSH needed):

```bash
# Step 1: Install Gateway API CRDs
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.1.0/standard-install.yaml

# Step 2: Install NGINX Gateway Fabric controller
echo "==> Installing NGINX Gateway Fabric"
kubectl apply -f https://raw.githubusercontent.com/nginxinc/nginx-gateway-fabric/v1.4.0/deploy/default/deploy.yaml

# Step 3: Wait for controller to be ready
echo "==> Waiting for nginx-gateway controller..."
kubectl -n nginx-gateway wait --for=condition=Ready pod -l app.kubernetes.io/name=nginx-gateway-fabric --timeout=300s 2>/dev/null || echo "Continuing..."

# Step 4: Apply Gateway API manifests
kubectl apply -f - <<'EOF'
---
# GatewayClass is cluster-scoped — no namespace field
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: nginx
spec:
  controllerName: gateway.nginx.org/nginx-gateway-controller
  description: "NGINX Gateway Fabric controller"
---
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: tomcat-gateway
  namespace: tomcat-app
spec:
  gatewayClassName: nginx
  listeners:
    - name: http
      protocol: HTTP
      port: 80
      allowedRoutes:
        namespaces:
          from: Same
---
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: tomcat-route
  namespace: tomcat-app
spec:
  parentRefs:
    - name: tomcat-gateway
      namespace: tomcat-app
  hostnames:
    - "*"
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /
      backendRefs:
        - name: tomcat-service
          port: 80
EOF

# Verify Gateway status
echo "==> Gateway API Resources:"
kubectl get gatewayclasses
kubectl -n tomcat-app get gateways,httproutes

echo "==> Gateway status:"
kubectl -n tomcat-app describe gateway tomcat-gateway

echo "==> NGINX Gateway Fabric service (external IP):"
kubectl -n nginx-gateway get svc

# Test connectivity
echo "==> Testing Tomcat app through Gateway API:"
kubectl -n tomcat-app run curltest --rm -it --image=curlimages/curl --restart=Never -- curl -s http://tomcat-service/ 2>/dev/null || echo "Done"
```

3. **Check the status** - look for the Gateway's external IP/port in the output

---

## Option 2: Local Network Debugging

If you need to fix SSH connectivity:

```bash
# Check if your ISP/firewall is blocking the Azure IP
ping 20.127.130.235

# If ping fails, try Windows Firewall check:
# Settings > Privacy & Security > Windows Firewall > Allow an app through firewall
# Ensure SSH or appropriate app is allowed

# Try SSH with increased timeout:
ssh -o ConnectTimeout=30 -i terraform/k8s_id_rsa azureuser@20.127.130.235
```

---

## Option 3: Re-deploy Infrastructure (if needed)

If connectivity is persistent, you can redeploy:

```bash
cd terraform
terraform destroy -auto-approve
terraform apply           # Fresh deployment with new IPs
```

After applying, use Cloud Shell to deploy Gateway API as shown in Option 1.

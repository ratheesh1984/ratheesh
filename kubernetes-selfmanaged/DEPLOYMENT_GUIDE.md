# Kubernetes Self-Managed Cluster on Azure — Deployment Guide

This document consolidates every command used to build and troubleshoot this cluster,
with an explanation of what each command does and why it was needed.

---

## Architecture

```
Internet
   │
   ▼
20.127.130.235:30080  (Master public IP, Azure NSG opens 30000–32767)
   │
   ▼  NodePort → DNAT (kube-proxy nftables)
ingress-nginx pod  (on k8s-master, 192.168.235.196)
   │
   ▼  Calico VXLAN (UDP 4789, cross-node overlay)
tomcat pods × 2   (on k8s-worker, 192.168.254.132 / .133)

Nodes
  k8s-master   10.10.1.5  (public: 20.127.130.235)
  k8s-worker   10.10.1.4  (private only)
```

---

## Step 1 — Provision Azure VMs (Terraform)

```bash
cd terraform
terraform init
terraform apply
```

**Why:** Creates the Azure resource group, VNet, subnet, NSG, two Ubuntu 22.04 VMs
(master + worker), public IPs, NICs, and generates the SSH key pair `k8s_id_rsa`.
Cloud-init pre-installs `containerd`, `kubeadm`, `kubelet`, and `kubectl` on both VMs
so the bootstrap scripts can run immediately after the VMs are up.

---

## Step 2 — Copy the master init script to the master VM

```bash
scp -i terraform/k8s_id_rsa scripts/01-init-master.sh azureuser@20.127.130.235:~
```

**Why:** `scp` (Secure Copy) transfers a local file over SSH to the remote VM.
The script lives on your laptop; it needs to be on the master before it can be executed there.

---

## Step 3 — Make the script executable

```bash
# run remotely via SSH:
ssh -i terraform/k8s_id_rsa azureuser@20.127.130.235 "chmod +x ~/01-init-master.sh"
```

**Why:** Files copied with `scp` do not carry their execute permission bit.
`chmod +x` sets the executable bit so the shell can run the script directly (`./script.sh`).

---

## Step 4 — Initialise the Kubernetes control plane

```bash
ssh -i terraform/k8s_id_rsa azureuser@20.127.130.235 "~/01-init-master.sh 10.10.1.5"
```

**Why:** Runs `01-init-master.sh` on the master with the master's **private** IP as the
argument. Internally the script does:

| Sub-command | Purpose |
|---|---|
| `kubeadm init --apiserver-advertise-address=10.10.1.5 --pod-network-cidr=192.168.0.0/16` | Bootstraps the control plane (API server, etcd, scheduler, controller-manager) and sets the pod IP range for Calico |
| `mkdir ~/.kube && cp /etc/kubernetes/admin.conf ~/.kube/config` | Copies the cluster credentials so `kubectl` works as `azureuser` without `sudo` |
| `kubectl apply -f calico.yaml` | Installs the Calico CNI plugin so pods on different nodes can talk to each other |
| `kubectl apply -f ingress-nginx baremetal deploy.yaml` | Installs the NGINX ingress controller as a NodePort service |
| `kubectl patch svc ingress-nginx-controller --nodePort 30080` | Pins the NodePort to a known value (30080) so the Azure NSG rule is predictable |
| `kubeadm token create --print-join-command` | Prints the one-time join command for worker nodes |

---

## Step 5 — Join the worker node

```bash
# Copy the SSH key to the master so it can SSH into the worker
scp -i terraform/k8s_id_rsa terraform/k8s_id_rsa azureuser@20.127.130.235:~/.ssh/worker_key

# From the master, SSH into the worker and run the join command
ssh -i terraform/k8s_id_rsa azureuser@20.127.130.235 \
  "chmod 600 ~/.ssh/worker_key && \
   ssh -i ~/.ssh/worker_key -o StrictHostKeyChecking=no azureuser@10.10.1.4 \
   'sudo kubeadm join 10.10.1.5:6443 \
     --token o46kva.6poqbku9mjrus24z \
     --discovery-token-ca-cert-hash sha256:9181b60c6fe19f7f50cbfb335855be58e33e24fd0a157ae2f45f64f708006b49'"
```

**Why:** The worker only has a private IP so it is not directly reachable from the
internet. We use the master as a **jump host** — SSH into master first, then SSH from
master into worker. `kubeadm join` registers the worker with the API server using a
short-lived bootstrap token and TLS certificate hash for security.

**Verify:**
```bash
ssh -i terraform/k8s_id_rsa azureuser@20.127.130.235 "kubectl get nodes"
# Expected: both k8s-master and k8s-worker show STATUS=Ready
```

---

## Step 6 — Deploy the Tomcat app

```bash
# Copy manifests and deploy script to master
scp -i terraform/k8s_id_rsa -r scripts kubernetes azureuser@20.127.130.235:~

# Run the deploy script
ssh -i terraform/k8s_id_rsa azureuser@20.127.130.235 \
  "chmod +x ~/scripts/03-deploy-app.sh && ~/scripts/03-deploy-app.sh"
```

**Why:** `03-deploy-app.sh` runs `kubectl apply` on five manifests in order:

| Manifest | What it creates |
|---|---|
| `01-namespace.yaml` | Namespace `tomcat-app` — logical isolation for all app resources |
| `02-configmap.yaml` | ConfigMap with a sample JSP page mounted into the Tomcat container |
| `03-deployment.yaml` | 2-replica Deployment running `tomcat:9-jdk17` |
| `04-service.yaml` | ClusterIP Service on port 80 → targetPort 8080 (Tomcat's default) |
| `05-ingress.yaml` | Ingress rule: all paths (`/`) → `tomcat-service:80` via `ingressClassName: nginx` |

---

## Step 7 — Deploy Gateway API (Optional)

Gateway API is the successor to Ingress. It offers better role separation, richer routing,
and cross-namespace support. Both Ingress and Gateway API can run at the same time.

```bash
# Copy manifests and script to master (if not already there)
scp -i terraform/k8s_id_rsa -r scripts kubernetes azureuser@20.127.130.235:~

# Run the Gateway API deploy script
ssh -i terraform/k8s_id_rsa azureuser@20.127.130.235 \
  "chmod +x ~/scripts/04-deploy-gateway-api.sh && ~/scripts/04-deploy-gateway-api.sh"
```

**What the script does:**

| Step | Command | Purpose |
|---|---|---|
| 1 | `kubectl apply -f standard-install.yaml` | Installs the Gateway API CRDs (GatewayClass, Gateway, HTTPRoute) |
| 2 | `kubectl apply -f nginx-gateway-fabric/deploy.yaml` | Installs NGINX Gateway Fabric controller in `nginx-gateway` namespace |
| 3 | `kubectl apply -f 06-gatewayclass.yaml` | Registers the NGINX controller as a `GatewayClass` (cluster-scoped) |
| 4 | `kubectl apply -f 07-gateway.yaml` | Creates the `Gateway` — the network entry point on port 80 |
| 5 | `kubectl apply -f 08-httproute.yaml` | Creates the `HTTPRoute` — routes all paths to `tomcat-service:80` |

**Verify:**
```bash
ssh -i terraform/k8s_id_rsa azureuser@20.127.130.235 \
  "kubectl get gatewayclasses && kubectl -n tomcat-app get gateways,httproutes"
```

**Test (from inside the cluster):**
```bash
kubectl -n tomcat-app run curltest --rm -it --image=curlimages/curl --restart=Never \
  -- curl -s http://tomcat-service/
```

---

## Troubleshooting — ingress webhook timeout

**Error:**
```
Internal error occurred: failed calling webhook "validate.nginx.ingress.kubernetes.io":
Post "https://ingress-nginx-controller-admission.svc:443/...": context deadline exceeded
```

**Fix:**
```bash
kubectl delete validatingwebhookconfiguration ingress-nginx-admission
kubectl apply -f ~/kubernetes/05-ingress.yaml
```

**Why:** The ingress-nginx admission webhook validates Ingress objects before they are
saved. During initial cluster setup the webhook service is not reachable yet (pod not
fully ready, or DNS not resolved), so the API server cannot call it and rejects the
Ingress. Deleting the `ValidatingWebhookConfiguration` removes the validation step so
the Ingress can be created. In production you would wait for the webhook to be healthy
instead of deleting it.

---

## Troubleshooting — app not reachable on port 30080

### Diagnosis commands used

```bash
# 1. Check if NodePort service is configured correctly
kubectl -n ingress-nginx get svc ingress-nginx-controller
# Expected: TYPE=NodePort, PORT(S)=80:30080/TCP

# 2. Check all pod locations
kubectl -n ingress-nginx get pod -o wide
kubectl -n tomcat-app get pod -o wide

# 3. Test from inside the master — is the port reachable locally?
curl -m 5 http://localhost:30080/
curl -m 5 http://10.10.1.5:30080/

# 4. Check nftables rules (kube-proxy uses nftables on Ubuntu 22.04)
sudo nft list ruleset | grep -B5 -A5 '30080'

# 5. Test each hop individually
curl -m 5 http://10.10.1.4:30080/        # worker NodePort — HTTP 200 ✓
curl -m 5 http://192.168.254.132:8080/   # tomcat pod direct — timed out ✗
```

---

### Fix 1 — Move ingress-nginx pod to the master node

**Root cause:** All pods (including ingress-nginx) scheduled to the worker. External
traffic arrives at the master's public IP. The master's NodePort DNAT rule forwards to
the worker pod, but the return path (SNAT/masquerade) was unreliable, causing timeouts.

**Fix:** Force the ingress-nginx pod to run on the master by adding a `nodeSelector`
and a toleration for the control-plane taint.

```bash
kubectl -n ingress-nginx patch deployment ingress-nginx-controller --patch \
  '{"spec":{"template":{"spec":{
    "tolerations":[{"key":"node-role.kubernetes.io/control-plane","operator":"Exists","effect":"NoSchedule"}],
    "nodeSelector":{"kubernetes.io/hostname":"k8s-master"}
  }}}}'

kubectl -n ingress-nginx rollout status deployment/ingress-nginx-controller
```

**Why `tolerations`:** The master has a taint `node-role.kubernetes.io/control-plane:NoSchedule`
which prevents normal pods from being scheduled on it. Adding a matching toleration
opts this pod out of that restriction.

**Why `nodeSelector`:** Tells the Kubernetes scheduler to place this pod only on the
node named `k8s-master`.

---

### Fix 2 — Switch Calico from IPIP to VXLAN

**Root cause:** Even with ingress-nginx on the master, the ingress pod could not reach
the tomcat pods on the worker. The ingress logs showed:
```
upstream timed out (110: Operation timed out) while connecting to upstream
http://192.168.254.133:8080/
```

Calico was using **IPIP encapsulation** (IP protocol 4) for cross-node pod traffic.
Azure NSGs **do not support IP protocol 4** — only TCP, UDP, and ICMP are allowed.
IPIP packets were silently dropped by Azure's network fabric.

**Fix:** Switch Calico to **VXLAN** (UDP port 4789), which Azure supports.

```bash
# 1. Patch the Calico IP pool to disable IPIP and enable VXLAN
kubectl patch ippool default-ipv4-ippool --type=merge \
  -p '{"spec":{"ipipMode":"Never","vxlanMode":"Always"}}'

# 2. Restart calico-node on all nodes to pick up the new mode
kubectl -n kube-system rollout restart daemonset/calico-node
kubectl -n kube-system rollout status daemonset/calico-node

# 3. Verify cross-node pod connectivity is restored
curl -m 5 http://192.168.254.132:8080/   # tomcat pod — HTTP 200 ✓
curl -m 5 http://10.10.1.5:30080/        # NodePort on master — HTTP 200 ✓
```

**IPIP vs VXLAN:**

| | IPIP | VXLAN |
|---|---|---|
| Encapsulation | IP-in-IP (protocol 4) | UDP (port 4789) |
| Azure support | No — blocked by NSG | Yes — standard UDP |
| Overhead | Lower | Slightly higher |
| Use when | On-prem / bare metal | Cloud (Azure, GCP, AWS) |

---

## Final verification

```bash
ssh -i terraform/k8s_id_rsa azureuser@20.127.130.235 "kubectl get nodes && kubectl -n tomcat-app get all,ingress"
```

Expected output:
```
NAME         STATUS   ROLES           AGE   VERSION
k8s-master   Ready    control-plane   ...   v1.29.15
k8s-worker   Ready    <none>          ...   v1.29.15

pod/tomcat-deployment-xxx   1/1   Running   ...
service/tomcat-service      ClusterIP   ...
deployment/tomcat-deployment  2/2   ...
ingress/tomcat-ingress      nginx   *   10.10.1.5   80
```

App URL: **http://20.127.130.235:30080/**

---

## Traffic flow (end-to-end)

```
Browser → 20.127.130.235:30080
  │
  │ Azure NSG: AllowNodePorts (30000–32767 TCP inbound) ✓
  ▼
kube-proxy nftables DNAT on k8s-master
  (KUBE-NODEPORTS chain: dport 30080 → ingress-nginx pod)
  │
  ▼
ingress-nginx pod (192.168.235.196, running on k8s-master)
  │
  │ Calico VXLAN tunnel (UDP 4789) — cross-node overlay
  ▼
tomcat pod (192.168.254.132 or .133, on k8s-worker)
  port 8080
```

---

## Gateway API traffic flow (optional step 7)

```
Browser → <nginx-gateway-svc external IP>:80
  │
  │ Azure NSG: allow TCP 80 inbound
  ▼
NGINX Gateway Fabric pod (nginx-gateway namespace, on k8s-master)
  matches HTTPRoute: path prefix / → tomcat-service:80
  │
  │ Calico VXLAN tunnel (UDP 4789) — cross-node overlay
  ▼
tomcat pod (192.168.254.132 or .133, on k8s-worker)
  port 8080
```

**Gateway API vs Ingress:**

| | Ingress | Gateway API |
|---|---|---|
| API version | `networking.k8s.io/v1` | `gateway.networking.k8s.io/v1` |
| Controller | ingress-nginx (NodePort 30080) | NGINX Gateway Fabric (LoadBalancer/NodePort 80) |
| Namespace | `ingress-nginx` | `nginx-gateway` |
| Route object | `Ingress` | `HTTPRoute` |
| Multi-team routing | Limited | Built-in (cross-namespace refs) |
| Conflict with other | None | None — both run in parallel |

---

## Key concepts

| Concept | What it is |
|---|---|
| `kubeadm` | CLI tool that bootstraps a Kubernetes cluster (init, join, token) |
| `kubelet` | Agent running on every node; starts/stops pod containers |
| `kubectl` | CLI to manage the cluster (apply, get, describe, patch, logs) |
| `containerd` | Container runtime; actually pulls images and runs containers |
| Calico CNI | Network plugin; assigns pod IPs and routes traffic between pods across nodes |
| VXLAN | Layer-2 overlay over UDP; tunnels pod traffic between nodes through the Azure VNet |
| NodePort | Service type that opens a port (30000–32767) on every node, forwarded to the service pods |
| Ingress | Kubernetes API object that defines HTTP routing rules (host/path → service) |
| ingress-nginx | An ingress controller: watches Ingress objects and configures NGINX accordingly |
| kube-proxy | Runs on each node; programs nftables/iptables rules for Service routing and NodePort NAT |
| Gateway API | Successor to Ingress; three resources: GatewayClass (controller), Gateway (entry point), HTTPRoute (rules) |
| GatewayClass | Cluster-scoped resource that names the controller implementation (e.g. NGINX Gateway Fabric) |
| NGINX Gateway Fabric | Gateway API controller by NGINX Inc; replaces ingress-nginx in the Gateway API model |

---

## Cleanup

```bash
cd terraform
terraform destroy
```

Destroys all Azure resources (VMs, VNet, NSG, public IPs, NICs, resource group).

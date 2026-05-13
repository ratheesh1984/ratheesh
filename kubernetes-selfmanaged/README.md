# Kubernetes Master/Worker on Azure with Tomcat + NGINX Ingress
<<<<<<< HEAD
=======
# Hi how are you 
# This is ratheesh
# he i shari 
>>>>>>> d3678e316a3eb8a46bed962ffc9c55eb1494225d
Two-VM Kubernetes cluster on Azure, provisioned with Terraform, with a sample
Tomcat app deployed via YAML into a dedicated namespace, fronted by the
NGINX ingress controller.

## What you get
## What you get
- **Infra (Terraform):** RG, VNet, Subnet, NSG, 2 Public IPs, 2 NICs, 2 Ubuntu 22.04 VMs (master + worker), generated SSH key.
- **Cluster bootstrap:** containerd + kubeadm + kubelet + kubectl pre-installed via cloud-init; Calico CNI; ingress-nginx.
- **App (YAML):** namespace `tomcat-app`, ConfigMap (sample JSP), Deployment (2 replicas, Tomcat 9 + JDK 17), Service (`ClusterIP`), Ingress.
- **Traffic flow:** `client → NodePort 30080 → ingress-nginx → tomcat-service (ClusterIP) → tomcat pods`.

## Layout

```
terraform/      Azure infra
kubernetes/     YAML manifests applied with kubectl
scripts/        Bootstrap + deploy helpers
```

## Runbook

### 1. Provision Azure VMs

```bash
cd terraform
terraform init
terraform apply           # ~5 minutes
```

Outputs include the public IPs and ready-to-paste SSH commands. Private key is written to `terraform/k8s_id_rsa`.

### 2. Initialize the master

```bash
# from your laptop
scp -i terraform/k8s_id_rsa scripts/01-init-master.sh azureuser@<MASTER_IP>:~
ssh -i terraform/k8s_id_rsa azureuser@<MASTER_IP>

# on the master
chmod +x 01-init-master.sh
./01-init-master.sh <MASTER_PRIVATE_IP>     # e.g. 10.10.1.4
```

Copy the `kubeadm join ...` line it prints at the end.

### 3. Join the worker

```bash
scp -i terraform/k8s_id_rsa scripts/02-join-worker.sh azureuser@<WORKER_IP>:~
ssh -i terraform/k8s_id_rsa azureuser@<WORKER_IP>

# on the worker
chmod +x 02-join-worker.sh
sudo ./02-join-worker.sh kubeadm join <MASTER_PRIVATE_IP>:6443 --token ... --discovery-token-ca-cert-hash sha256:...
```

Verify on the master:

```bash
kubectl get nodes
# both nodes should show Ready
```

### 4. Deploy the Tomcat app

```bash
# copy manifests + script to master
scp -i terraform/k8s_id_rsa -r kubernetes scripts/03-deploy-app.sh azureuser@<MASTER_IP>:~

# on the master
chmod +x 03-deploy-app.sh
./03-deploy-app.sh
```

### 5. Hit it

The ingress-nginx controller is exposed as a NodePort on **30080**. Curl any node's public IP:

```bash
curl http://<WORKER_PUBLIC_IP>:30080/
# or
curl http://<MASTER_PUBLIC_IP>:30080/
```

You should get the sample JSP showing pod hostname, IP, and timestamp. Refresh a few times — the hostname changes between the two replicas, proving the ingress is load-balancing.

## Cleanup

```bash
cd terraform
terraform destroy
```

## Notes / variations

- **Why NodePort, not LoadBalancer?** A bare-metal kubeadm cluster has no Azure cloud controller, so `Service: LoadBalancer` would stay `<pending>`. The ingress controller is exposed as NodePort 30080, and the NSG opens 30000–32767. If you'd rather have a real Azure LB in front, add an `azurerm_lb` in Terraform pointing at both NICs on port 30080. (You could also switch to AKS, but then this whole exercise collapses to one Terraform module.)
- **SSH lockdown:** `allowed_ssh_cidr` defaults to `0.0.0.0/0`. Set it to `<your-ip>/32` in `terraform.tfvars`.
- **VM size:** `Standard_B2s` is the practical floor for kubeadm (2 vCPU / 4 GB).

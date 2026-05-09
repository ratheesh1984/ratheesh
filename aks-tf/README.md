# AKS Basic Test Cluster — Terraform

Single-node AKS cluster in East US for basic testing.

## Prerequisites

- Terraform >= 1.3.0
- Azure CLI installed and logged in
- Sufficient Azure subscription permissions (Contributor or Owner)

## Login to Azure

```bash
az login
az account set --subscription "<your-subscription-id>"
```

## Deploy

```bash
# 1. Initialise providers
terraform init

# 2. Preview what will be created
terraform plan

# 3. Deploy (takes ~5-8 minutes)
terraform apply

# 4. Configure kubectl
az aks get-credentials \
  --resource-group rg-aks-basic-test \
  --name aks-basic-test \
  --overwrite-existing

# 5. Verify node is ready
kubectl get nodes
```

## Get kubeconfig manually

```bash
terraform output -raw kube_config_raw > ~/.kube/config-aks-test
export KUBECONFIG=~/.kube/config-aks-test
```

## Get VNet details (for Azure LB backend pool)

```bash
terraform output vnet_name
terraform output node_resource_group
```

## Destroy when done (avoid unnecessary costs)

```bash
terraform destroy
```

## Resources created

| Resource | Name |
|---|---|
| Resource Group | rg-aks-basic-test |
| VNet | aks-basic-test-vnet (10.0.0.0/16) |
| Subnet | aks-basic-test-subnet (10.0.1.0/24) |
| AKS Cluster | aks-basic-test |
| Node pool | 1 x Standard_B2s |
| Identity | System-assigned managed identity |

## VM size options for testing

| Size | vCPU | RAM | Notes |
|---|---|---|---|
| Standard_B2s | 2 | 4GB | Cheapest, fine for basic testing |
| Standard_B2ms | 2 | 8GB | More memory for heavier workloads |
| Standard_D2s_v3 | 2 | 8GB | Better CPU performance |

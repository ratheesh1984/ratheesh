Username: hariaws2000@outlook.com
password: Iamgroot08@

az group create --name k8s_rg --location eastus
az deployment group create --resource-group k8s_rg --template-file AKS_k8s_service

kubectl create -f AKS_k8sdeployments_template         
kubectl get pods
kubectl delete pod ngnix
kubectl create deployment nginx --image=nginx
kubectl get deployments
kubectl expose deployment nginx --port=80 --target-port=80 --type=LoadBalancer


az aks show --resource-group kml_rg_main-5382a387a4f94280 --name k8s-dev --query nodeResourceGroup -o tsv
az resource list --resource-group MC_kml_rg_main-3caeada36b3b4148_k8s-dev_eastus -o table

#k8s - ingres-->service-->deployments
# Apply all three manifests
kubectl apply -f nginx-deployment.yaml
kubectl apply -f nginx-service.yaml
kubectl apply -f nginx-ingress.yaml

# Verify ingress is created (ADDRESS will be empty until LB is assigned)
kubectl get ingress nginx-ingress -n default

# Once you create your external Azure Load Balancer, 
# patch the ingress with the frontend IP:
kubectl patch ingress nginx-ingress -n default \
  --type='merge' \
  -p '{"status":{"loadBalancer":{"ingress":[{"ip":"<YOUR_LB_PUBLIC_IP>"}]}}}'

# OR if you're using a static public IP on your ingress controller service,
# annotate the ingress controller's LoadBalancer service instead:
kubectl annotate service ingress-nginx-controller \
  -n ingress-nginx \
  service.beta.kubernetes.io/azure-load-balancer-resource-group="<your-rg>"

k8s cluster start:
$ az aks start --resource-group rg-aks-basic-test --name aks-basic-test

k8s connect:
az aks get-credentials --resource-group rg-aks-basic-test --name aks-basic-test --overwrite-existing


helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update


  ####resource group change
error: C:\Users\arath\Downloads>az deployment group create --resource-group kml_rg_main-5382a387a4f94280 --template-file AKS_k8scluster_template.json
{"code": "AuthorizationFailed", "message": "The client 'kk_lab_user_main-78937c46f6594f2b@azurekmlprodkodekloud.onmicrosoft.com' with object id 'f6ccde21-5457-426f-83b9-020514787a94' does not have authorization to perform action 'Microsoft.Resources/deployments/validate/action' over scope '/subscriptions/a2b28c85-1948-4263-90ca-bade2bac4df4/resourcegroups/kml_rg_main-5382a387a4f94280/providers/Microsoft.Resources/deployments/AKS_k8scluster_template' or the scope is invalid. If access was recently granted, please refresh your credentials."}

======================================================================================================================
#k8s version change 1.29 to 1.33
azurerm_kubernetes_cluster.aks: Still creating... [00m10s elapsed]
╷
│ Error: creating Kubernetes Cluster (Subscription: "328ffe1c-5161-4d3f-a908-0208b8dfc44d"
│ Resource Group Name: "rg-aks-basic-test"
│ Kubernetes Cluster Name: "aks-basic-test"): performing CreateOrUpdate: unexpected status 400 (400 Bad Request) with response: {
│   "code": "K8sVersionNotSupported",
│   "details": null,
│   "message": "Managed cluster aks-basic-test is on version 1.29.15 which is not supported in this region. Please use [az aks get-versions] command to get the supported version list in this region. For more information, please check https://aka.ms/supported-version-list",
│   "subcode": ""
│  }
│ 
│   with azurerm_kubernetes_cluster.aks,
│   on main.tf line 42, in resource "azurerm_kubernetes_cluster" "aks":
│   42: resource "azurerm_kubernetes_cluster" "aks" {
  ==========================================================================================
Error 3: start k8s as its already in stopped state:
  azurerm_kubernetes_cluster.aks: Modifying... [id=/subscriptions/328ffe1c-5161-4d3f-a908-0208b8dfc44d/resourceGroups/rg-aks-basic-test/providers/Microsoft.ContainerService/managedClusters/aks-basic-test]
╷
│ Error: updating Default Node Pool Agent Pool (Subscription: "328ffe1c-5161-4d3f-a908-0208b8dfc44d"
│ Resource Group Name: "rg-aks-basic-test"
│ Managed Cluster Name: "aks-basic-test"
│ Agent Pool Name: "default") performing CreateOrUpdate: unexpected status 400 (400 Bad Request) with response: {
│   "code": "OperationNotAllowed",
│   "details": null,
│   "message": "An error has occurred in subscription 328ffe1c-5161-4d3f-a908-0208b8dfc44d, resourceGroup: rg-aks-basic-test request: Managed Cluster is in stopped state, no operations except for start are allowed.",
│   "subcode": ""
│  }
│ 
│   with azurerm_kubernetes_cluster.aks,
│   on main.tf line 42, in resource "azurerm_kubernetes_cluster" "aks":
│   42: resource "azurerm_kubernetes_cluster" "aks" {
│ ==========================================================================================
aks ╵

output "resource_group_name" {
  description = "Resource group name"
  value       = azurerm_resource_group.aks_rg.name
}

output "cluster_name" {
  description = "AKS cluster name"
  value       = azurerm_kubernetes_cluster.aks.name
}

output "cluster_id" {
  description = "AKS cluster resource ID"
  value       = azurerm_kubernetes_cluster.aks.id
}

output "kube_config_raw" {
  description = "Raw kubeconfig — use to configure kubectl"
  value       = azurerm_kubernetes_cluster.aks.kube_config_raw
  sensitive   = true
}

output "host" {
  description = "AKS API server endpoint"
  value       = azurerm_kubernetes_cluster.aks.kube_config[0].host
  sensitive   = true
}

output "node_resource_group" {
  description = "Auto-created MC_ resource group containing AKS nodes"
  value       = azurerm_kubernetes_cluster.aks.node_resource_group
}

output "vnet_name" {
  description = "VNet name (needed for Azure LB backend pool)"
  value       = azurerm_virtual_network.aks_vnet.name
}

output "subnet_id" {
  description = "Subnet ID used by AKS nodes"
  value       = azurerm_subnet.aks_subnet.id
}

output "identity_principal_id" {
  description = "System-assigned managed identity principal ID"
  value       = azurerm_kubernetes_cluster.aks.identity[0].principal_id
}

output "get_credentials_command" {
  description = "Run this command after apply to configure kubectl"
  value       = "az aks get-credentials --resource-group ${azurerm_resource_group.aks_rg.name} --name ${azurerm_kubernetes_cluster.aks.name} --overwrite-existing"
}

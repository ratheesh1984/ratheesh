variable "resource_group_name" {
  description = "Name of the Azure Resource Group"
  type        = string
  default     = "rg-aks-basic-test"
}

variable "location" {
  description = "Azure region for all resources"
  type        = string
  default     = "eastus"
}

variable "cluster_name" {
  description = "Name of the AKS cluster"
  type        = string
  default     = "aks-basic-test"
}

variable "dns_prefix" {
  description = "DNS prefix for the AKS cluster"
  type        = string
  default     = "aks-basic-test"
}

variable "kubernetes_version" {
  description = "Kubernetes version for the AKS cluster"
  type        = string
  default     = "1.29"
}

variable "node_vm_size" {
  description = "VM size for the single test node (Standard_B2s is cheapest for testing)"
  type        = string
  default     = "Standard_B2s"
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Environment = "testing"
    ManagedBy   = "terraform"
    Purpose     = "aks-basic-test"
  }
}

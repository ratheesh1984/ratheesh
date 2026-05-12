variable "resource_group_name" {
  description = "Azure resource group name"
  type        = string
  default     = "rg-k8s-tomcat"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "eastus"
}

variable "prefix" {
  description = "Prefix for resource naming"
  type        = string
  default     = "k8s"
}

variable "vm_size" {
  description = "VM size (min 2 vCPU / 2GB RAM for kubeadm)"
  type        = string
  default     = "Standard_DC2s_v3"
}

variable "admin_username" {
  description = "Admin user for the VMs"
  type        = string
  default     = "azureuser"
}

variable "vnet_cidr" {
  description = "VNet address space"
  type        = string
  default     = "10.10.0.0/16"
}

variable "subnet_cidr" {
  description = "Subnet address space"
  type        = string
  default     = "10.10.1.0/24"
}

variable "allowed_ssh_cidr" {
  description = "CIDR allowed to SSH (set to your /32 for security)"
  type        = string
  default     = "0.0.0.0/0"
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default = {
    project     = "k8s-tomcat"
    environment = "demo"
    managed_by  = "terraform"
  }
}

output "master_public_ip" {
  description = "Public IP of the Kubernetes master/control-plane node"
  value       = azurerm_public_ip.pip["master"].ip_address
}

output "master_private_ip" {
  description = "Private IP of the master (used for kubeadm --apiserver-advertise-address)"
  value       = azurerm_network_interface.nic["master"].private_ip_address
}

output "worker_public_ip" {
  description = "Public IP of the Kubernetes worker node"
  value       = azurerm_public_ip.pip["worker"].ip_address
}

output "worker_private_ip" {
  description = "Private IP of the worker"
  value       = azurerm_network_interface.nic["worker"].private_ip_address
}

output "ssh_master" {
  description = "SSH command for master"
  value       = "ssh -i k8s_id_rsa ${var.admin_username}@${azurerm_public_ip.pip["master"].ip_address}"
}

output "ssh_worker" {
  description = "SSH command for worker"
  value       = "ssh -i k8s_id_rsa ${var.admin_username}@${azurerm_public_ip.pip["worker"].ip_address}"
}

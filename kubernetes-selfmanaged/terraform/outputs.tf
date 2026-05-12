output "master_public_ip" {
  description = "Public IP of the master / jump host"
  value       = azurerm_public_ip.master_pip.ip_address
}

output "master_private_ip" {
  description = "Private IP of the master (used for kubeadm --apiserver-advertise-address)"
  value       = azurerm_network_interface.master_nic.private_ip_address
}

output "worker_private_ip" {
  description = "Private IP of the worker (no public IP — reach via master jump host)"
  value       = azurerm_network_interface.worker_nic.private_ip_address
}

output "ssh_master" {
  description = "SSH command for master"
  value       = "ssh -i k8s_id_rsa ${var.admin_username}@${azurerm_public_ip.master_pip.ip_address}"
}

output "ssh_worker_via_jump" {
  description = "SSH to worker through master as jump host"
  value       = "ssh -i k8s_id_rsa -J ${var.admin_username}@${azurerm_public_ip.master_pip.ip_address} ${var.admin_username}@${azurerm_network_interface.worker_nic.private_ip_address}"
}

output "app_url" {
  description = "URL to hit the Tomcat app via NGINX ingress (NodePort 30080 on master)"
  value       = "http://${azurerm_public_ip.master_pip.ip_address}:30080/"
}

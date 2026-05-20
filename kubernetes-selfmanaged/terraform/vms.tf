resource "tls_private_key" "ssh" {
  algorithm = "RSA"
  rsa_bits  = 4096
}
# Cloud-init: install containerd + kubeadm/kubelet/kubectl on every node.
locals {
  cloud_init = base64encode(<<-EOT
    #cloud-config
    package_update: true
    package_upgrade: false
    write_files:
      - path: /etc/modules-load.d/k8s.conf
        content: |
          overlay
          br_netfilter
      - path: /etc/sysctl.d/k8s.conf
        content: |
          net.bridge.bridge-nf-call-iptables  = 1
          net.bridge.bridge-nf-call-ip6tables = 1
          net.ipv4.ip_forward                 = 1
    runcmd:
      - swapoff -a
      - sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab
      - modprobe overlay
      - modprobe br_netfilter
      - sysctl --system
      - apt-get update -y
      - apt-get install -y apt-transport-https ca-certificates curl gnupg
      - mkdir -p /etc/apt/keyrings
      - apt-get install -y containerd
      - mkdir -p /etc/containerd
      - containerd config default | tee /etc/containerd/config.toml
      - sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
      - systemctl restart containerd
      - systemctl enable containerd
      - curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.29/deb/Release.key | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
      - echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.29/deb/ /" > /etc/apt/sources.list.d/kubernetes.list
      - apt-get update -y
      - apt-get install -y kubelet kubeadm kubectl
      - apt-mark hold kubelet kubeadm kubectl
      - systemctl enable kubelet
  EOT
  )
}

resource "azurerm_linux_virtual_machine" "master" {
  name                            = "${var.prefix}-master"
  resource_group_name             = azurerm_resource_group.rg.name
  location                        = azurerm_resource_group.rg.location
  size                            = var.vm_size
  admin_username                  = var.admin_username
  network_interface_ids           = [azurerm_network_interface.master_nic.id]
  disable_password_authentication = true
  custom_data                     = local.cloud_init
  tags                            = merge(var.tags, { role = "master" })

  admin_ssh_key {
    username   = var.admin_username
    public_key = tls_private_key.ssh.public_key_openssh
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
    disk_size_gb         = 30
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = "latest"
  }
}

resource "azurerm_linux_virtual_machine" "worker" {
  name                            = "${var.prefix}-worker"
  resource_group_name             = azurerm_resource_group.rg.name
  location                        = azurerm_resource_group.rg.location
  size                            = var.vm_size
  admin_username                  = var.admin_username
  network_interface_ids           = [azurerm_network_interface.worker_nic.id]
  disable_password_authentication = true
  custom_data                     = local.cloud_init
  tags                            = merge(var.tags, { role = "worker" })

  admin_ssh_key {
    username   = var.admin_username
    public_key = tls_private_key.ssh.public_key_openssh
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
    disk_size_gb         = 30
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = "latest"
  }
}

terraform {
  required_version = ">= 1.3.0"

  # State stored in Azure Blob — survives across GitHub Actions runs
  backend "azurerm" {
    resource_group_name  = "rg-tfstate"
    storage_account_name = "tfstatek8stomcat"   # must be globally unique, lowercase, 3-24 chars
    container_name       = "tfstate"
    key                  = "k8s-selfmanaged.tfstate"
    use_oidc             = true                       # authenticates via the same App Registration OIDC
  }

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }
}

provider "azurerm" {
  features {}
}

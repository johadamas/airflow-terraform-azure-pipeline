# Create a resource group
resource "azurerm_resource_group" "rg" {
  name     = "yugioh-project-rg"
  location = "Southeast Asia"
}

# Azure Data Lake Storage (ADLS)
resource "azurerm_storage_account" "adls" {
  name                     = "yugiohprojectstorage"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
  is_hns_enabled           = true
}

# Create a filesystem named "yugioh-data" inside ADLS
resource "azurerm_storage_data_lake_gen2_filesystem" "adls_fs" {
  name               = "yugioh-data"               # Filesystem name, acts like a container
  storage_account_id = azurerm_storage_account.adls.id
}

# Azure Synapse Analytics
resource "azurerm_synapse_workspace" "synapse" {
  name                = "yugioh-project-sa"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  storage_data_lake_gen2_filesystem_id = azurerm_storage_data_lake_gen2_filesystem.adls_fs.id
  sql_administrator_login          = "synapseadmin"
  sql_administrator_login_password = "Password123!"

  identity {
    type = "SystemAssigned"
  }
}

# Grant Synapse Workspace managed identity access to the ADLS container
resource "azurerm_role_assignment" "synapse_adls_access" {
  principal_id   = azurerm_synapse_workspace.synapse.identity[0].principal_id
  role_definition_name = "Storage Blob Data Contributor"
  scope          = azurerm_storage_account.adls.id
}

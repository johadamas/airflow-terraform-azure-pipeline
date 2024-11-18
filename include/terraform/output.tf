output "adls_access_key" {
  value = azurerm_storage_account.adls.primary_access_key
  sensitive = true
}

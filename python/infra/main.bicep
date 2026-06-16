@description('Base name for the resources, e.g. ramblers-sf-py')
param name string

@description('Location for all resources')
param location string = resourceGroup().location

@description('Entra tenant id the API validates inbound JWTs against')
param entraTenantId string = ''

@description('Application ID URI / audience the API accepts (the app registration that exposes this API)')
param entraAudience string = ''

@description('Comma-separated group/area codes this deployment serves')
param allowedGroupCodes string = ''

var storageName = toLower(replace('${name}stg', '-', ''))

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageName
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
}

resource plan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: '${name}-plan'
  location: location
  sku: { name: 'B1', tier: 'Basic' }
  properties: { reserved: true }
}

resource functionApp 'Microsoft.Web/sites@2023-12-01' = {
  name: '${name}-func'
  location: location
  kind: 'functionapp,linux'
  identity: { type: 'SystemAssigned' }
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'Python|3.11'
      ftpsState: 'Disabled'
      alwaysOn: true
      appSettings: [
        { name: 'FUNCTIONS_EXTENSION_VERSION', value: '~4' }
        { name: 'FUNCTIONS_WORKER_RUNTIME', value: 'python' }
        {
          name: 'AzureWebJobsStorage'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storage.name};EndpointSuffix=${environment().suffixes.storage};AccountKey=${storage.listKeys().keys[0].value}'
        }
        { name: 'AUTH_MODE', value: 'entra' }
        { name: 'ENTRA_TENANT_ID', value: entraTenantId }
        { name: 'ENTRA_AUDIENCE', value: entraAudience }
        { name: 'ALLOWED_GROUP_CODES', value: allowedGroupCodes }
        { name: 'PROVIDER', value: 'salesforce' }
        { name: 'OVERLAY_TABLE_NAME', value: 'memberoverlay' }
        {
          name: 'OVERLAY_CONNECTION_STRING'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storage.name};EndpointSuffix=${environment().suffixes.storage};AccountKey=${storage.listKeys().keys[0].value}'
        }
      ]
    }
  }
}

output functionAppName string = functionApp.name
output functionAppPrincipalId string = functionApp.identity.principalId

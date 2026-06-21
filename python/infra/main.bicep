@description('Base name for the resources, e.g. ramblers-sf-py')
param name string

@description('Location for all resources')
param location string = resourceGroup().location

@description('Full container image reference, e.g. myacr.azurecr.io/ramblers-sf-py:tag')
param containerImage string

@description('ACR login server the image is pulled from, e.g. myacr.azurecr.io')
param acrLoginServer string

@description('Name of the existing Azure Container Registry holding the image')
param acrName string

@description('demo (synthetic) or salesforce (real source + overlay)')
@allowed(['demo', 'salesforce'])
param provider string = 'demo'

@description('none (open demo), entra (validate Entra JWTs), or token (hashed bearer)')
@allowed(['none', 'entra', 'token'])
param authMode string = 'none'

@description('Entra tenant id whose tokens are accepted (entra mode). Not a secret.')
param entraTenantId string = ''

@description('API app registration Application id required as the token audience. Not a secret.')
param entraAudience string = ''

@description('Comma-separated group/area codes this deployment serves')
param allowedGroupCodes string = ''

@description('Overlay table name')
param overlayTableName string = 'memberoverlay'

var keyVaultSecretsUserRole = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  '4633458b-17de-408a-b874-0445c86b69e6'
)
var acrPullRole = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  '7f951dda-4ed3-4680-a7ca-43fe172d538d'
)

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${name}-identity'
  location: location
}

resource registry 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' existing = {
  name: acrName
}

resource acrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(registry.id, identity.id, acrPullRole)
  scope: registry
  properties: {
    roleDefinitionId: acrPullRole
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: toLower(replace('${name}overlay', '-', ''))
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
}

resource table 'Microsoft.Storage/storageAccounts/tableServices/tables@2023-05-01' = {
  name: '${storage.name}/default/${overlayTableName}'
}

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: '${name}-kv'
  location: location
  properties: {
    sku: { family: 'A', name: 'standard' }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
  }
}

resource overlaySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'overlay-connection-string'
  properties: {
    value: 'DefaultEndpointsProtocol=https;AccountName=${storage.name};EndpointSuffix=${environment().suffixes.storage};AccountKey=${storage.listKeys().keys[0].value}'
  }
}

resource keyVaultSecretsUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, identity.id, keyVaultSecretsUserRole)
  scope: keyVault
  properties: {
    roleDefinitionId: keyVaultSecretsUserRole
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${name}-logs'
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

resource managedEnv 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${name}-env'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logs.properties.customerId
        sharedKey: logs.listKeys().primarySharedKey
      }
    }
  }
}

resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: name
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${identity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: managedEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
      }
      registries: [
        {
          server: acrLoginServer
          identity: identity.id
        }
      ]
      secrets: [
        {
          name: 'overlay-connection-string'
          keyVaultUrl: '${keyVault.properties.vaultUri}secrets/overlay-connection-string'
          identity: identity.id
        }
      ]
    }
    template: {
      containers: [
        {
          name: name
          image: containerImage
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            { name: 'PROVIDER', value: provider }
            { name: 'AUTH_MODE', value: authMode }
            { name: 'ENTRA_TENANT_ID', value: entraTenantId }
            { name: 'ENTRA_AUDIENCE', value: entraAudience }
            { name: 'ALLOWED_GROUP_CODES', value: allowedGroupCodes }
            { name: 'OVERLAY_TABLE_NAME', value: overlayTableName }
            { name: 'OVERLAY_CONNECTION_STRING', secretRef: 'overlay-connection-string' }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
      }
    }
  }
  dependsOn: [
    acrPull
    keyVaultSecretsUser
    overlaySecret
  ]
}

output appFqdn string = app.properties.configuration.ingress.fqdn
output appPrincipalId string = identity.properties.principalId

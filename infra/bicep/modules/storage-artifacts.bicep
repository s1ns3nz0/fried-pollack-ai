param location string
param uniqueSuffix string
@description('Enable object-level immutability on artifact containers. Off in lab so the plane tears down cleanly; on for retention-critical environments.')
param enableImmutableArtifacts bool
param tags object

var storageName = 'dahredst${uniqueSuffix}'

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageName
  location: location
  sku: {
    name: 'Standard_ZRS'
  }
  kind: 'StorageV2'
  tags: tags
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    publicNetworkAccess: 'Enabled'
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  name: 'default'
  parent: storage
  properties: {
    isVersioningEnabled: true
    deleteRetentionPolicy: {
      enabled: true
      days: 30
    }
    containerDeleteRetentionPolicy: {
      enabled: true
      days: 30
    }
  }
}

resource containers 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = [for name in [
  'runs'
  'payloads'
  'reports'
]: {
  name: name
  parent: blobService
  properties: {
    publicAccess: 'None'
    immutableStorageWithVersioning: {
      enabled: enableImmutableArtifacts
    }
  }
}]

// Artifact lifecycle: hot for 30 days, cool at 30, expire at 365. Archive tier
// is intentionally omitted — it is unsupported on ZRS and moot for a lab that
// tears down well before 180 days. A retention-critical env can switch SKU to
// LRS/GRS and add tierToArchive.
resource lifecycle 'Microsoft.Storage/storageAccounts/managementPolicies@2023-05-01' = {
  name: 'default'
  parent: storage
  properties: {
    policy: {
      rules: [
        {
          name: 'red-artifact-lifecycle'
          enabled: true
          type: 'Lifecycle'
          definition: {
            filters: {
              blobTypes: [
                'blockBlob'
              ]
            }
            actions: {
              baseBlob: {
                tierToCool: {
                  daysAfterModificationGreaterThan: 30
                }
                delete: {
                  daysAfterModificationGreaterThan: 365
                }
              }
            }
          }
        }
      ]
    }
  }
}

output storageId string = storage.id
output storageName string = storage.name

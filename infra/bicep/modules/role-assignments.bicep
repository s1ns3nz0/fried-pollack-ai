param aksName string
param aksRbacClusterAdminObjectIds array
param acrName string
param storageName string
param toolserverPrincipalId string
param kubeletPrincipalId string

var acrPullRoleDefinitionId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
var storageBlobDataContributorRoleDefinitionId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
var aksRbacClusterAdminRoleDefinitionId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'b1ff04bb-8a4e-4dc4-8eb5-8693973ce19b')

resource acr 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' existing = {
  name: acrName
}

resource aks 'Microsoft.ContainerService/managedClusters@2024-05-01' existing = {
  name: aksName
}

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storageName
}

resource kubeletAcrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(acr.id, kubeletPrincipalId, 'AcrPull')
  scope: acr
  properties: {
    principalId: kubeletPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: acrPullRoleDefinitionId
  }
}

resource toolserverBlobContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage.id, toolserverPrincipalId, 'StorageBlobDataContributor')
  scope: storage
  properties: {
    principalId: toolserverPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: storageBlobDataContributorRoleDefinitionId
  }
}

resource aksRbacClusterAdmins 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for objectId in aksRbacClusterAdminObjectIds: {
  name: guid(aks.id, objectId, 'AzureKubernetesServiceRBACClusterAdmin')
  scope: aks
  properties: {
    principalId: objectId
    principalType: 'User'
    roleDefinitionId: aksRbacClusterAdminRoleDefinitionId
  }
}]

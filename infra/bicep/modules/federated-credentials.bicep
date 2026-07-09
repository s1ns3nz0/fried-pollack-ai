@description('OIDC issuer URL of the red AKS cluster.')
param oidcIssuerUrl string
param toolserverIdentityName string
param kagentIdentityName string
@description('Namespace/ServiceAccount that binds to the ToolServer identity.')
param toolserverNamespace string
param toolserverServiceAccount string
@description('Namespace/ServiceAccount that binds to the kagent identity.')
param kagentNamespace string
param kagentServiceAccount string

resource toolserverIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' existing = {
  name: toolserverIdentityName
}

resource kagentIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' existing = {
  name: kagentIdentityName
}

resource toolserverFederatedCredential 'Microsoft.ManagedIdentity/userAssignedIdentities/federatedIdentityCredentials@2023-01-31' = {
  name: 'red-toolserver-wi'
  parent: toolserverIdentity
  properties: {
    issuer: oidcIssuerUrl
    subject: 'system:serviceaccount:${toolserverNamespace}:${toolserverServiceAccount}'
    audiences: [
      'api://AzureADTokenExchange'
    ]
  }
}

resource kagentFederatedCredential 'Microsoft.ManagedIdentity/userAssignedIdentities/federatedIdentityCredentials@2023-01-31' = {
  name: 'red-kagent-wi'
  parent: kagentIdentity
  properties: {
    issuer: oidcIssuerUrl
    subject: 'system:serviceaccount:${kagentNamespace}:${kagentServiceAccount}'
    audiences: [
      'api://AzureADTokenExchange'
    ]
  }
}

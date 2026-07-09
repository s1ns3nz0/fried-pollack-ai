param location string
param tags object

resource kagentIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'dah-red-kagent-mi'
  location: location
  tags: tags
}

resource toolserverIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'dah-red-toolserver-mi'
  location: location
  tags: tags
}

output kagentIdentityName string = kagentIdentity.name
output kagentClientId string = kagentIdentity.properties.clientId
output kagentPrincipalId string = kagentIdentity.properties.principalId
output toolserverIdentityName string = toolserverIdentity.name
output toolserverClientId string = toolserverIdentity.properties.clientId
output toolserverPrincipalId string = toolserverIdentity.properties.principalId

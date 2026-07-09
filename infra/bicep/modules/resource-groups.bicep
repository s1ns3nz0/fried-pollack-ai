targetScope = 'subscription'

param location string
param redResourceGroupName string
param tags object

resource redRg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: redResourceGroupName
  location: location
  tags: tags
}

output redResourceGroupName string = redRg.name

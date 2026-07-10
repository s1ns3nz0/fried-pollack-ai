param location string
param simAddressPrefix string
param simAksSubnetPrefix string
param tags object

resource simVnet 'Microsoft.Network/virtualNetworks@2024-05-01' = {
  name: 'dah-sim-vnet'
  location: location
  tags: tags
  properties: {
    addressSpace: {
      addressPrefixes: [
        simAddressPrefix
      ]
    }
    subnets: [
      {
        name: 'snet-sim-aks'
        properties: {
          addressPrefix: simAksSubnetPrefix
        }
      }
    ]
  }
}

output simVnetId string = simVnet.id
output simAksSubnetId string = '${simVnet.id}/subnets/snet-sim-aks'

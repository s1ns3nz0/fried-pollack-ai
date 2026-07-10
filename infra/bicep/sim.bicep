targetScope = 'subscription'

@description('Deployment location for sim-plane Azure resources.')
param location string = 'koreacentral'

@description('Environment name used in tags and resource naming.')
param environment string = 'lab'

@description('Resource group for the sim plane.')
param simResourceGroupName string = 'dah-sim-rg'

@description('CIDR for the sim VNet.')
param simAddressPrefix string = '10.240.0.0/16'

@description('CIDR for the sim AKS subnet.')
param simAksSubnetPrefix string = '10.240.1.0/24'

@description('AKS API server authorized IP ranges for sim AKS.')
param authorizedIpRanges array

var plane = 'sim'
var commonTags = {
  project: 'dah'
  plane: plane
  environment: environment
  data_classification: 'restricted'
  managed_by: 'bicep'
}

resource simRg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: simResourceGroupName
  location: location
  tags: commonTags
}

module network 'modules/network-sim.bicep' = {
  name: 'sim-network'
  scope: resourceGroup(simResourceGroupName)
  dependsOn: [
    simRg
  ]
  params: {
    location: location
    simAddressPrefix: simAddressPrefix
    simAksSubnetPrefix: simAksSubnetPrefix
    tags: commonTags
  }
}

module aks 'modules/aks-sim.bicep' = {
  name: 'sim-aks'
  scope: resourceGroup(simResourceGroupName)
  params: {
    location: location
    aksSubnetId: network.outputs.simAksSubnetId
    nodeResourceGroup: '${simResourceGroupName}-aks-nodes'
    authorizedIpRanges: authorizedIpRanges
    tags: commonTags
  }
}

output simResourceGroupName string = simResourceGroupName
output simAksName string = aks.outputs.aksName
output simVnetId string = network.outputs.simVnetId

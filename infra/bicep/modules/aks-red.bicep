param location string
param aksSubnetId string
param nodeResourceGroup string
param authorizedIpRanges array
param tags object

resource aks 'Microsoft.ContainerService/managedClusters@2024-05-01' = {
  name: 'dah-red-aks'
  location: location
  tags: tags
  sku: {
    name: 'Base'
    tier: 'Standard'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    dnsPrefix: 'dah-red-aks'
    nodeResourceGroup: nodeResourceGroup
    disableLocalAccounts: true
    enableRBAC: true
    aadProfile: {
      managed: true
      enableAzureRBAC: true
    }
    oidcIssuerProfile: {
      enabled: true
    }
    securityProfile: {
      workloadIdentity: {
        enabled: true
      }
    }
    apiServerAccessProfile: {
      enablePrivateCluster: false
      authorizedIPRanges: authorizedIpRanges
    }
    networkProfile: {
      networkPlugin: 'azure'
      networkPolicy: 'calico'
      outboundType: 'userDefinedRouting'
    }
    agentPoolProfiles: [
      {
        name: 'npsystem'
        mode: 'System'
        count: 1
        vmSize: 'Standard_D4s_v5'
        osType: 'Linux'
        type: 'VirtualMachineScaleSets'
        vnetSubnetID: aksSubnetId
        enableAutoScaling: true
        minCount: 1
        maxCount: 3
      }
      {
        name: 'npred'
        mode: 'User'
        count: 1
        vmSize: 'Standard_D4s_v5'
        osType: 'Linux'
        type: 'VirtualMachineScaleSets'
        vnetSubnetID: aksSubnetId
        enableAutoScaling: true
        minCount: 1
        maxCount: 5
        nodeTaints: [
          'workload=red-agent:NoSchedule'
        ]
        nodeLabels: {
          workload: 'red-agent'
        }
      }
    ]
  }
}

output aksName string = aks.name
output aksId string = aks.id
output kubeletPrincipalId string = aks.properties.identityProfile.kubeletidentity.objectId
output oidcIssuerUrl string = aks.properties.oidcIssuerProfile.issuerURL

targetScope = 'subscription'

@description('Deployment location for red-plane Azure resources.')
param location string = 'koreacentral'

@description('Environment name used in tags and resource naming.')
param environment string = 'lab'

@description('Globally unique suffix for ACR and Storage Account names.')
param uniqueSuffix string

@description('CIDR for the red VNet.')
param redAddressPrefix string = '10.230.0.0/16'

@description('CIDR for the red AKS subnet.')
param redAksSubnetPrefix string = '10.230.1.0/24'

@description('CIDR for the red Azure Firewall subnet. Must be named AzureFirewallSubnet.')
param redFirewallSubnetPrefix string = '10.230.254.0/26'

@description('AKS API server authorized IP ranges.')
param authorizedIpRanges array

@description('Microsoft Entra object IDs granted Azure Kubernetes Service RBAC Cluster Admin on the red AKS cluster.')
param aksRbacClusterAdminObjectIds array = []

@description('Extra egress FQDNs allowed through the firewall (Azure OpenAI, approved sim endpoints).')
param allowedEgressFqdns array = [
  '*.openai.azure.com'
  '*.cognitiveservices.azure.com'
]

@description('Resource group containing the Azure OpenAI account used by kagent.')
param azureOpenAIResourceGroupName string = ''

@description('Azure OpenAI account name used by kagent.')
param azureOpenAIAccountName string = ''

@description('Azure OpenAI endpoint used by kagent ModelConfig.')
param azureOpenAIEndpoint string = ''

@description('Azure OpenAI deployment name used by kagent ModelConfig.')
param azureOpenAIDeploymentName string = ''

@description('Namespace of the red ToolServer ServiceAccount for Workload Identity federation.')
param toolserverNamespace string = 'red-agent'

@description('Name of the red ToolServer ServiceAccount for Workload Identity federation.')
param toolserverServiceAccount string = 'fried-pollack-toolserver'

@description('Namespace of the kagent ServiceAccount for Workload Identity federation.')
param kagentNamespace string = 'kagent'

@description('Name of the kagent ServiceAccount for Workload Identity federation.')
param kagentServiceAccount string = 'kagent'

@description('Enable SOC-facing resources (DNS link, VNet peering). Out of scope by default.')
param enableSoc bool = false

@description('Enable object-level immutability on artifact containers. Off in lab for clean teardown.')
param enableImmutableArtifacts bool = false

@description('Optional existing sim VNet resource ID for peering. Leave empty until known.')
param simVnetResourceId string = ''

@description('Optional existing soc VNet resource ID for peering. Only used when enableSoc is true.')
param socVnetResourceId string = ''

var plane = 'red'
var rgName = 'dah-red-rg'
var commonTags = {
  project: 'dah'
  plane: plane
  environment: environment
  data_classification: 'restricted'
  managed_by: 'bicep'
}

module resourceGroups 'modules/resource-groups.bicep' = {
  name: 'red-resource-groups'
  params: {
    location: location
    redResourceGroupName: rgName
    tags: commonTags
  }
}

module identities 'modules/identities.bicep' = {
  name: 'red-identities'
  scope: resourceGroup(rgName)
  dependsOn: [
    resourceGroups
  ]
  params: {
    location: location
    tags: commonTags
  }
}

module acr 'modules/acr.bicep' = {
  name: 'red-acr'
  scope: resourceGroup(rgName)
  dependsOn: [
    resourceGroups
  ]
  params: {
    location: location
    uniqueSuffix: uniqueSuffix
    tags: commonTags
  }
}

module storage 'modules/storage-artifacts.bicep' = {
  name: 'red-artifact-storage'
  scope: resourceGroup(rgName)
  dependsOn: [
    resourceGroups
  ]
  params: {
    location: location
    uniqueSuffix: uniqueSuffix
    enableImmutableArtifacts: enableImmutableArtifacts
    tags: commonTags
  }
}

module network 'modules/network-red.bicep' = {
  name: 'red-network'
  scope: resourceGroup(rgName)
  dependsOn: [
    resourceGroups
  ]
  params: {
    location: location
    redAddressPrefix: redAddressPrefix
    redAksSubnetPrefix: redAksSubnetPrefix
    redFirewallSubnetPrefix: redFirewallSubnetPrefix
    simVnetResourceId: simVnetResourceId
    socVnetResourceId: socVnetResourceId
    enableSoc: enableSoc
    tags: commonTags
  }
}

module firewall 'modules/firewall-egress.bicep' = {
  name: 'red-firewall'
  scope: resourceGroup(rgName)
  params: {
    location: location
    firewallSubnetId: network.outputs.firewallSubnetId
    redAksSubnetPrefix: redAksSubnetPrefix
    acrLoginServer: acr.outputs.loginServer
    allowedEgressFqdns: allowedEgressFqdns
    tags: commonTags
  }
}

module aks 'modules/aks-red.bicep' = {
  name: 'red-aks'
  scope: resourceGroup(rgName)
  // Egress routes through the firewall (userDefinedRouting), so the route table
  // and firewall rules must exist before the cluster bootstraps. Nodes reach the
  // public API server through the firewall, so its public IP must be authorized.
  // The firewall output reference below creates the required deployment ordering.
  params: {
    location: location
    aksSubnetId: network.outputs.aksSubnetId
    nodeResourceGroup: 'dah-red-rg-aks-nodes'
    authorizedIpRanges: union(authorizedIpRanges, [
      '${firewall.outputs.firewallPublicIp}/32'
    ])
    tags: commonTags
  }
}

module federatedCredentials 'modules/federated-credentials.bicep' = {
  name: 'red-federated-credentials'
  scope: resourceGroup(rgName)
  params: {
    oidcIssuerUrl: aks.outputs.oidcIssuerUrl
    toolserverIdentityName: identities.outputs.toolserverIdentityName
    kagentIdentityName: identities.outputs.kagentIdentityName
    toolserverNamespace: toolserverNamespace
    toolserverServiceAccount: toolserverServiceAccount
    kagentNamespace: kagentNamespace
    kagentServiceAccount: kagentServiceAccount
  }
}

module privateDns 'modules/private-dns.bicep' = {
  name: 'red-private-dns'
  scope: resourceGroup(rgName)
  params: {
    redVnetId: network.outputs.redVnetId
    enableSoc: enableSoc
    tags: commonTags
  }
}

module roleAssignments 'modules/role-assignments.bicep' = {
  name: 'red-role-assignments'
  scope: resourceGroup(rgName)
  params: {
    aksName: aks.outputs.aksName
    aksRbacClusterAdminObjectIds: aksRbacClusterAdminObjectIds
    acrName: acr.outputs.acrName
    storageName: storage.outputs.storageName
    toolserverPrincipalId: identities.outputs.toolserverPrincipalId
    kubeletPrincipalId: aks.outputs.kubeletPrincipalId
  }
}

module openAIRoleAssignments 'modules/openai-role-assignments.bicep' = if (!empty(azureOpenAIResourceGroupName) && !empty(azureOpenAIAccountName)) {
  name: 'red-openai-role-assignments'
  scope: resourceGroup(azureOpenAIResourceGroupName)
  params: {
    azureOpenAIAccountName: azureOpenAIAccountName
    kagentPrincipalId: identities.outputs.kagentPrincipalId
  }
}

output redResourceGroupName string = rgName
output redAksName string = aks.outputs.aksName
output redAcrLoginServer string = acr.outputs.loginServer
output redStorageName string = storage.outputs.storageName
output redKagentClientId string = identities.outputs.kagentClientId
output redToolserverClientId string = identities.outputs.toolserverClientId
output redFirewallPublicIp string = firewall.outputs.firewallPublicIp
output azureOpenAIEndpoint string = azureOpenAIEndpoint
output azureOpenAIDeploymentName string = azureOpenAIDeploymentName

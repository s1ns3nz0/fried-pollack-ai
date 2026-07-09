param location string
param firewallSubnetId string
param redAksSubnetPrefix string
@description('ACR login server the red AKS nodes pull images from, e.g. dahredacrxxxx.azurecr.io')
param acrLoginServer string
@description('Extra egress FQDNs the red agent is allowed to reach (Azure OpenAI, approved sim endpoints, etc.)')
param allowedEgressFqdns array
param tags object

resource firewallPublicIp 'Microsoft.Network/publicIPAddresses@2024-05-01' = {
  name: 'pip-red-fw-egress'
  location: location
  tags: tags
  sku: {
    name: 'Standard'
  }
  properties: {
    publicIPAllocationMethod: 'Static'
  }
}

resource firewallPolicy 'Microsoft.Network/firewallPolicies@2024-05-01' = {
  name: 'dah-red-fw-policy'
  location: location
  tags: tags
  properties: {
    threatIntelMode: 'Alert'
  }
}

// Default-deny egress with an explicit allowlist. Priority 200 network rules
// cover the AKS control-plane requirements; priority 300 application rules
// cover the FQDNs the nodes and red agent must reach. Everything else is denied
// by the firewall's implicit final rule.
resource ruleCollectionGroup 'Microsoft.Network/firewallPolicies/ruleCollectionGroups@2024-05-01' = {
  name: 'red-egress'
  parent: firewallPolicy
  properties: {
    priority: 200
    ruleCollections: [
      {
        ruleCollectionType: 'FirewallPolicyFilterRuleCollection'
        name: 'aks-network-egress'
        priority: 200
        action: {
          type: 'Allow'
        }
        rules: [
          {
            ruleType: 'NetworkRule'
            name: 'aks-control-plane-udp'
            ipProtocols: [
              'UDP'
            ]
            sourceAddresses: [
              redAksSubnetPrefix
            ]
            destinationAddresses: [
              'AzureCloud.${location}'
            ]
            destinationPorts: [
              '1194'
            ]
          }
          {
            ruleType: 'NetworkRule'
            name: 'aks-control-plane-tcp'
            ipProtocols: [
              'TCP'
            ]
            sourceAddresses: [
              redAksSubnetPrefix
            ]
            destinationAddresses: [
              'AzureCloud.${location}'
            ]
            destinationPorts: [
              // 9000 = tunnelfront, 443 = konnectivity/API server. Modern AKS
              // reaches the API server on 443; without it the node CSE bootstrap
              // fails its API-server connectivity check (curl exit 51).
              '9000'
              '443'
            ]
          }
          {
            ruleType: 'NetworkRule'
            name: 'ntp'
            ipProtocols: [
              'UDP'
            ]
            sourceAddresses: [
              redAksSubnetPrefix
            ]
            destinationAddresses: [
              '*'
            ]
            destinationPorts: [
              '123'
            ]
          }
        ]
      }
      {
        ruleCollectionType: 'FirewallPolicyFilterRuleCollection'
        name: 'aks-application-egress'
        priority: 300
        action: {
          type: 'Allow'
        }
        rules: [
          {
            ruleType: 'ApplicationRule'
            name: 'aks-required-fqdns'
            sourceAddresses: [
              redAksSubnetPrefix
            ]
            protocols: [
              {
                protocolType: 'Https'
                port: 443
              }
            ]
            fqdnTags: [
              'AzureKubernetesService'
            ]
          }
          {
            ruleType: 'ApplicationRule'
            name: 'container-registries'
            sourceAddresses: [
              redAksSubnetPrefix
            ]
            protocols: [
              {
                protocolType: 'Https'
                port: 443
              }
            ]
            targetFqdns: union([
              acrLoginServer
              'mcr.microsoft.com'
              '*.data.mcr.microsoft.com'
              '*.blob.${environment().suffixes.storage}'
              'packages.microsoft.com'
            ], allowedEgressFqdns)
          }
        ]
      }
    ]
  }
}

resource firewall 'Microsoft.Network/azureFirewalls@2024-05-01' = {
  name: 'dah-red-fw'
  location: location
  tags: tags
  dependsOn: [
    ruleCollectionGroup
  ]
  properties: {
    sku: {
      name: 'AZFW_VNet'
      tier: 'Standard'
    }
    firewallPolicy: {
      id: firewallPolicy.id
    }
    ipConfigurations: [
      {
        name: 'egress'
        properties: {
          subnet: {
            id: firewallSubnetId
          }
          publicIPAddress: {
            id: firewallPublicIp.id
          }
        }
      }
    ]
  }
}

output firewallPrivateIp string = firewall.properties.ipConfigurations[0].properties.privateIPAddress
output firewallPublicIp string = firewallPublicIp.properties.ipAddress

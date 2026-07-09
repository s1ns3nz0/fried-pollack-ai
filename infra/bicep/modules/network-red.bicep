param location string
param redAddressPrefix string
param redAksSubnetPrefix string
param redFirewallSubnetPrefix string
param simVnetResourceId string
param socVnetResourceId string
param enableSoc bool
param tags object

// Azure Firewall takes the 4th usable address of AzureFirewallSubnet as its
// private IP (index 3 => .4). Deriving it deterministically breaks the circular
// dependency between the route table, the subnet, and the firewall resource:
// the subnet can reference the route table at VNet-creation time while the
// firewall itself is provisioned in parallel.
var firewallPrivateIp = cidrHost(redFirewallSubnetPrefix, 3)

resource redAksRouteTable 'Microsoft.Network/routeTables@2024-05-01' = {
  name: 'rt-red-aks'
  location: location
  tags: tags
  properties: {
    disableBgpRoutePropagation: true
    routes: [
      {
        name: 'default-egress-to-firewall'
        properties: {
          addressPrefix: '0.0.0.0/0'
          nextHopType: 'VirtualAppliance'
          nextHopIpAddress: firewallPrivateIp
        }
      }
    ]
  }
}

resource redVnet 'Microsoft.Network/virtualNetworks@2024-05-01' = {
  name: 'dah-red-vnet'
  location: location
  tags: tags
  properties: {
    addressSpace: {
      addressPrefixes: [
        redAddressPrefix
      ]
    }
    subnets: [
      {
        name: 'snet-red-aks'
        properties: {
          addressPrefix: redAksSubnetPrefix
          routeTable: {
            id: redAksRouteTable.id
          }
        }
      }
      {
        // Azure Firewall subnet must be named AzureFirewallSubnet and must not
        // carry a route table, otherwise the firewall loses direct egress.
        name: 'AzureFirewallSubnet'
        properties: {
          addressPrefix: redFirewallSubnetPrefix
        }
      }
    ]
  }
}

resource simPeering 'Microsoft.Network/virtualNetworks/virtualNetworkPeerings@2024-05-01' = if (!empty(simVnetResourceId)) {
  name: 'peer-red-to-sim'
  parent: redVnet
  properties: {
    allowVirtualNetworkAccess: true
    allowForwardedTraffic: false
    allowGatewayTransit: false
    useRemoteGateways: false
    remoteVirtualNetwork: {
      id: simVnetResourceId
    }
  }
}

resource socPeering 'Microsoft.Network/virtualNetworks/virtualNetworkPeerings@2024-05-01' = if (enableSoc && !empty(socVnetResourceId)) {
  name: 'peer-red-to-soc'
  parent: redVnet
  properties: {
    allowVirtualNetworkAccess: true
    allowForwardedTraffic: false
    allowGatewayTransit: false
    useRemoteGateways: false
    remoteVirtualNetwork: {
      id: socVnetResourceId
    }
  }
}

output redVnetId string = redVnet.id
output aksSubnetId string = '${redVnet.id}/subnets/snet-red-aks'
output firewallSubnetId string = '${redVnet.id}/subnets/AzureFirewallSubnet'
output firewallPrivateIp string = firewallPrivateIp

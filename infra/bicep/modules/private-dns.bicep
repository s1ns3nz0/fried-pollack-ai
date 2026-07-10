param redVnetId string
param enableSoc bool
param tags object

resource simZone 'Microsoft.Network/privateDnsZones@2024-06-01' = {
  name: 'sim.pollak.store'
  location: 'global'
  tags: tags
}

resource simLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2024-06-01' = {
  name: 'link-red-vnet'
  parent: simZone
  location: 'global'
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: redVnetId
    }
  }
}

// SOC DNS is only linked into the red plane when SOC ingest is enabled. It is
// out of scope for this session and stays off by default.
resource socZone 'Microsoft.Network/privateDnsZones@2024-06-01' = if (enableSoc) {
  name: 'soc.pollak.store'
  location: 'global'
  tags: tags
}

resource socLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2024-06-01' = if (enableSoc) {
  name: 'link-red-vnet'
  parent: socZone
  location: 'global'
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: redVnetId
    }
  }
}

output simPrivateDnsZoneName string = simZone.name

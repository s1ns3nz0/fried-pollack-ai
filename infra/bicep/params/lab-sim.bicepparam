using '../sim.bicep'

param location = 'koreacentral'
param environment = 'lab'
param simResourceGroupName = 'dah-sim-rg'

param simAddressPrefix = '10.240.0.0/16'
param simAksSubnetPrefix = '10.240.1.0/24'

param authorizedIpRanges = [
  'REDACTED_IP/32'
]

using '../sim.bicep'

// Judge / reviewer sim-plane template for Path B. Replace REPLACE_* tokens.
// Deployed automatically by scripts/deploy-red-with-sim.sh when SIM_PARAM_FILE
// points here and the sim AKS does not already exist.

param location = 'koreacentral'
param environment = 'judge'
param simResourceGroupName = 'dah-sim-rg'

param simAddressPrefix = '10.240.0.0/16'
param simAksSubnetPrefix = '10.240.1.0/24'

// Your workstation public IP as a /32 (same value as judge.bicepparam).
// curl -s ifconfig.me
param authorizedIpRanges = [
  'REPLACE_YOUR_PUBLIC_IP/32'
]

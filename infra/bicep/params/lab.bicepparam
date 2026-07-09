using '../main.bicep'

param location = 'koreacentral'
param environment = 'lab'

param uniqueSuffix = 'r0710a'

param authorizedIpRanges = [
  'REDACTED_IP/32'
]

// Egress FQDNs allowed through dah-red-fw in addition to the AKS/registry
// baseline. Add approved sim target endpoints here as they are confirmed.
param allowedEgressFqdns = [
  '*.openai.azure.com'
  '*.cognitiveservices.azure.com'
  'cr.kagent.dev'
  'ghcr.io'
  '*.ghcr.io'
  'pkg-containers.githubusercontent.com'
  '*.pkg-containers.githubusercontent.com'
  'docker.io'
  '*.docker.io'
  'registry-1.docker.io'
  'auth.docker.io'
  'production.cloudflare.docker.com'
]

param aksRbacClusterAdminObjectIds = [
  'REDACTED_OBJECT_ID'
]

param azureOpenAIResourceGroupName = 'dah-soc-rg'
param azureOpenAIAccountName = 'dah-aoai-REDACTED'
param azureOpenAIEndpoint = 'https://dah-aoai-REDACTED.openai.azure.com/'
param azureOpenAIDeploymentName = 'gpt-4o-soc'

// Workload Identity federation subjects. Must match the red overlay manifests.
param toolserverNamespace = 'red-agent'
param toolserverServiceAccount = 'fried-pollack-toolserver'
param kagentNamespace = 'kagent'
param kagentServiceAccount = 'kagent-controller'

// SOC is out of scope for this session.
param enableSoc = false

// Lab: keep immutability off so `az group delete` tears the plane down cleanly.
// Object-level immutability blocks storage-account (and thus RG) deletion.
param enableImmutableArtifacts = false

// Fill after sim/soc VNet resource IDs are confirmed.
param simVnetResourceId = ''
param socVnetResourceId = ''

using '../main.bicep'

// ---------------------------------------------------------------------------
// Judge / reviewer parameter template for Path B (deploy into your OWN Azure
// subscription). Copy this file, replace every REPLACE_* token below, then
// deploy with:
//
//   az deployment sub create \
//     --location <your-region> \
//     --template-file infra/bicep/main.bicep \
//     --parameters infra/bicep/params/judge.bicepparam
//
// See deploy/JUDGE-DEPLOY.md for the full runbook. Tokens left as REPLACE_*
// intentionally fail `what-if`/`create` loudly instead of deploying into the
// author's tenant.
// ---------------------------------------------------------------------------

param location = 'koreacentral'
param environment = 'judge'

// Globally unique 4-8 char suffix. Combined with fixed prefixes to name the ACR
// (dahredacr<suffix>) and Storage account, which must be globally unique across
// all of Azure. Pick something random, e.g. 'jz7f3a'.
param uniqueSuffix = 'REPLACE_UNIQUE_SUFFIX'

// Your workstation's public IP as a /32. Find it with: curl -s ifconfig.me
// This is added to the AKS API server authorized-IP allowlist so your kubectl
// can reach the cluster.
param authorizedIpRanges = [
  'REPLACE_YOUR_PUBLIC_IP/32'
]

// Egress FQDNs allowed out through the red firewall, in addition to the
// AKS/registry baseline. The list below is provider-generic; keep as-is unless
// you add approved target endpoints.
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

// Your Microsoft Entra object ID, granted AKS RBAC Cluster Admin on the red
// cluster. Find it with: az ad signed-in-user show --query id -o tsv
param aksRbacClusterAdminObjectIds = [
  'REPLACE_YOUR_ENTRA_OBJECT_ID'
]

// Your own Azure OpenAI account (Path B requires you to provision this; the
// author's 'dah-soc-rg' account is not shareable). Create an account and a
// chat-model deployment (e.g. gpt-4o), then fill these in.
// See deploy/JUDGE-DEPLOY.md step 2.
param azureOpenAIResourceGroupName = 'REPLACE_YOUR_OPENAI_RESOURCE_GROUP'
param azureOpenAIAccountName = 'REPLACE_YOUR_OPENAI_ACCOUNT_NAME'
param azureOpenAIEndpoint = 'https://REPLACE_YOUR_OPENAI_ACCOUNT_NAME.openai.azure.com/'
param azureOpenAIDeploymentName = 'REPLACE_YOUR_OPENAI_DEPLOYMENT_NAME'

// Workload Identity federation subjects. Must match the red overlay manifests.
// Leave as-is unless you rename namespaces/service accounts.
param toolserverNamespace = 'red-agent'
param toolserverServiceAccount = 'fried-pollack-toolserver'
param kagentNamespace = 'kagent'
param kagentServiceAccount = 'kagent-controller'

// SOC plane is out of scope for review. Keep disabled.
param enableSoc = false

// Keep immutability off so `az group delete` tears the plane down cleanly after
// review. Object-level immutability blocks storage-account (and RG) deletion.
param enableImmutableArtifacts = false

// No sim/soc VNet peering for a standalone Path B deploy. deploy-red-with-sim.sh
// injects the sim VNet ID automatically when it provisions the sim plane too.
param simVnetResourceId = ''
param socVnetResourceId = ''

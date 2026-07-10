#!/usr/bin/env bash
set -euo pipefail

LOCATION="${LOCATION:-koreacentral}"
RED_DEPLOYMENT_NAME="${RED_DEPLOYMENT_NAME:-red-plane-current}"
SIM_DEPLOYMENT_NAME="${SIM_DEPLOYMENT_NAME:-sim-plane-current}"
RED_RESOURCE_GROUP="${RED_RESOURCE_GROUP:-dah-red-rg}"
SIM_RESOURCE_GROUP="${SIM_RESOURCE_GROUP:-dah-sim-rg}"
SIM_AKS_NAME="${SIM_AKS_NAME:-dah-sim-aks}"
SIM_VNET_NAME="${SIM_VNET_NAME:-dah-sim-vnet}"
DEPLOY_SIM="${DEPLOY_SIM:-true}"

# Path B (reviewer's own subscription): point these at the judge templates, e.g.
#   RED_PARAM_FILE=infra/bicep/params/judge.bicepparam \
#   SIM_PARAM_FILE=infra/bicep/params/judge-sim.bicepparam \
#   scripts/deploy-red-with-sim.sh
RED_PARAM_FILE="${RED_PARAM_FILE:-infra/bicep/params/lab.bicepparam}"
SIM_PARAM_FILE="${SIM_PARAM_FILE:-infra/bicep/params/lab-sim.bicepparam}"

sim_aks_exists() {
  az aks show \
    --resource-group "$SIM_RESOURCE_GROUP" \
    --name "$SIM_AKS_NAME" \
    --query id \
    --output tsv >/dev/null 2>&1
}

sim_vnet_id() {
  az network vnet show \
    --resource-group "$SIM_RESOURCE_GROUP" \
    --name "$SIM_VNET_NAME" \
    --query id \
    --output tsv 2>/dev/null || true
}

if [ "$DEPLOY_SIM" = "true" ]; then
  if sim_aks_exists; then
    echo "sim AKS exists in $SIM_RESOURCE_GROUP/$SIM_AKS_NAME; skipping sim deployment"
  else
    echo "sim AKS not found; deploying sim plane"
    az deployment sub create \
      --name "$SIM_DEPLOYMENT_NAME" \
      --location "$LOCATION" \
      --template-file infra/bicep/sim.bicep \
      --parameters "$SIM_PARAM_FILE" \
      --query '{state:properties.provisioningState,outputs:properties.outputs}' \
      --output json
  fi
else
  echo "DEPLOY_SIM=false; skipping sim deployment check"
fi

SIM_VNET_ID="$(sim_vnet_id)"
if [ -n "$SIM_VNET_ID" ]; then
  echo "using sim VNet for red peering: $SIM_VNET_ID"
  az deployment sub create \
    --name "$RED_DEPLOYMENT_NAME" \
    --location "$LOCATION" \
    --template-file infra/bicep/main.bicep \
    --parameters "$RED_PARAM_FILE" simVnetResourceId="$SIM_VNET_ID" \
    --query '{state:properties.provisioningState,outputs:properties.outputs}' \
    --output json
else
  echo "sim VNet $SIM_RESOURCE_GROUP/$SIM_VNET_NAME not found; deploying red without sim peering"
  az deployment sub create \
    --name "$RED_DEPLOYMENT_NAME" \
    --location "$LOCATION" \
    --template-file infra/bicep/main.bicep \
    --parameters "$RED_PARAM_FILE" \
    --query '{state:properties.provisioningState,outputs:properties.outputs}' \
    --output json
fi

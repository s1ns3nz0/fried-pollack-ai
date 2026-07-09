#!/usr/bin/env bash
set -euo pipefail

RED_RESOURCE_GROUP="${RED_RESOURCE_GROUP:-dah-red-rg}"
RED_AKS_NAME="${RED_AKS_NAME:-dah-red-aks}"
RED_ACR_NAME="${RED_ACR_NAME:-dahredacrr0710a}"
TOOLSERVER_IDENTITY_NAME="${TOOLSERVER_IDENTITY_NAME:-dah-red-toolserver-mi}"
KAGENT_IDENTITY_NAME="${KAGENT_IDENTITY_NAME:-dah-red-kagent-mi}"
AZURE_OPENAI_RESOURCE_GROUP="${AZURE_OPENAI_RESOURCE_GROUP:-dah-soc-rg}"
AZURE_OPENAI_ACCOUNT_NAME="${AZURE_OPENAI_ACCOUNT_NAME:-dah-aoai-REDACTED}"
KAGENT_VERSION="${KAGENT_VERSION:-0.9.9}"
CLIENT_ID_PLACEHOLDER="00000000-0000-0000-0000-000000000000"

az aks get-credentials \
  --resource-group "$RED_RESOURCE_GROUP" \
  --name "$RED_AKS_NAME" \
  --overwrite-existing

az deployment sub create \
  --name red-plane-current \
  --location koreacentral \
  --template-file infra/bicep/main.bicep \
  --parameters infra/bicep/params/lab.bicepparam \
  --query '{state:properties.provisioningState,outputs:properties.outputs}' \
  --output json

AZURE_OPENAI_KEY="$(
  az cognitiveservices account keys list \
    --resource-group "$AZURE_OPENAI_RESOURCE_GROUP" \
    --name "$AZURE_OPENAI_ACCOUNT_NAME" \
    --query key1 \
    --output tsv
)"

TOOLSERVER_CLIENT_ID="$(
  az identity show \
    --resource-group "$RED_RESOURCE_GROUP" \
    --name "$TOOLSERVER_IDENTITY_NAME" \
    --query clientId \
    --output tsv
)"

KAGENT_CLIENT_ID="$(
  az identity show \
    --resource-group "$RED_RESOURCE_GROUP" \
    --name "$KAGENT_IDENTITY_NAME" \
    --query clientId \
    --output tsv
)"

echo "Using ToolServer managed identity client ID: $TOOLSERVER_CLIENT_ID"
echo "Using kagent managed identity client ID: $KAGENT_CLIENT_ID"

kubectl create namespace kagent --dry-run=client -o yaml | kubectl apply -f -
kubectl create secret generic kagent-azure-openai \
  --namespace kagent \
  --from-literal=AZUREOPENAI_API_KEY="$AZURE_OPENAI_KEY" \
  --dry-run=client -o yaml | kubectl apply -f -

az acr import \
  --name "$RED_ACR_NAME" \
  --source docker.io/library/postgres:18.3-alpine \
  --image library/postgres:18.3-alpine \
  --force \
  --output none

helm upgrade --install kagent-crds \
  oci://ghcr.io/kagent-dev/kagent/helm/kagent-crds \
  --version "$KAGENT_VERSION" \
  --namespace kagent \
  --create-namespace \
  --wait \
  --timeout 10m

helm upgrade --install kagent \
  oci://ghcr.io/kagent-dev/kagent/helm/kagent \
  --version "$KAGENT_VERSION" \
  --namespace kagent \
  --values deploy/kagent-values.yaml \
  --wait \
  --timeout 15m

kubectl create namespace fried-pollack --dry-run=client -o yaml | kubectl apply -f -
kubectl create secret generic kagent-azure-openai \
  --namespace fried-pollack \
  --from-literal=AZUREOPENAI_API_KEY="$AZURE_OPENAI_KEY" \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl kustomize deploy/overlays/aks \
  | sed "s/${CLIENT_ID_PLACEHOLDER}/${TOOLSERVER_CLIENT_ID}/g" \
  | kubectl apply -f -
kubectl -n fried-pollack rollout status deploy/fried-pollack-toolserver --timeout=180s
kubectl -n fried-pollack get agent,remotemcpserver,modelconfig,pods

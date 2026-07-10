#!/usr/bin/env bash
set -euo pipefail

RED_RESOURCE_GROUP="${RED_RESOURCE_GROUP:-dah-red-rg}"
RED_AKS_NAME="${RED_AKS_NAME:-dah-red-aks}"
RED_ACR_NAME="${RED_ACR_NAME:-dahredacrr0710a}"
TOOLSERVER_IDENTITY_NAME="${TOOLSERVER_IDENTITY_NAME:-dah-red-toolserver-mi}"
KAGENT_IDENTITY_NAME="${KAGENT_IDENTITY_NAME:-dah-red-kagent-mi}"
AZURE_OPENAI_RESOURCE_GROUP="${AZURE_OPENAI_RESOURCE_GROUP:-dah-soc-rg}"
# The real Azure OpenAI account name is intentionally NOT committed (scrubbed to a
# placeholder in the public repo). Supply it at deploy time; it is injected into
# the kagent values + ModelConfig endpoint below, replacing AOAI_PLACEHOLDER.
AZURE_OPENAI_ACCOUNT_NAME="${AZURE_OPENAI_ACCOUNT_NAME:-dah-aoai-REDACTED}"
AOAI_PLACEHOLDER="dah-aoai-REDACTED"
KAGENT_VERSION="${KAGENT_VERSION:-0.9.9}"
# Azure infra (bicep) now lives in the pollak-infra repo. This app-repo script
# only installs the red workloads (kagent + ToolServer) onto an already-
# provisioned cluster. Re-applying bicep is off by default; provision from
# pollak-infra first. To re-apply from here, set BOOTSTRAP_APPLY_BICEP=true and
# point BICEP_TEMPLATE / BICEP_PARAM_FILE at a local pollak-infra checkout.
BOOTSTRAP_APPLY_BICEP="${BOOTSTRAP_APPLY_BICEP:-false}"
CLIENT_ID_PLACEHOLDER="00000000-0000-0000-0000-000000000000"

# Path B (reviewer's own subscription): override to target your resources.
#   TOOLSERVER_IMAGE  - your ACR image ref, swapped into the rendered overlay so
#                       the committed kustomization is not edited in place.
BICEP_TEMPLATE="${BICEP_TEMPLATE:-../pollak-infra/bicep/main.bicep}"
BICEP_PARAM_FILE="${BICEP_PARAM_FILE:-../pollak-infra/bicep/params/lab.bicepparam}"
DEFAULT_TOOLSERVER_IMAGE="dahredacrr0710a.azurecr.io/fried-pollack-ai:9db7585"
TOOLSERVER_IMAGE="${TOOLSERVER_IMAGE:-$DEFAULT_TOOLSERVER_IMAGE}"

az aks get-credentials \
  --resource-group "$RED_RESOURCE_GROUP" \
  --name "$RED_AKS_NAME" \
  --overwrite-existing
kubelogin convert-kubeconfig --login azurecli

if [ "$BOOTSTRAP_APPLY_BICEP" = "true" ]; then
  az deployment sub create \
    --name red-plane-current \
    --location koreacentral \
    --template-file "$BICEP_TEMPLATE" \
    --parameters "$BICEP_PARAM_FILE" \
    --query '{state:properties.provisioningState,outputs:properties.outputs}' \
    --output json
fi

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

# Inject the real Azure OpenAI account into the kagent values (public copy holds
# only the placeholder). Rendered to a temp file so the committed file stays clean.
KAGENT_VALUES_RENDERED="$(mktemp)"
trap 'rm -f "$KAGENT_VALUES_RENDERED"' EXIT
sed "s/${AOAI_PLACEHOLDER}/${AZURE_OPENAI_ACCOUNT_NAME}/g" \
  deploy/kagent-values.yaml > "$KAGENT_VALUES_RENDERED"

helm upgrade --install kagent \
  oci://ghcr.io/kagent-dev/kagent/helm/kagent \
  --version "$KAGENT_VERSION" \
  --namespace kagent \
  --values "$KAGENT_VALUES_RENDERED" \
  --wait \
  --timeout 15m

kubectl create namespace fried-pollack --dry-run=client -o yaml | kubectl apply -f -
kubectl create secret generic kagent-azure-openai \
  --namespace fried-pollack \
  --from-literal=AZUREOPENAI_API_KEY="$AZURE_OPENAI_KEY" \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl kustomize deploy/overlays/aks \
  | sed "s/${CLIENT_ID_PLACEHOLDER}/${TOOLSERVER_CLIENT_ID}/g" \
  | sed "s#${DEFAULT_TOOLSERVER_IMAGE}#${TOOLSERVER_IMAGE}#g" \
  | sed "s/${AOAI_PLACEHOLDER}/${AZURE_OPENAI_ACCOUNT_NAME}/g" \
  | kubectl apply -f -
kubectl -n fried-pollack rollout status deploy/fried-pollack-toolserver --timeout=180s
kubectl -n fried-pollack get agent,remotemcpserver,modelconfig,pods

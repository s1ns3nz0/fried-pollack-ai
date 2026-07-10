# Judge Deployment Guide (Path B — deploy into your own Azure subscription)

This guide lets a reviewer stand up the full red plane
(`fried-pollack-ai` ToolServer + kagent + optional ArgoCD, with an optional sim
target cluster) in **their own Azure subscription**, from a clean checkout of
this repository. No access to the author's tenant is required.

> The author's live deployment (`deploy/README.md`) hardcodes tenant-specific
> names (`dahredacrr0710a`, `dah-aoai-REDACTED`, the author's IP and Entra
> object ID). This guide replaces every one of those with values you control.

---

## 0. What gets created & rough cost

| Plane | Resource group | Key resources |
|---|---|---|
| red | `dah-red-rg` | AKS, ACR, Azure Firewall (+ public IP), Storage, VNet, managed identities |
| sim (optional) | `dah-sim-rg` | AKS, VNet — the UAV simulation target |

Azure Firewall and two AKS clusters are the cost drivers. Budget a few USD/hour
while running; **tear it all down after review (step 9)**.

## 1. Prerequisites

- An Azure subscription where you are **Owner** (needed to create resource
  groups and assign RBAC roles).
- CLIs on your workstation: `az` (logged in via `az login`), `kubectl`,
  `helm` (v3), `kustomize`, `docker` (running), `git`, `curl`.
- Quota for **2 × Standard AKS clusters** in your chosen region.
- Access to **Azure OpenAI** (subject to Microsoft approval on your
  subscription). kagent will not start without it.

Confirm your context:

```bash
az account show --query '{sub:id, tenant:tenantId}' -o table
az login   # if the above fails
```

## 2. Provision Azure OpenAI (you must own this)

The author's Azure OpenAI account is not shareable, so create your own and a
chat-model deployment.

```bash
OPENAI_RG=dah-judge-openai-rg
OPENAI_ACCT=judge-aoai-$RANDOM        # must be globally unique
LOCATION=koreacentral                 # a region where you have OpenAI quota

az group create -n "$OPENAI_RG" -l "$LOCATION"

az cognitiveservices account create \
  --name "$OPENAI_ACCT" --resource-group "$OPENAI_RG" \
  --kind OpenAI --sku S0 --location "$LOCATION" \
  --custom-domain "$OPENAI_ACCT" --yes

az cognitiveservices account deployment create \
  --name "$OPENAI_ACCT" --resource-group "$OPENAI_RG" \
  --deployment-name gpt-4o \
  --model-name gpt-4o --model-version 2024-11-20 --model-format OpenAI \
  --sku-capacity 10 --sku-name Standard

echo "endpoint: https://$OPENAI_ACCT.openai.azure.com/"
```

Note the resource group, account name, endpoint, and deployment name
(`gpt-4o`) — you fill these into the param file next.

## 3. Fill in the parameter templates

Gather your identifiers:

```bash
curl -s ifconfig.me                                   # your public IP
az ad signed-in-user show --query id -o tsv           # your Entra object ID
```

Azure infrastructure-as-code lives in the sibling **pollak-infra** repo. Clone
it next to this checkout:

```bash
git clone <pollak-infra-url> ../pollak-infra
```

Edit `../pollak-infra/bicep/params/judge.bicepparam` and replace every `REPLACE_*` token:

| Token | Value |
|---|---|
| `uniqueSuffix` | random 4–8 chars, e.g. `jz7f3a` (drives ACR/Storage names) |
| `authorizedIpRanges` | `<your public IP>/32` |
| `aksRbacClusterAdminObjectIds` | your Entra object ID |
| `azureOpenAIResourceGroupName` | `$OPENAI_RG` from step 2 |
| `azureOpenAIAccountName` | `$OPENAI_ACCT` |
| `azureOpenAIEndpoint` | `https://<account>.openai.azure.com/` |
| `azureOpenAIDeploymentName` | `gpt-4o` |

If you also want the sim target, apply the **same** `uniqueSuffix` region and
your IP to `../pollak-infra/bicep/params/judge-sim.bicepparam`.

Then set your shell environment (used by the bootstrap scripts):

```bash
cp deploy/judge.env.example deploy/judge.env
# edit deploy/judge.env: replace REPLACE_UNIQUE_SUFFIX and the OpenAI values
set -a; . deploy/judge.env; set +a
```

## 4. Deploy the Azure infrastructure

Run from the **pollak-infra** checkout. `deploy-red-with-sim.sh` provisions the
sim plane (if absent) and the red plane, wiring VNet peering automatically.

```bash
cd ../pollak-infra

# Dry run of the red plane
az deployment sub what-if \
  --location "$LOCATION" \
  --template-file bicep/main.bicep \
  --parameters "$RED_PARAM_FILE"

# Provision sim (optional) + red
scripts/deploy-red-with-sim.sh

cd -   # back to the app repo for the remaining steps
```

To skip the sim target entirely: `DEPLOY_SIM=false scripts/deploy-red-with-sim.sh`.

## 5. Build and push the ToolServer image to YOUR ACR

The committed overlay points at the author's ACR. Build from source and push to
yours; the bootstrap script rewrites the image reference from the
`TOOLSERVER_IMAGE` env var (set in step 3).

```bash
az acr login --name "$RED_ACR_NAME"
docker build -t "$TOOLSERVER_IMAGE" .
docker push "$TOOLSERVER_IMAGE"
```

## 6. Bootstrap kagent + the ToolServer

```bash
scripts/bootstrap-red-agent.sh
```

This reapplies Bicep, imports the mirrored Postgres image into your ACR, creates
the kagent Azure OpenAI secret from your account key, installs the kagent Helm
charts, and applies the red overlay with your ToolServer image and the recreated
managed-identity client ID injected.

## 7. (Optional) ArgoCD / GitOps

```bash
scripts/bootstrap-argocd.sh                  # uses ACR_NAME / ACR_LOGIN_SERVER from env
kubectl apply -f deploy/argocd/root-app.yaml
```

For continuous GitOps you would fork the repo and set the GitHub Actions
variables/secrets described in `deploy/README.md` step 7. For a one-shot review,
steps 5–6 are sufficient and ArgoCD is optional.

## 8. Verify

```bash
az aks get-credentials -g dah-red-rg -n dah-red-aks --overwrite-existing
kubectl -n fried-pollack get agent,remotemcpserver,modelconfig,pods
kubectl -n fried-pollack rollout status deploy/fried-pollack-toolserver --timeout=180s
```

All pods `Running` and the rollout complete means the plane is up.

## 9. Teardown (do this after review)

```bash
az group delete -n dah-red-rg --yes --no-wait
az group delete -n dah-sim-rg --yes --no-wait       # if you deployed sim
az group delete -n "$OPENAI_RG" --yes --no-wait     # your Azure OpenAI RG
```

Immutability is off by default, so the storage account and resource groups
delete cleanly.

## 10. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `what-if` fails on a `REPLACE_*` value | A token in `judge.bicepparam` wasn't filled in. |
| ACR name already taken | `uniqueSuffix` collided globally — pick another and update `judge.env`. |
| kagent pods `CrashLoopBackOff` | Azure OpenAI account/deployment name or key wrong; re-check step 2 values. |
| `kubectl` times out to the API server | Your public IP changed — update `authorizedIpRanges` and re-run the red deploy. |
| ToolServer `ImagePullBackOff` | Image not pushed to your ACR, or `TOOLSERVER_IMAGE` not exported (step 3/5). |

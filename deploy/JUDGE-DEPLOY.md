# Judge / Reviewer Guide

Three reproduction tiers, cheapest first. **Tier 0 needs no Azure and reproduces
the core contribution in minutes — start there.** Tiers 1 and the full
architecture are optional and progressively heavier.

| Tier | What it shows | Needs | Cost / time |
|---|---|---|---|
| **0 — Local contract** | attack scenarios → `UAV*_CL` telemetry → SOC Alert contract | Python only | ~0, minutes |
| **1 — Live red plane** | the agentic red ToolServer + kagent running on a real AKS cluster | your Azure subscription + Azure OpenAI | a few USD/hr |
| **Full 3-plane** | red attacks sim, SOC detects independently via Sentinel | 3 clusters + Sentinel | optional one-command live deployment; highest cost/time |

### Which path should I choose?

| Dimension | Tier 0 short demo | Full 3-plane launcher |
|---|---|---|
| Time / cost | Minutes / no Azure cost | Tens of minutes / billable Azure resources |
| AI model | No hosted model or API key | kagent uses Azure OpenAI `gpt-4o-mini` via `gpt-4o-soc` |
| Model authority | No LLM participates | Model assists interaction and summary; deterministic Gate, HITL, and ground truth retain authority |
| SOC evidence | Local UAV*_CL and Alert contract emulator | Real Log Analytics and Sentinel resources |
| Isolation evidence | Code, tests, and architecture | Separate live sim, SOC, and red AKS clusters |
| Dashboards | Generated KPI HTML | KPI, kagent UI, optional ArgoCD, and Azure Portal links |

---

## Tier 0 — Local detection-contract reproduction (no Azure)

This reproduces the project's central artifact: the red engagement's attack
actions turned into defender-side `UAV*_CL` telemetry rows and a single SOC
`Alert` (the one-way RedTeam→SOC contract). It runs entirely offline.

```bash
git clone https://github.com/s1ns3nz0/fried-pollack-ai.git && cd fried-pollack-ai
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

python run.py --emit-soc
```

Outputs land in `out/`:

- `out/uav_cl_rows.ndjson` — the `UAV*_CL` telemetry rows a range network tap
  would produce from the observed MAVLink traffic.
- `out/soc_alert.json` — the SOC Alert (detection signals, MITRE ATT&CK-ICS
  techniques, severity, D3FEND remediation playbook).

Inspect them:

```bash
cat out/soc_alert.json | python -m json.tool
```

> **Honesty note.** In Tier 0 the tap and Sentinel analytics rules are
> *emulated* red-side: `run.py` replays its own audit log to reconstruct the
> rows a real range tap + Sentinel would generate (see `redteam_core/bridge/`).
> This is a faithful stand-in for the contract, not a live SOC detection. The
> real pipeline (tap in the sim plane → Azure Sentinel append-only → SOC detects
> independently) is the "Full 3-plane" tier below.

Run the full test suite to confirm the build:

```bash
pytest -q          # 624 tests
```

---

## Tier 1 — Live red plane on Azure (optional)

Stands up the red plane (`fried-pollack-ai` ToolServer + kagent, optional
ArgoCD) in **your own Azure subscription**. Shows the agentic attack running on a
real AKS cluster. The sim target and SOC are **not** required for this tier.

Azure IaC lives in the sibling **pollack-infra** repo:

```bash
git clone https://github.com/s1ns3nz0/pollack-infra.git ../pollack-infra
```

### 1.1 Prerequisites

- Azure subscription where you are **Owner**.
- CLIs: `az` (logged in), `kubectl`, `helm` v3, `kustomize`, `docker` (running),
  `git`, `curl`.
- Quota for **1 Standard AKS cluster** (red only; sim is optional).
- **Azure OpenAI** access on your subscription (kagent will not start without
  it; subject to Microsoft approval).

```bash
az account show --query '{sub:id, tenant:tenantId}' -o table   # az login if needed
```

### 1.2 Provision your Azure OpenAI

```bash
OPENAI_RG=dah-judge-openai-rg
OPENAI_ACCT=judge-aoai-$RANDOM        # globally unique
LOCATION=koreacentral                 # a region where you have OpenAI quota

az group create -n "$OPENAI_RG" -l "$LOCATION"
az cognitiveservices account create \
  --name "$OPENAI_ACCT" --resource-group "$OPENAI_RG" \
  --kind OpenAI --sku S0 --location "$LOCATION" --custom-domain "$OPENAI_ACCT" --yes
az cognitiveservices account deployment create \
  --name "$OPENAI_ACCT" --resource-group "$OPENAI_RG" \
  --deployment-name gpt-4o \
  --model-name gpt-4o --model-version 2024-11-20 --model-format OpenAI \
  --sku-capacity 10 --sku-name Standard
echo "endpoint: https://$OPENAI_ACCT.openai.azure.com/"
```

### 1.3 Fill in the parameter template

```bash
curl -s ifconfig.me                             # your public IP
az ad signed-in-user show --query id -o tsv     # your Entra object ID
```

Edit `../pollack-infra/bicep/params/judge.bicepparam`, replacing every
`REPLACE_*` token:

| Token | Value |
|---|---|
| `uniqueSuffix` | random 4–8 chars, e.g. `jz7f3a` (drives ACR/Storage names) |
| `authorizedIpRanges` | `<your public IP>/32` |
| `aksRbacClusterAdminObjectIds` | your Entra object ID |
| `azureOpenAIResourceGroupName` | `$OPENAI_RG` |
| `azureOpenAIAccountName` | `$OPENAI_ACCT` |
| `azureOpenAIEndpoint` | `https://<account>.openai.azure.com/` |
| `azureOpenAIDeploymentName` | `gpt-4o` |

Set the shell environment used by the bootstrap script:

```bash
cp deploy/judge.env.example deploy/judge.env
# edit deploy/judge.env: REPLACE_UNIQUE_SUFFIX and the OpenAI values
set -a; . deploy/judge.env; set +a
```

### 1.4 Provision the red plane

```bash
cd ../pollack-infra
DEPLOY_SIM=false az deployment sub what-if \
  --location "$LOCATION" --template-file bicep/main.bicep --parameters "$RED_PARAM_FILE"
DEPLOY_SIM=false scripts/deploy-red-with-sim.sh
cd -
```

(Drop `DEPLOY_SIM=false` only if you also want the optional sim target cluster.)

### 1.5 Build & push the ToolServer image to your ACR

```bash
az acr login --name "$RED_ACR_NAME"
docker build -t "$TOOLSERVER_IMAGE" .
docker push "$TOOLSERVER_IMAGE"
```

### 1.6 Bootstrap kagent + the ToolServer

```bash
scripts/bootstrap-red-agent.sh
```

Imports the mirrored Postgres image into your ACR, creates the kagent Azure
OpenAI secret, installs the kagent Helm charts, and applies the red overlay with
your `TOOLSERVER_IMAGE` and the recreated managed-identity client ID injected.

### 1.7 (Optional) ArgoCD

```bash
scripts/bootstrap-argocd.sh
kubectl apply -f deploy/argocd/root-app.yaml
```

### 1.8 Verify

```bash
az aks get-credentials -g dah-red-rg -n dah-red-aks --overwrite-existing
kubectl -n fried-pollack get agent,remotemcpserver,modelconfig,pods
kubectl -n fried-pollack rollout status deploy/fried-pollack-toolserver --timeout=180s
```

### 1.9 Teardown (do this after review)

```bash
az group delete -n dah-red-rg --yes --no-wait
az group delete -n dah-sim-rg --yes --no-wait       # only if you deployed sim
az group delete -n "$OPENAI_RG" --yes --no-wait
```

Immutability is off by default, so resource groups delete cleanly.

---

## Full 3-plane architecture — one-command author demo

The complete design isolates three planes as **separate AKS clusters** (red /
sim / soc), with red→sim over VNet peering + firewall egress allowlist, and
sim→SOC over a shared **Azure Sentinel** workspace (append-only ingestion, no
direct sim↔soc network path) so the SOC detects the attack **independently** —
red is not in the detection path.

For the author's prepared subscription—or a reviewer who explicitly accepts
the time, cost, quota, and Azure OpenAI prerequisites—the complete environment
and its local dashboard proxies can be prepared with one command:

```bash
git clone https://github.com/s1ns3nz0/pollack-infra.git
git clone https://github.com/s1ns3nz0/fried-pollack-ai.git
cd pollack-infra
bash scripts/deploy-judge-demo.sh
```

The launcher deploys all planes, builds the ToolServer image when needed,
bootstraps kagent, generates the KPI HTML, verifies the Agent and MCP tool, and
prints kagent UI, KPI, optional ArgoCD, Sentinel, Log Analytics, AOAI, AKS, ACR,
and Storage links. Local proxy state is stored under
`/tmp/fried-pollack-judge-demo/` and can be stopped with:

```bash
bash scripts/stop-judge-demo.sh
```

Stopping proxies does **not** delete billable Azure resources. Tier 0 remains
the recommended time-boxed reproduction. Tier 1 above remains the cheaper
manual red-only alternative. The full launcher is for live control-plane and
isolation evidence when those additional costs and prerequisites are acceptable.

---

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| Tier 0 `pip install` fails | Use Python 3.11+; recreate the venv. |
| `what-if` fails on a `REPLACE_*` value | A token in `judge.bicepparam` wasn't filled in. |
| ACR name already taken | `uniqueSuffix` collided globally — pick another, update `judge.env`. |
| kagent pods `CrashLoopBackOff` | Azure OpenAI account/deployment name or key wrong; re-check 1.2 values. |
| `kubectl` times out to the API server | Your public IP changed — update `authorizedIpRanges` and re-run 1.4. |
| ToolServer `ImagePullBackOff` | Image not pushed to your ACR, or `TOOLSERVER_IMAGE` not exported. |

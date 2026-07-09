# Red Agent Separated Infrastructure Plan

> 작성: 2026-07-10
> 목적: `fried-pollack-ai` red agent를 표적 시뮬레이션 AKS와 분리된 red 전용 Azure 경계에 배포한다.

## 문제 정의

기존 AKS+kagent+ArgoCD 마이그레이션 계획은 red agent MCP ToolServer를 `dah-sim-aks`에 배포하는 전제를 갖고 있었다.
하지만 `dah-sim-aks`는 red agent가 공격 테스트를 수행해야 하는 **표적 시뮬레이션 레인지**다.

따라서 red agent를 `dah-sim-aks`에 올리면 다음 문제가 생긴다.

- 공격자와 표적이 같은 Kubernetes trust boundary 안에 존재한다.
- red agent가 실수로 표적 cluster API/RBAC/ServiceAccount 경계를 공유할 수 있다.
- 공격 트래픽과 내부 cluster 동작이 섞여 SOC/telemetry 해석이 왜곡된다.
- red/sim/soc 분리 원칙과 물리 안전 불변식이 약해진다.

## 확정 아키텍처

red, sim, soc를 별도 resource group과 AKS cluster로 분리한다.

| Plane | Resource Group | AKS | 역할 |
|---|---|---|---|
| red | `dah-red-rg` | `dah-red-aks` | red agent, kagent, MCP ToolServer, red ArgoCD |
| sim | `dah-sim-rg` | `dah-sim-aks` | UAV simulation target range |
| soc | `dah-soc-rg` | `dah-soc-aks` | SOC/defender telemetry and alerting |

## Naming Rules

| 종류 | 규칙 | 예시 |
|---|---|---|
| Resource Group | `dah-<plane>-rg` | `dah-red-rg` |
| AKS | `dah-<plane>-aks` | `dah-red-aks` |
| AKS node RG | `dah-<plane>-rg-aks-nodes` | `dah-red-rg-aks-nodes` |
| ACR | `dah<plane>acr<suffix>` | `dahredacr7k3m2p` |
| Storage Account | `dah<plane>st<suffix>` | `dahredst7k3m2p` |
| Managed Identity | `dah-<plane>-<role>-mi` | `dah-red-kagent-mi` |
| VNet | `dah-<plane>-vnet` | `dah-red-vnet` |
| Subnet | `snet-<plane>-<purpose>` | `snet-red-aks` |
| Firewall | `dah-red-fw` | `dah-red-fw` |
| Public IP | `pip-<plane>-<purpose>` | `pip-red-fw-egress` |
| Kubernetes namespace | `<plane>-<app>` or app name | `red-agent`, `argocd`, `kagent` |
| Workload | `<app>-<component>` | `fried-pollack-toolserver` |
| ArgoCD Application | `<plane>-<app>` | `red-fried-pollack-agent` |
| Private DNS zone | `<scope>.dah.internal` | `sim.dah.internal` |

Recommended tags:

- `project=dah`
- `plane=red|sim|soc`
- `environment=lab`
- `owner=<team>`
- `data_classification=restricted`
- `managed_by=bicep|argocd`

## Red Resource Inventory

`dah-red-rg` owns:

- `dah-red-aks`
- `dahredacr<suffix>`
- `dahredst<suffix>`
- `dah-red-vnet`
- `snet-red-aks`
- `snet-red-fw`
- `dah-red-fw`
- `pip-red-fw-egress`
- `dah-red-kagent-mi`
- `dah-red-toolserver-mi`
- red Private DNS links

## Deployment Boundary

Red agent runtime is deployed only to `dah-red-aks`.

Kubernetes resources:

- namespace `argocd`
- namespace `kagent`
- namespace `red-agent`
- Deployment `fried-pollack-toolserver`
- Service `fried-pollack-toolserver`
- kagent `ModelConfig`
- kagent `MCPServer`
- kagent `Agent`
- ConfigMap `target-profile`

Red ArgoCD manages only `dah-red-aks`.

Forbidden:

- red ArgoCD managing `dah-sim-aks`
- red ArgoCD managing `dah-soc-aks`
- red agent holding kubeconfig/RBAC for `dah-sim-aks`
- red agent holding kubeconfig/RBAC for `dah-soc-aks`

## Image and Artifact Stores

Image store:

- ACR: `dahredacr<suffix>.azurecr.io`
- repo: `fried-pollack-ai`
- tag: commit SHA

Artifact store:

- Storage Account: `dahredst<suffix>`
- containers:
  - `runs`
  - `payloads`
  - `reports`

Run artifact layout:

```text
runs/{run_id}/report.json
runs/{run_id}/full_scenario_eval.json
runs/{run_id}/successful_payloads.json
runs/{run_id}/scenario_results.csv
runs/{run_id}/soc_payload.json
runs/{run_id}/logs/*.log
```

Artifacts are immutable per `run_id`.

Lifecycle policy:

- hot: 30 days
- cool/archive: 180 days
- delete: 365 days or manual policy

Required metadata:

- `run_id`
- `git_sha`
- `image_digest`
- `target_profile_hash`
- `range_mode`
- `operator`
- `started_at`

## Identity Model

Use role-separated managed identities.

| Identity | Purpose | Permissions |
|---|---|---|
| `dah-red-kagent-mi` | kagent LLM orchestration | Azure OpenAI caller only |
| `dah-red-toolserver-mi` | ToolServer execution and artifact write | Storage Blob Data Contributor on `dahredst<suffix>` |
| AKS kubelet identity | image pull | AcrPull on `dahredacr<suffix>` |

Do not give kagent direct blob write unless a future design explicitly requires it.
Do not give ToolServer Azure OpenAI permission unless code starts calling LLMs directly.

## Network Model

Use VNet peering plus strict Azure Firewall/NSG allowlist.

Initial firewall policy:

- Azure Firewall SKU: Standard
- Egress public IP: `pip-red-fw-egress`
- Threat intel mode: Alert
- NAT Gateway: not used initially; firewall public IP is the fixed egress IP

Topology:

- `dah-red-vnet` peers with `dah-sim-vnet`
- `dah-red-vnet` peers with `dah-soc-vnet` only if SOC ingest is enabled
- red AKS subnet routes egress through `dah-red-fw`
- default deny egress

Allowed egress examples:

- red agent to Azure OpenAI endpoint
- red agent to `dahredacr<suffix>.azurecr.io`
- red agent to approved `dah-sim-aks` target service endpoints
- red agent to read-only oracle endpoint
- red agent to SOC ingest endpoint only when explicitly enabled
- red control plane operational endpoints required by AKS

Forbidden:

- red agent to `dah-sim-aks` Kubernetes API
- red agent to `dah-soc-aks` Kubernetes API
- red agent to full sim node/pod CIDR
- broad RFC1918 scanning
- unrestricted internet egress

Private Link may be added later for oracle/SOC ingest endpoints.

## Target Discovery

Red agent discovers targets using ConfigMap profile plus Azure Private DNS.

ConfigMap:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: target-profile
  namespace: red-agent
data:
  target_profile.yaml: |
    range_name: dah-sim
    allowed_range_modes:
      - container
      - sitl
    datalink_los_url: datalink-los.sim.dah.internal
    datalink_satcom_url: datalink-satcom.sim.dah.internal
    gcs_api_url: gcs.sim.dah.internal
    oracle_readonly_url: oracle.sim.dah.internal
    soc_ingest_url: soc-ingest.soc.dah.internal
```

DNS examples:

- `datalink-los.sim.dah.internal`
- `datalink-satcom.sim.dah.internal`
- `gcs.sim.dah.internal`
- `oracle.sim.dah.internal`
- `soc-ingest.soc.dah.internal`

## Range Mode Policy

Initial allowed modes:

| Mode | Policy |
|---|---|
| `container` | allowed |
| `sitl` | allowed |
| `hil` | blocked |
| `live` | blocked |

The MCP server must validate requested mode against `ALLOWED_RANGE_MODES`.

Initial env:

```text
ALLOWED_RANGE_MODES=container,sitl
```

`hil` and `live` remain disabled in deployment settings.

## Node Pools

Use separated node pools.

| Node Pool | Purpose |
|---|---|
| `np-system` | ArgoCD, kagent platform/controller, cluster add-ons |
| `np-red` | `fried-pollack-toolserver`, kagent Agent runtime, red execution workload |
| `np-tools` | optional future heavy benchmark/tool execution |

`np-red` should use taint:

```text
workload=red-agent:NoSchedule
```

Red workloads must include matching toleration and node selector.

## AKS API Access

Initial `dah-red-aks` API server policy:

- public API server enabled
- authorized IP ranges enabled
- Azure RBAC enabled
- local admin disabled
- OIDC issuer enabled
- Workload Identity enabled

Long-term private cluster migration remains possible through Bicep parameters,
but the initial build uses public API server plus authorized IP ranges for
bootstrap practicality.

## SOC Flow

Default:

- ToolServer writes artifacts to red storage.
- MCP response returns summary plus artifact URI.

Out of scope for this session:

- SOC ingest endpoint integration.
- SOC cluster deployment or schema design.
- Red-to-SOC network allowlist.

Future optional flow:

- `emit_soc=true`
- `soc_ingest_url` exists in target profile
- ToolServer emits SOC-facing alert/log payload to SOC ingest endpoint.

Forbidden:

- red agent writes directly to SOC cluster internals
- red agent has SOC AKS API access
- red agent has broad SOC Log Analytics write access

## IaC and GitOps Split

Use Bicep for Azure resources.

Bicep deployment shape:

- subscription-scope `infra/bicep/main.bicep`
- resource-group-scope modules
- parameters in `infra/bicep/params/lab.bicepparam`

Bicep owns:

- `dah-red-rg`
- `dah-red-aks`
- `dahredacr<suffix>`
- `dahredst<suffix>`
- red VNet/subnets/firewall/NAT/route tables
- Managed identities
- Role assignments
- Workload Identity federated credentials
- Private DNS links

ArgoCD owns Kubernetes apps in `dah-red-aks`.

ArgoCD apps:

- `red-kagent-platform`
- `red-fried-pollack-agent`

CI/CD:

- PR: pytest, full scenario eval, manifest render, secret scan
- main: GitHub OIDC login, `az deployment what-if`, `az deployment create`, image push to red ACR, GitOps image tag bump
- red ArgoCD syncs red AKS only

Recommended repo structure:

```text
infra/
  bicep/
    main.bicep
    params/
      lab.bicepparam
    modules/
      resource-groups.bicep
      network-red.bicep
      firewall-egress.bicep
      aks-red.bicep
      acr.bicep
      storage-artifacts.bicep
      identities.bicep
      private-dns.bicep
      role-assignments.bicep
```

## Required Code/Repo Changes

1. Add Bicep under `infra/bicep`.
2. Add `deploy/overlays/red-aks`.
3. Replace sim-oriented placeholder examples with red-oriented values.
4. Update `mcp_server.py` from hardcoded `container` to env allowlist.
5. Add target profile ConfigMap manifest.
6. Add nodeSelector/toleration for red workloads.
7. Add artifact storage support in service layer.
8. Update CI to push to red ACR and bump red overlay.
9. Update docs to state `dah-sim-aks` is target only.

## Superseded Decisions

- Terraform was considered first, but cancelled in favor of Bicep because the infrastructure is Azure-only and can be managed with native ARM deployments.
- Terraform state backend (`dah-tfstate-rg`, `dahtfst<suffix>`) is no longer required.

## Open Decisions

- Exact suffix generation for globally unique ACR and Storage Account names.
- Whether kagent CRDs are installed by red ArgoCD or Bicep bootstrap.

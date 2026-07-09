# Red Plane Implementation Plan

> 작성: 2026-07-10
> 기준 설계: `plans/2026-07-10-red-agent-separated-infra.md`
> 범위: red plane only. SOC ingest는 다른 세션에서 다룬다.

## 목표

`fried-pollack-ai` red agent를 표적 `dah-sim-aks`와 분리된 `dah-red-aks`에 배포할 수 있게 만든다.

1차 완료 기준:

- Bicep으로 red Azure 리소스를 what-if/build 검증할 수 있다.
- red AKS용 GitOps overlay가 존재한다.
- MCP ToolServer는 `container,sitl`만 허용하고 `hil/live`를 차단한다.
- red workload는 `np-red` node pool에만 스케줄되도록 설정된다.
- target discovery는 ConfigMap profile과 Private DNS 이름을 사용한다.
- run artifact는 red storage에 저장할 수 있는 코드 경계가 준비된다.
- CI/CD는 red ACR과 red overlay를 대상으로 동작한다.

## 범위 밖

- SOC ingest endpoint 구현
- SOC AKS 배포
- HIL/live range enablement
- sim AKS 리소스 변경
- red ArgoCD가 sim/soc cluster를 관리하는 구조

## Phase 1 — Bicep 완성도 올리기

작업:

- `infra/bicep/main.bicep`와 modules를 deployable 수준으로 보강한다.
- `lab.bicepparam`에서 placeholder를 명확히 한다.
- red AKS public API + authorized IP ranges를 파라미터화한다.
- Azure Firewall Standard와 route table/UDR 연결을 완성한다.
- ACR, Storage, Managed Identity, role assignment를 검증한다.
- Workload Identity federated credentials를 Bicep에 추가한다.

검증:

```bash
az bicep build --file infra/bicep/main.bicep
az deployment sub what-if \
  --location koreacentral \
  --template-file infra/bicep/main.bicep \
  --parameters infra/bicep/params/lab.bicepparam
```

완료 조건:

- build 오류 0
- what-if가 red plane 리소스만 생성/변경한다.

## Phase 2 — red AKS overlay 추가

작업:

- `deploy/overlays/red-aks/kustomization.yaml` 추가
- image newName을 `dahredacr<suffix>.azurecr.io/fried-pollack-ai`로 설정
- namespace를 `red-agent`로 변경
- ServiceAccount annotation을 `dah-red-toolserver-mi` client ID로 patch
- Deployment에 nodeSelector/toleration 추가:
  - `nodeSelector.workload=red-agent`
  - toleration `workload=red-agent:NoSchedule`
- env 추가:
  - `ALLOWED_RANGE_MODES=container,sitl`
  - storage 관련 env
  - target profile path

검증:

```bash
kubectl kustomize deploy/overlays/red-aks
```

완료 조건:

- rendered namespace가 `red-agent`
- rendered image가 red ACR
- `hil/live`는 env allowlist에 없다.

## Phase 3 — target profile ConfigMap

작업:

- `deploy/base/target-profile-configmap.yaml` 추가
- `target_profile.yaml`에 red가 사용할 sim endpoint DNS 이름만 둔다.
- SOC ingest 값은 비워두거나 제외한다.

초기 값:

```yaml
range_name: dah-sim
allowed_range_modes:
  - container
  - sitl
datalink_los_url: datalink-los.sim.dah.internal
datalink_satcom_url: datalink-satcom.sim.dah.internal
gcs_api_url: gcs.sim.dah.internal
oracle_readonly_url: oracle.sim.dah.internal
```

검증:

```bash
kubectl kustomize deploy/overlays/red-aks | rg 'target-profile|datalink-los.sim.dah.internal'
```

완료 조건:

- red agent가 sim Kubernetes API 없이 endpoint를 알 수 있다.

## Phase 4 — MCP range mode policy

작업:

- `mcp_server.py`의 hardcoded `container` 검증을 env allowlist로 변경한다.
- 기본값은 안전하게 `container`.
- red overlay에서만 `ALLOWED_RANGE_MODES=container,sitl` 설정.
- `hil/live` 요청은 red overlay에서도 거부된다.

검증:

```bash
python -m pytest tests/test_mcp_server.py -q
ALLOWED_RANGE_MODES=container,sitl python - <<'PY'
from mcp_server import validate_cluster_range_mode
print(validate_cluster_range_mode('container'))
print(validate_cluster_range_mode('sitl'))
try:
    validate_cluster_range_mode('live')
except ValueError as e:
    print('blocked')
PY
```

완료 조건:

- `container`, `sitl` 허용
- `hil`, `live` 차단

## Phase 5 — artifact storage seam

작업:

- service layer에 run artifact writer seam 추가
- 기본은 현재처럼 inline/no-op
- Azure Blob writer는 env가 있을 때만 활성화
- 저장 대상:
  - `report.json`
  - `full_scenario_eval.json`
  - `successful_payloads.json`
  - logs
- MCP 응답에는 artifact URI와 요약을 반환한다.

검증:

```bash
python -m pytest tests/test_mcp_server.py tests/test_deploy_manifests.py -q
python run.py --json
```

완료 조건:

- storage env가 없으면 기존 CLI 동작 불변
- storage env가 있으면 writer seam을 통해 artifact path가 생성된다.

## Phase 6 — CI/CD red target

작업:

- GitHub Actions variables를 red 기준으로 정리한다.
  - `RED_ACR_NAME`
  - `RED_RESOURCE_GROUP`
  - `RED_AKS_NAME`
- image push target을 red ACR로 변경한다.
- kustomize image bump target을 `deploy/overlays/red-aks`로 변경한다.
- PR에 Bicep build 검증 추가.

검증:

```bash
az bicep build --file infra/bicep/main.bicep
python -m pytest -q
kubectl kustomize deploy/overlays/red-aks
```

완료 조건:

- CI가 sim ACR/AKS를 참조하지 않는다.
- red overlay만 bump한다.

## Phase 7 — red-only smoke test

작업:

- ACR remote build 또는 CI image push
- red AKS에 ArgoCD/app sync
- ToolServer rollout 확인
- `/healthz`
- MCP `list_tools`
- `run_engagement(range_mode=container)`
- `run_engagement(range_mode=sitl)`은 target endpoint allowlist가 준비된 뒤에만 수행

검증:

```bash
kubectl get pods -n red-agent -o wide
kubectl port-forward -n red-agent svc/fried-pollack-toolserver 18081:8080
curl -fsS http://127.0.0.1:18081/healthz
```

완료 조건:

- red workload가 `np-red` 노드에 뜬다.
- red workload가 `dah-sim-aks`에 배포되지 않는다.
- MCP tool 호출이 성공한다.

## Final Verification

```bash
az bicep build --file infra/bicep/main.bicep
kubectl kustomize deploy/overlays/red-aks
python -m pytest -q
```

성공 기준:

- Bicep build 통과
- red overlay render 통과
- pytest 전체 통과
- `test-results/`는 git ignored 상태 유지

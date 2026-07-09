# AKS + kagent + ArgoCD 마이그레이션 계획

> fried-pollack-ai(UAV 레드팀 CLI)를 AKS에서 kagent 오케스트레이션 + ArgoCD GitOps로 구동.
> 작성 2026-07-09. grill-me 합의 결과 기반.

## 합의된 설계 결정 (요약)

| # | 결정 | 선택 |
|---|---|---|
| Q1 | kagent 역할 | **A** — kagent 오케스트레이터, 앱은 MCP ToolServer |
| Q2 | 툴 표면 | **coarse** — 굵은 툴 1~2개(`run_engagement`). LLM에 스텝 판정권 안 줌 |
| Q3 | HITL(물리 비가역) | **fail-closed** — `range_mode=container` 스텁 전용, 게이트 도달 기록만. 실 SITL 범위 밖 |
| Q4 | 오케스트레이터 LLM | **Azure OpenAI** + Workload Identity(키리스) |
| Q5 | GitOps 토폴로지 | **mono repo `deploy/` + app-of-apps**. ArgoCD가 kagent 플랫폼+앱 부트스트랩 |
| Q6 | MCP wrapper | **HTTP/SSE + FastMCP + in-process 호출** |
| Q7 | 이미지/승격 | **ACR + CI-bump**(태그=커밋 SHA, kustomize newTag 커밋) |
| Q8 | 산출물 | **inline** — 파일 안 씀, 응답 JSON에 SOC 행/Alert 반환. stateless |
| Q9 | 아이덴티티 | **Workload Identity**(Azure OpenAI keyless, ACR AcrPull, repo public) |

**불변 원칙**: 안전 게이트·오라클·HITL·결정론 파이프라인은 컨테이너 안에 그대로. kagent LLM은
판정권 0 — "실행 트리거 + 리포트 요약"만. `range_mode=container`에서 물리 비가역은 게이트에서
거부되고 "능력 도달"만 기록(A4 킬체인 `n3 takeoff blocked`와 동일) → 헤드리스 파드와 완전 호환.

---

## 현 코드 사실 (탐색 결과)

- `run.py:run_engagement(profile, range_mode, hardened, apply_egress, persist_learning)` 이미
  존재 → 전체 state dict 반환. **서비스 추출이 사실상 완료돼 있음.**
- `run.py:_emit_soc(state, out_dir)` — state에서 `tap_from_audit`→rows, `rows_to_alert`→alert 생성
  후 **파일로 씀**. 인라인화 = 이 로직에서 파일 쓰기만 제거하면 됨.
- `run.py:demo_approver` — 물리 비가역 `denied`, 그 외 `approved`. 헤드리스 fail-closed 이미 구현됨.
- 컨테이너/k8s 아티팩트 전무. `.github/workflows/ci.yml` 하나(pytest→check_gates→verify_claims→gitleaks).
- Python 3.12. Tier-0 stdlib 실행. `requirements.txt`: langgraph/pyyaml/pydantic-settings/pytest/pymavlink.

---

## Tracer-bullet 단계 (각 단계 독립 검증 가능)

### Phase 0 — 브랜치
- `main`에서 `feat/aks-kagent-argocd` 브랜치 생성.

### Phase 1 — 서비스 레이어 추출 (코드, CLI 동작 불변)
목표: MCP 서버와 CLI가 같은 함수 호출. 로직 중복 0.

- `redteam_core/service.py` 신규:
  - `run_engagement(profile_path, range_mode="container", hardened=False, emit_soc=False,
    apply_egress=False, persist_learning=None) -> dict`
  - 내부: 현 `run.py:run_engagement` 로직 이동 + `report = state["report"]` 추출.
  - `emit_soc=True`면 `tap_from_audit`/`rows_to_alert`로 rows·alert 생성해 **반환 dict에 인라인**
    (`{"report":…, "soc":{"rows":[…],"alert":{…}}, "backend":…}`). 파일 안 씀.
  - `demo_approver`(fail-closed HITL)도 이 모듈로 이동.
- `run.py` 리팩터: `from redteam_core.service import run_engagement`. CLI는 이 함수 호출 후
  기존대로 출력. `--emit-soc`는 반환된 inline soc를 파일로 쓰는 얇은 어댑터로(CLI 파리티 유지).
- **검증**: `python run.py --json`, `python run.py --emit-soc`, `./run_tests.sh`(182 tests green 유지).

### Phase 2 — MCP 서버 (코드)
- `requirements.txt`에 `mcp>=1.0`(FastMCP) 추가 — Tier 확장 주석으로 명시(선택 seam).
- `mcp_server.py` 신규:
  - FastMCP HTTP/SSE 서버. `@mcp.tool()` `run_engagement(range_mode="container", hardened=False,
    emit_soc=False, profile=None)` → `service.run_engagement(...)` 반환 dict.
  - `range_mode`는 기본 `container` 강제, `sitl|hil|live` 요청 시 **거부**(클러스터 스텁 전용 불변식).
  - 헬스 엔드포인트(`/healthz`) — k8s probe용.
  - 포트/호스트 env(`MCP_HOST`,`MCP_PORT`) 파라미터화.
- **검증**: 로컬 `python mcp_server.py` 기동 후 MCP inspector 또는 curl로 `run_engagement` 호출,
  스텁 리포트 JSON 확인. `range_mode=sitl` 요청이 거부되는지 확인.

### Phase 3 — 컨테이너 (Dockerfile)
- `Dockerfile`: `python:3.12-slim` 베이스, non-root user, `pip install -r requirements.txt`,
  `CMD ["python","mcp_server.py"]`. `.dockerignore`(out/, .git, __pycache__, tests 선택).
- **검증**: `docker build` → `docker run -p 8080:8080` → curl `run_engagement`.

### Phase 4 — k8s manifest (`deploy/base` + `overlays/aks`)
- `deploy/base/`:
  - `toolserver-deploy.yaml` — Deployment(non-root, resources, liveness/readiness `/healthz`,
    replicas=1) + Service(ClusterIP :8080).
  - `serviceaccount.yaml` — Workload Identity 애노테이션 자리(`azure.workload.identity/client-id`).
  - `kagent-modelconfig.yaml` — kagent `ModelConfig`(Azure OpenAI, WI 인증). 엔드포인트 플레이스홀더.
  - `kagent-toolserver.yaml` — kagent `ToolServer` CR → 위 Service(HTTP/SSE) 참조.
  - `kagent-agent.yaml` — kagent `Agent` CR: ModelConfig 참조 + ToolServer의 `run_engagement` 툴 바인딩
    + 시스템 프롬프트(판정권 없음, 실행·요약만 명시).
  - `kustomization.yaml`.
- `deploy/overlays/aks/`:
  - `kustomization.yaml` — `images: [{name: app, newName: <ACR>.azurecr.io/fried-pollack-ai,
    newTag: <SHA>}]` + WI client-id patch + 네임스페이스.
- **검증**: `kustomize build deploy/overlays/aks` 렌더 성공, `kubectl apply --dry-run=server`.

### Phase 5 — ArgoCD app-of-apps (`deploy/argocd`)
- `root-app.yaml` — app-of-apps 루트(이 repo `deploy/argocd/apps` 추적).
- `apps/kagent-platform.yaml` — kagent controller/CRD 설치 App(공식 kagent Helm/manifest source).
- `apps/fried-pollack.yaml` — 우리 앱 App(`deploy/overlays/aks` 추적, auto-sync + prune + selfHeal).
- Sync wave 순서: kagent 플랫폼(wave 0, CRD 먼저) → 앱(wave 1).
- **검증**: `kubectl apply -f deploy/argocd/root-app.yaml` → ArgoCD가 두 App sync → 파드 Ready →
  kagent Agent가 `run_engagement` 호출 성공.

### Phase 6 — CI 확장 (이미지 빌드 + GitOps bump)
- `.github/workflows/ci.yml`에 job 추가(main push 시, 기존 test job 통과 후):
  - `az login`(OIDC federated) → ACR 로그인 → `docker build/push tag=${GITHUB_SHA}`.
  - `kustomize edit set image app=<ACR>.azurecr.io/fried-pollack-ai:${GITHUB_SHA}` in overlays/aks →
    commit → push(`[skip ci]`). ArgoCD가 이 커밋 sync.
- **검증**: main push → 이미지 ACR 등장 + overlay newTag bump 커밋 + ArgoCD 새 리비전 sync.

### Phase 7 — 문서
- `deploy/README.md` — 부트스트랩 런북: WI federation 설정(`az` 명령), `az aks update --attach-acr`,
  `Cognitive Services OpenAI User` 롤 부여, ArgoCD root-app 적용 순서, 플레이스홀더 치환 목록.
- `ARCHITECTURE.md`/`README.md`에 배포 섹션 링크(선택).

---

## 플레이스홀더 (실값 나중 치환)
`<ACR_NAME>` · `<AZURE_OPENAI_ENDPOINT>` · `<AZURE_OPENAI_DEPLOYMENT>` · `<SUBSCRIPTION_ID>` ·
`<RESOURCE_GROUP>` · `<AKS_NAME>` · `<MANAGED_IDENTITY_CLIENT_ID>` · `<TENANT_ID>` · `<NAMESPACE>`

## 범위 밖 (명시)
- 실 SITL/Gazebo/HIL 클러스터 구동 (별도 인가 물리 레인지에서 수동).
- 실 SOC/Sentinel 폐루프 연동.
- 비동기 HITL 승인 채널(Slack/웹훅).
- PVC/Blob 산출물 영속(stateless inline 반환으로 대체).
- 멀티 환경(dev/stg/prod) 오버레이 — 지금 aks 단일.

## 안전 회귀 가드 (마이그레이션이 깨면 안 되는 것)
- `range_mode=container`에서 물리 비가역 실집행 = 0 (게이트 도달만).
- MCP 서버가 `sitl|hil|live` 요청 거부.
- 182 tests green + check_gates G1~G4 통과 유지.
- kagent LLM이 원자 액션 스텝 선택 불가(coarse 툴만 노출).

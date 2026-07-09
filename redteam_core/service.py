"""service.py — engagement 실행 공용 서비스 레이어.

CLI(`run.py`)와 MCP 서버(`mcp_server.py`)가 **같은 함수**를 호출한다(로직 중복 0).
안전 게이트·오라클·HITL·결정론 파이프라인은 전부 이 아래(redteam_core)에 그대로 있고,
이 레이어는 그것을 감싸 호출·결과 정형화만 한다. 판정권은 여기에도 없다.

- `run_engagement(...)`     : 파이프라인 실행 → 전체 state dict 반환(기존 run.py 계약 그대로).
- `build_soc_payload(state)`: ③ 브릿지 산출(UAV*_CL 행 + SOC Alert)을 파일 대신 **인라인 dict**로.
- `engagement_report(...)`  : MCP/서비스용 JSON-직렬화 가능 산출(report + 선택 soc + backend).
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from redteam_core.bridge import rows_to_alert, tap_from_audit
from redteam_core.engagement.gate import load_gate
from redteam_core.learning import (new_persistent_experience_gates,
                                    new_persistent_target_gate)
from redteam_core.logging_util import get_logger
from redteam_core.session import build_initial_state
from redteam_core.settings import settings_summary
from redteam_core.tools.range_factory import make_range

log = get_logger("service")

DEFAULT_PROFILE = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                               "engagement_profile.yaml")


def demo_approver(ctx):
    """HITL 콜백: 물리 비가역은 인간 전용 → 자동대응 보류(안전). 그 외 승인.

    ctx = hitl_gate의 _hitl_context(dict). stdlib·LangGraph interrupt 양쪽에서 동일 계약.
    헤드리스(파드) 실행에선 인간 부재 → 물리 비가역은 fail-closed(denied)로 게이트 도달만 기록.
    """
    return "denied" if ctx.get("physical_irreversible") else "approved"


def _persistent_gates(learning_dir: str):
    """디스크 백엔드 학습 게이트 쌍 — 여러 run에 걸쳐 자기개선 누적(2a seam 배선)."""
    os.makedirs(learning_dir, exist_ok=True)
    eg = new_persistent_experience_gates(os.path.join(learning_dir, "experience.json"))
    tg = new_persistent_target_gate(os.path.join(learning_dir, "target_profile.json"))
    return eg, tg


def run_engagement(profile_path: str, range_mode: str = None, hardened: bool = False,
                   apply_egress: bool = False, persist_learning: str = None) -> dict:
    """engagement 파이프라인 1회 실행 → 전체 state dict 반환.

    기존 run.py:run_engagement 와 동일 계약(하위호환). CLI·MCP 공용 진입점.
    """
    gate, profile = load_gate(profile_path, apply_egress=apply_egress)
    if range_mode:
        profile.setdefault("engagement", {})["range_mode"] = range_mode
    log.info("engagement 시작 name=%r range_mode=%s hardened=%s settings=%s",
             profile.get("engagement", {}).get("name"),
             profile.get("engagement", {}).get("range_mode"), hardened, settings_summary())
    eg, tg = (_persistent_gates(persist_learning) if persist_learning else (None, None))
    if persist_learning:
        log.info("학습 영속 활성 dir=%s", persist_learning)
    state = build_initial_state(profile, gate, make_range(profile, hardened=hardened),
                                demo_approver, experience_gate=eg, target_gate=tg)
    from redteam_core.graph.build import build_graph  # 지연 import(선택적 langgraph seam)
    graph = build_graph()                       # 기본 LangGraph(interrupt HITL), 미설치면 stdlib
    backend = type(graph).__name__
    final = graph.invoke(state)
    try:
        final["_backend"] = backend
    except Exception:
        pass
    return final


def build_soc_payload(state: dict) -> dict:
    """③ 브릿지: 관측 트래픽 → UAV*_CL 행 + SOC Alert. 파일 안 씀, 인라인 dict 반환(A8)."""
    ts = datetime.now(timezone.utc).isoformat()
    rows = tap_from_audit(state["audit_log"], state["profile"], ts=ts)
    alert = rows_to_alert(rows, state["profile"],
                          alert_id="rt-" + ts.replace(":", "").replace("-", "")[:15])
    return {"rows": rows, "alert": alert}


def engagement_report(range_mode: str = "container", hardened: bool = False,
                      emit_soc: bool = False, profile_path: str = None) -> dict:
    """MCP/서비스용 JSON-직렬화 가능 산출.

    stateless: 파일 안 씀. report + (선택) soc 인라인 + backend 라벨만 반환.
    range_mode 검증은 호출측(mcp_server)에서 — 여기선 받은 값 그대로 전달.
    """
    state = run_engagement(profile_path or DEFAULT_PROFILE, range_mode=range_mode,
                           hardened=hardened)
    out = {
        "report": state["report"],
        "backend": state.get("_backend"),
        "range_mode": state["profile"].get("engagement", {}).get("range_mode"),
    }
    if emit_soc:
        out["soc"] = build_soc_payload(state)
    return out

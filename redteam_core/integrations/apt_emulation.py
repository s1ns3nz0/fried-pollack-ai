"""APT 에뮬레이션 — 위협행위자의 '순서 있는 킬체인 패턴' 참조·실행 (§O 확장).

TI(actor→시나리오 집합)를 넘어, 각 APT 의 특징적 킬체인 순서(emulation_chain)를
참조해 "그 APT 로서" 캠페인을 실행하고 blue 가 어디서 잡는지 산출한다.
  - APT_EMULATION: ATT&CK Groups 기반 순서 킬체인 시드(오프라인).
  - CTID seam: env CTID_PLAN_URL 지정 시 MITRE CTID Adversary Emulation Library pull.
  - next_ttp_by_pattern: 패턴 기반 다음 TTP 제안(planner 참조, LLM 있으면 정교화).
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .http_json import get_json

# APT → 순서 있는 킬체인 패턴(확장). ATT&CK Group 운용 특성 반영.
# 정찰(S97)로 시작해 7단계 킬체인을 최대한 커버.
APT_EMULATION = {
    # ── 기존 5개(확장) ──
    "Sandworm (G0034)": ["S97", "S33", "S38", "S4", "S5", "S51", "S52"],   # OT 파괴
    "APT28 (G0007)": ["S97", "S34", "S35", "S37", "S79", "S3", "S92"],      # 방산 espionage
    "Volt Typhoon (G1017)": ["S97", "S34", "S39", "S22", "S21", "S17"],       # LOTL 인프라
    "EW Threat Cluster": ["S1", "S23", "S24", "S18", "S19", "S20"],           # 전자전 확전
    "AML Adversary (ATLAS)": ["S89", "S88", "S90", "S91", "S100"],             # AI 계층(전 단계 미배포)
    # ── 신규 3개(한국 방산 관련 DPRK + 항공우주) ──
    "Lazarus (G0032)": ["S97", "S34", "S33", "S3", "S51", "S52"],            # DPRK 파괴·탈취
    "Kimsuky (G0094)": ["S97", "S34", "S35", "S36", "S92"],                  # DPRK ROK 방산 espionage
    "APT33 (G0064)": ["S97", "S33", "S1", "S3"],                            # 항공우주 표적
}

# campaigns 에 없는 시나리오의 탐지상태 — **배포된 S1~S7 룰 기준**.
# 배포룰 존재=탐지(True) / 미배포(S88·S89·군집·AI계열)=사각(None).
_EXTRA_STATIC = {
    "S17": True, "S18": True, "S2": True, "S19": True, "S35": True, "S20": True,
    "S4": True, "S38": True, "S51": True, "S21": True, "S52": True,
    "S22": True, "S39": True,
    "S88": None, "S89": None,                       # 미배포 = 사각지대
}


def _exec(sid: str) -> Tuple[bool, Optional[bool]]:
    if sid in _EXTRA_STATIC:
        return True, _EXTRA_STATIC[sid]
    from ..campaigns.chains import _exec_scenario
    return _exec_scenario(sid)


# ── CTID Adversary Emulation Library seam ────────────────────────────────────
def ctid_available() -> bool:
    return bool(os.environ.get("CTID_PLAN_URL", ""))


def status() -> dict:
    return {"available": ctid_available(),
            "ctid_url": os.environ.get("CTID_PLAN_URL", "") or None,
            "mode": "real" if ctid_available() else "fallback",
            "apt_profiles": len(APT_EMULATION)}


def emulation_plan(actor: str) -> List[str]:
    """APT 킬체인 순서. CTID 연동 시 실 플랜(본선), 아니면 시드."""
    if ctid_available():
        return ctid_plan_detail(actor)["chain"]
    return list(APT_EMULATION.get(actor, []))


def _parse_ctid_plan(data, actor: str) -> tuple:
    """CTID JSON manifest → 시나리오 chain. 지원 형태:

      1) actor-keyed : {"<actor>": ["S97", "S34", ...]}
      2) plans array : {"plans": [{"actor": "<actor>", "chain": ["S97", ...]}]}

    반환 (chain, warning). malformed/미발견 면 ([], warning) 로 상위가 시드 폴백.
    """
    if not isinstance(data, dict):
        return [], "CTID response is not a JSON object"
    if isinstance(data.get(actor), list):                       # 형태 1
        return [str(x) for x in data[actor]], None
    plans = data.get("plans")
    if isinstance(plans, list):                                 # 형태 2
        for row in plans:
            if isinstance(row, dict) and row.get("actor") == actor:
                chain = row.get("chain")
                if isinstance(chain, list):
                    return [str(x) for x in chain], None
                return [], f"CTID plan for {actor!r} has non-list 'chain'"
        return [], f"CTID plan for {actor!r} not found in 'plans'"
    return [], f"CTID manifest missing actor key {actor!r} or 'plans' array"


def ctid_plan_detail(actor: str) -> dict:
    """실 CTID pull + schema 검증. {chain, source, warning} 반환(fail-soft, 시드 폴백)."""
    seed = list(APT_EMULATION.get(actor, []))
    if not ctid_available():
        return {"chain": seed, "source": "seed", "warning": None}
    data = get_json(os.environ["CTID_PLAN_URL"])
    if isinstance(data, dict) and set(data) == {"error"}:       # http_json transport/status 오류
        return {"chain": seed, "source": "seed_fallback", "warning": f"CTID fetch error: {data['error']}"}
    chain, warn = _parse_ctid_plan(data, actor)
    if not chain:
        return {"chain": seed, "source": "seed_fallback", "warning": warn}
    return {"chain": chain, "source": "ctid", "warning": None}


# ── APT 에뮬레이션 실행 ───────────────────────────────────────────────────────
@dataclass
class AptEmulationResult:
    actor: str
    verdict: str                        # stealthy | detected
    steps: List[Tuple[str, Optional[bool]]] = field(default_factory=list)  # (sid, detected)
    detected_at: List[str] = field(default_factory=list)


def run_apt_emulation(actor: str) -> AptEmulationResult:
    steps: List[Tuple[str, Optional[bool]]] = []
    detected_at: List[str] = []
    for sid in emulation_plan(actor):
        _achieved, detected = _exec(sid)
        steps.append((sid, detected))
        if detected is True:
            detected_at.append(sid)
    verdict = "detected" if detected_at else "stealthy"
    return AptEmulationResult(actor, verdict, steps, detected_at)


# ── LLM 플래너 패턴 참조 ──────────────────────────────────────────────────────
def next_ttp_by_pattern(actor: str, completed: Optional[List[str]] = None) -> Optional[str]:
    """APT 패턴상 다음 TTP(미완료 첫 단계). LLM 있으면 정교화(opt-in)."""
    completed = set(completed or [])
    for sid in emulation_plan(actor):
        if sid not in completed:
            return sid                  # 결정론: 패턴 순서 준수
    return None

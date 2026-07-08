"""툴 자동검색 트리거 — 블로커 자동연동·커버리지 갭 배치·자율루프 훅.

adaptive_engage 가 막히면 해당 목표의 검색어로 GitHub 도구를 찾아 제안한다.
"""
from __future__ import annotations

from typing import List

from .github import search_github

# 목표/기법 → GitHub 검색어
OBJECTIVE_QUERY = {
    "weapon_effect": "mavlink weapon arm injection uav",
    "nav_denial": "gnss gps spoof drone", "nav_jam_denial": "gps jammer sdr",
    "c2_jam_denial": "wifi jammer sdr", "soc_llm_inject": "llm prompt injection redteam",
    "model_extraction": "llm model extraction garak", "recon_access": "drone credential bruteforce",
    "data_exfiltration": "exfiltration tunnel drone", "crypto_key_exfil": "mavlink signing key extract",
    "wifi_deauth": "wifi deauth aircrack drone", "wifi_evil_twin": "evil twin rogue ap drone",
    "rc_link_hijack": "rc frsky elrs bind hijack", "rc_override": "rc override mavlink",
    "dshot_motor": "dshot esc motor betaflight", "antiforensics": "drone forensics anti log wipe",
}


def suggest_on_block(objective: str, verdict: str, limit: int = 3) -> dict:
    """blocked/미달 시에만 GitHub 도구 제안(진행 어려움 트리거)."""
    if verdict == "achieved":
        return {"objective": objective, "triggered": False, "tools": []}
    q = OBJECTIVE_QUERY.get(objective, objective.replace("_", " "))
    return {"objective": objective, "triggered": True, "query": q,
            "tools": search_github(q, limit)}


def discover_for_objective(objective: str, limit: int = 3) -> dict:
    """목표를 교전 → 막히면 자동 검색."""
    from ..assessment import adaptive_engage
    r = adaptive_engage(objective)
    return {**suggest_on_block(objective, r.verdict, limit), "verdict": r.verdict}


def discover_for_gaps(limit: int = 2) -> List[dict]:
    """KPI 사각지대/차단 목표 배치 → 각 목표에 도구 탐색."""
    from ..assessment import OBJECTIVES, adaptive_engage
    out = []
    for obj in OBJECTIVES:
        r = adaptive_engage(obj)
        # 차단(무장) 또는 사각지대(미탐지) = 방어/공격 갭 → 도구 제안 후보
        stuck = r.verdict != "achieved" or (r.trace and r.trace[-1][2].detected is None)
        if stuck and obj in OBJECTIVE_QUERY:
            out.append({"objective": obj, "verdict": r.verdict,
                        "tools": search_github(OBJECTIVE_QUERY[obj], limit)})
    return out

"""레드팀 기법/도구 카탈로그 + 회피 심화 — ired.team / A-poc/RedTeam-Tools.

ATT&CK 기법 → 실 오픈소스 도구 → 우리 시나리오 매핑(발표 근거·정당성) +
방어 회피 기법 카탈로그(§I 소모/§H 기만 심화).
"""
from __future__ import annotations

from typing import List

# ATT&CK 기법 → (실 도구, 우리 시나리오)
TECHNIQUE_TOOLS = [
    {"tactic": "Recon", "technique": "T1595", "tools": ["nmap", "masscan"], "scenario": "S97"},
    {"tactic": "Initial Access", "technique": "T1078", "tools": ["hydra", "medusa"], "scenario": "S34"},
    {"tactic": "Delivery", "technique": "T1195", "tools": ["cosign", "syft"], "scenario": "S33"},
    {"tactic": "Lateral Movement", "technique": "TA0008", "tools": ["impacket", "crackmapexec"], "scenario": "S21"},
    {"tactic": "C2", "technique": "TA0011", "tools": ["Sliver", "Mythic", "Caldera"], "scenario": "S94"},
    {"tactic": "Exfiltration", "technique": "T1041", "tools": ["dnscat2", "chisel"], "scenario": "S94"},
    {"tactic": "AI/ML", "technique": "AML.T0051", "tools": ["PyRIT", "Garak"], "scenario": "S90"},
    {"tactic": "RF/EW", "technique": "T1557", "tools": ["gps-sdr-sim", "gr-frsky", "bladeRF"], "scenario": "S29"},
    {"tactic": "Defense Evasion", "technique": "T1070", "tools": ["timestomp", "shred"], "scenario": "S40"},
]

# 방어 회피 기법(§I 소모/§H 기만 심화)
EVASION_TECHNIQUES = [
    {"id": "obfuscation", "technique": "T1027", "desc": "페이로드 난독화(base64·homoglyph·zwsp) — §N payloads 적용"},
    {"id": "timestomp", "technique": "T1070.006", "desc": "타임스탬프 변조 — 로그 상관 교란"},
    {"id": "low_and_slow", "technique": "—", "desc": "임계 아래 누적 — §R tempo 적용"},
    {"id": "signature_rotation", "technique": "—", "desc": "탐지 TTP 소진 시 시그니처 회전 — §I sustainment"},
    {"id": "decoy_saturation", "technique": "—", "desc": "미끼 포화로 실공격 은폐 — §H MILDEC"},
]


def tools_for_scenario(scenario_id: str) -> List[dict]:
    return [t for t in TECHNIQUE_TOOLS if t["scenario"] == scenario_id]

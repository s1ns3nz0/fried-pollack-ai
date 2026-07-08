"""EMSO 교전 — EA 액션을 물리 지오메트리·스펙트럼으로 계획하고 효과를 산출.

RoE 게이트(§B)가 JCEOI 승인을 강제하므로, 여기서는 물리효과와 telemetry_hint 만
낸다. 산출은 §A BDA 로 연결(gnss_spoof→S1, jam→S2 관측면).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .effects import EwEffect, gnss_spoof_effect, jam_effect
from .rf import band_for


@dataclass
class EmsoOutcome:
    action: str
    ea_type: str                 # JP 3-85 EW 구분: 전자공격(EA)
    band: Optional[str]
    freq_mhz: float
    effect: EwEffect
    doctrine_refs: list = field(default_factory=lambda: ["JP 3-85 JEMSO (EA)", "JCEOI"])


# 액션 → 기본 표적 주파수(MHz)
_ACTION_FREQ = {
    "gnss_spoof": 1575.42,       # GPS L1
    "jam": 2437.0,               # 2.4GHz C2 기본
}


def plan_emso(action: str, geometry: dict) -> EmsoOutcome:
    """geometry:
        gnss_spoof → {spoof_eirp_dbm, spoof_dist_m}
        jam        → {jammer_eirp_dbm, jammer_dist_m, signal_eirp_dbm, signal_dist_m}
    """
    freq = float(geometry.get("freq_mhz", _ACTION_FREQ.get(action, 2437.0)))
    band = band_for(freq)
    if action == "gnss_spoof":
        eff = gnss_spoof_effect(geometry["spoof_eirp_dbm"], geometry["spoof_dist_m"], freq)
    elif action == "jam":
        eff = jam_effect(freq, geometry["jammer_eirp_dbm"], geometry["jammer_dist_m"],
                         geometry.get("signal_eirp_dbm", 20.0), geometry.get("signal_dist_m", 200.0))
    else:
        raise ValueError(f"EMSO 대상 아님: {action}")
    return EmsoOutcome(action=action, ea_type="EA", band=band.name if band else None,
                       freq_mhz=freq, effect=eff)

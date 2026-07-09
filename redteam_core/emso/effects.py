"""전자공격(EA) 효과 모델 — 재밍(J/S)·GNSS 스푸핑(포획).

결정론. 산출 telemetry_hint 는 §A BDA 로 흘러 blue 룰 판정(S1/S17)에 쓰인다.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .rf import j_to_s_db, rssi_dbm

# 재밍 번스루: J/S 가 이 값 이상이면 링크 차단(수신단 SINR 붕괴).
BURNTHROUGH_JS_DB = 6.0
# 정품 GNSS L1 수신전력(약 -130 dBm). 스푸핑이 이보다 우세해야 수신기 포획.
AUTH_GNSS_DBM = -130.0
GNSS_CAPTURE_MARGIN_DB = 3.0
# 포획 마진(dB) → EKF PosHorizVariance 강도 환산계수(대략).
_VAR_PER_DB = 0.05


@dataclass
class EwEffect:
    ea_type: str                 # "jam" | "gnss_spoof"
    achieved: bool               # 효과 달성 여부(링크 차단/수신기 포획)
    metric_db: float             # J/S(jam) 또는 포획 마진(spoof), dB
    telemetry_hint: dict = field(default_factory=dict)   # §A BDA 입력(table/field/value)
    note: str = ""


def jam_effect(freq_mhz: float, jammer_eirp_dbm: float, jammer_dist_m: float,
               signal_eirp_dbm: float, signal_dist_m: float, n: float = 2.2) -> EwEffect:
    js = j_to_s_db(jammer_eirp_dbm, jammer_dist_m, signal_eirp_dbm, signal_dist_m, freq_mhz, n)
    denied = js >= BURNTHROUGH_JS_DB
    # 재밍 시 표적 수신 RSSI 는 실제로 잡음바닥에 묻힘 → blue S17(RSSI≤-20, loss↑) 관측면.
    victim_rssi = rssi_dbm(signal_eirp_dbm, signal_dist_m, freq_mhz, n) - max(js, 0.0)
    loss_pct = min(100.0, max(0.0, (js) * 5.0)) if denied else 0.0
    return EwEffect(
        ea_type="jam", achieved=denied, metric_db=round(js, 2),
        telemetry_hint={"table": "UAVDatalink_CL", "c2_rssi_dbm": round(victim_rssi, 1),
                        "packet_loss_pct": round(loss_pct, 1)},
        note=f"J/S={js:.1f}dB {'≥' if denied else '<'} 번스루 {BURNTHROUGH_JS_DB}dB")


def gnss_spoof_effect(spoof_eirp_dbm: float, spoof_dist_m: float,
                      freq_mhz: float = 1575.42, n: float = 2.2) -> EwEffect:
    rssi = rssi_dbm(spoof_eirp_dbm, spoof_dist_m, freq_mhz, n)
    margin = rssi - AUTH_GNSS_DBM
    captured = margin >= GNSS_CAPTURE_MARGIN_DB
    pos_var = round(max(0.0, margin) * _VAR_PER_DB, 4) if captured else 0.0
    return EwEffect(
        ea_type="gnss_spoof", achieved=captured, metric_db=round(margin, 2),
        # §A BDA: PosHorizVariance 강도 → blue S1 룰(동적 게이트 ≈0.0238) 판정.
        telemetry_hint={"table": "UAVTelemetry_CL", "pos_horiz_variance": pos_var},
        note=f"포획마진={margin:.1f}dB {'≥' if captured else '<'} {GNSS_CAPTURE_MARGIN_DB}dB")

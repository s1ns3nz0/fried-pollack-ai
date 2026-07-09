"""비행로그 분석 오라클 — 공격효과를 로그로 검증 (Analytics-Agent 전이).

비행로그(실 DVD/SITL tlog·dataflash 또는 합성)를 분석해 공격효과 시그니처를 판정:
위치 이탈·고도 손실·자세 불안정·모드 변경. BDA 오라클(§A)을 로그 기반으로 강화.
"""
from __future__ import annotations

from typing import List, Optional


def analyze_flightlog(log: List[dict]) -> dict:
    """비행로그 샘플 리스트 분석 → 공격효과 판정.

    각 샘플: {pos_dev_m, alt_err_m, attitude_var, mode}. 임계 초과 시 효과 확인.
    """
    if not log:
        return {"effect": False, "signatures": [], "note": "로그 없음"}
    max_pos = max(s.get("pos_dev_m", 0.0) for s in log)
    max_alt = max(abs(s.get("alt_err_m", 0.0)) for s in log)
    max_att = max(s.get("attitude_var", 0.0) for s in log)
    modes = {s.get("mode") for s in log if s.get("mode")}
    sigs = []
    if max_pos >= 50:
        sigs.append(f"위치 이탈 {max_pos:.0f}m")
    if max_alt >= 20:
        sigs.append(f"고도 오차 {max_alt:.0f}m")
    if max_att >= 0.5:
        sigs.append(f"자세 불안정 var={max_att:.2f}")
    if "RTL" in modes or "LAND" in modes:
        sigs.append(f"failsafe 모드전환 {modes & {'RTL', 'LAND'}}")
    return {"effect": bool(sigs), "signatures": sigs,
            "max_pos_dev_m": round(max_pos, 1), "max_alt_err_m": round(max_alt, 1),
            "note": "공격효과 확인" if sigs else "정상 비행(효과 미확인)"}

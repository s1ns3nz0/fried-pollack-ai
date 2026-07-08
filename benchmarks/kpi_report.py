#!/usr/bin/env python3
"""KPI 대시보드 — 1~3순위 (방어공백·잔존·임계보정).

    python benchmarks/kpi_report.py

기존 층 원자값을 집계해 레드팀 KPI를 한 화면에 출력. 결정론·무의존(Tier-0).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from redteam_core.kpi import (                                     # noqa: E402
    calibration, coverage_gap, dwell,
    mitre_coverage, reattack_efficiency, roe_compliance,
)


def main() -> None:
    print("=== fried-pollack-ai · 레드팀 KPI 대시보드 (1~6순위) ===\n")

    cg = coverage_gap()
    print("① 방어 공백 지표 (Blue Coverage Gap)")
    print(f"   사각지대율      : {cg['blind_spot_ratio']*100:.0f}%  "
          f"({len(cg['blind_spots'])}/{cg['total_scenarios']}) → {', '.join(cg['blind_spots'])}")
    print(f"   회피가능율      : {cg['evadable_ratio']*100:.0f}%  → {', '.join(cg['evadable'])}")
    print(f"   은밀관통 캠페인 : {cg['stealthy_campaign_ratio']*100:.0f}%  "
          f"({len(cg['stealthy_campaigns'])}/{cg['total_campaigns']}) → {', '.join(cg['stealthy_campaigns'])}")

    print("\n② 공격자 잔존 / 탐지까지 단계 (dwell)")
    for cid, steps in dwell().items():
        print(f"   {cid:<5}: {'∞ (미탐지)' if steps is None else f'{steps}단계에서 탐지'}")

    print("\n③ 임계 실측 보정 기여 (Calibration)")
    print(f"   {'룰':<28}{'param':<20}{'실측경계':>9}{'가상값':>9}{'오차':>9}")
    for r in calibration():
        print(f"   {r['rule']:<28}{r['param']:<20}"
              f"{_f(r['measured_boundary']):>9}{_f(r['blue_assumed']):>9}{_f(r['abs_error']):>9}")

    mc = mitre_coverage()
    print("\n④ 시나리오 MITRE 커버리지")
    print(f"   총 기법 {mc['total_techniques']}개 · 프레임워크 {mc['by_framework']} · "
          f"D3FEND 사각 {mc['d3fend_blind_ratio']*100:.0f}%({len(mc['d3fend_blind_actions'])}액션)")

    rc = roe_compliance()
    print("\n⑤ RoE 교리 준수 분포 (액션 " + str(rc['evaluated']) + "개)")
    print(f"   판정 {rc['verdicts']}")
    print(f"   요구권한 {rc['required_authority']}  ·  CDE {rc['cde_tier']}")

    re_ = reattack_efficiency()
    print("\n⑥ 재타격 효율")
    print(f"   달성 {re_['achieved_objectives']}/{re_['total_objectives']} 목표 · "
          f"평균 시도 {re_['avg_attempts_to_achieve']}회/달성")

    print("\n요약: 사각지대(EW·AI)·완전 은밀 캠페인(C9)이 방어 최우선. "
          "RoE는 EW/무장을 교리대로 차단(JCEOI·ConOps). 임계보정은 watchlist 갱신 반영.")


def _f(x) -> str:
    return "-" if x is None else f"{x:g}"


if __name__ == "__main__":
    main()

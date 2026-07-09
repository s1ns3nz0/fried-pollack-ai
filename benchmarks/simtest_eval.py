#!/usr/bin/env python3
"""simtest §Z 데모 — 센서 폴트인젝션·환경 증폭·인시던트KB·로그 오라클.

    python benchmarks/simtest_eval.py

AutoSimTestFramework 영감. 결정론·무의존.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from redteam_core.simtest import (                                # noqa: E402
    ENVIRONMENTS, SENSOR_SCENARIOS, amplify, analyze_flightlog,
    run_sensor_fault, scenarios_from_incidents,
)


def main() -> None:
    print("=== fried-pollack-ai · simtest §Z (AutoSim 영감) ===\n")

    print("① 다중센서 폴트인젝션 (S9~S12, 점진 주입 ramp=0.1)")
    for sid, m in SENSOR_SCENARIOS.items():
        r = run_sensor_fault(sid, ramp_rate=0.1)
        tag = "🥷 은밀 수용" if r.stealthy else "🔴 EKF 거부"
        print(f"   {sid} {m['name']:<22} {tag} → {r.effect}")

    print("\n② 환경 공격 증폭 (GNSS 스푸핑 기준)")
    for env in ("clear", "urban_canyon", "high_wind", "storm"):
        a = amplify("gnss_spoof", env)
        print(f"   {env:<14} 효과 ×{a['gain']:<4} 은폐 {a['detection_masking']:.0%}  {a['note']}")

    print("\n③ 인시던트-KB → 근거화 시나리오 (S-Agent)")
    for s in scenarios_from_incidents()[:5]:
        print(f"   {s['from_incident']:<26}→ {s['scenario']:<4} ({s['provenance']})")

    print("\n④ 비행로그 분석 오라클 (Analytics-Agent)")
    log = [{"pos_dev_m": 120, "alt_err_m": 35, "attitude_var": 0.7, "mode": "RTL"}]
    o = analyze_flightlog(log)
    print(f"   효과={o['effect']} · 시그니처={o['signatures']}")

    print("\n핵심: 센서 계층(S9~S12)은 EKF 오염 신규 공격면·전부 사각지대.")
    print("      환경이 효과를 증폭(도심협곡 GNSS ×1.6). 인시던트-KB가 시나리오 근거화.")


if __name__ == "__main__":
    main()

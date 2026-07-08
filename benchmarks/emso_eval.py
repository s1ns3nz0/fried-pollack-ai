#!/usr/bin/env python3
"""EMSO(전자전) 데모 — 고도화 §C, JP 3-85 JEMSO.

    python benchmarks/emso_eval.py

전자공격(EA) 물리효과 → telemetry 강도 → §A BDA(blue 탐지) → §B RoE(JCEOI) 까지
한 화면에 보여준다. 결정론·무의존(Tier-0).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from redteam_core.emso import plan_emso                    # noqa: E402
from redteam_core.assessment import assess_action          # noqa: E402
from redteam_core.roe import evaluate_roe, load_roe_profile  # noqa: E402

_ROOT = Path(__file__).resolve().parent.parent
_GROUND = {"armed": False, "in_flight": False, "alt_rel": 0.0, "mode": "GUIDED"}

CASES = [
    ("gnss_spoof", {"spoof_eirp_dbm": 20, "spoof_dist_m": 100},  "근접 고출력 스푸핑"),
    ("gnss_spoof", {"spoof_eirp_dbm": -20, "spoof_dist_m": 20000}, "원거리 저출력 스푸핑"),
    ("jam",        {"jammer_eirp_dbm": 40, "jammer_dist_m": 100}, "근접 고출력 재밍"),
    ("jam",        {"jammer_eirp_dbm": 10, "jammer_dist_m": 3000}, "원거리 저출력 재밍"),
]


def main() -> None:
    prof = load_roe_profile(str(_ROOT / "engagement_roe.yaml"))
    jceoi = prof.get("spectrum", {}).get("jceoi_deconflicted")
    print("=== fried-pollack-ai · EMSO(전자전) — 고도화 §C (JP 3-85) ===")
    print(f"EA 물리효과 → §A BDA(blue 탐지) → §B RoE(JCEOI 승인={jceoi})\n")
    print(f"  {'시나리오':<20}{'대역':<9}{'metric(dB)':<12}{'효과':<8}{'blue탐지':<10}{'RoE'}")
    for action, geom, label in CASES:
        o = plan_emso(action, geom)
        eff = o.effect
        # §A BDA: gnss_spoof 는 PosVar 강도로 blue S1 판정.
        det = "-"
        if action == "gnss_spoof":
            bda = assess_action("gnss_spoof", intensity=eff.telemetry_hint["pos_horiz_variance"])
            det = {True: "🔴 탐지", False: "🟢 회피", None: "-"}[bda.detected]
        # §B RoE: EA 는 JCEOI 미승인이면 BLOCKED.
        roe = evaluate_roe(action, _GROUND, {"sysid": 42, "pid": True}, prof).verdict.value
        achieved = "달성" if eff.achieved else "미달"
        print(f"  {label:<20}{str(o.band):<9}{eff.metric_db:<12}{achieved:<8}{det:<10}{roe}")

    print("\n해석: 물리(J/S·포획마진)로 효과 달성 판정 → 산출 강도가 §A BDA 로 흘러 blue 탐지 결정.")
    print("      단, §B RoE 가 JCEOI 미승인 EA 를 사전 차단(BLOCKED) — 교리상 스펙트럼 데컨플릭션 필수.")


if __name__ == "__main__":
    main()

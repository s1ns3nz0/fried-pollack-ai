#!/usr/bin/env python3
"""폐루프 전투평가(BDA) 실행기 — 고도화 §A 데모.

    python benchmarks/closed_loop_eval.py

동언님 코어를 감싸는 전투평가 하네스. 킬체인 액션 시퀀스를 폐루프로 돌려
단계별 탐지/회피, 그리고 blue 가상값 임계의 실측 보정(calibration)을 출력한다.
결정론·무의존(Tier-0) — LLM/네트워크/SITL 불필요.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from redteam_core.assessment import run_closed_loop      # noqa: E402


# C2 유사 cross-domain 킬체인 + 범주형 대조. intensity 는 blue 임계 위에서 시작.
KILLCHAIN = [
    {"action": "active_scan", "intensity": 20},        # S34: FailCount 20 → 탐지
    {"action": "spoof_telemetry", "intensity": 16},    # S20: unsigned 16 → 탐지
    {"action": "gnss_spoof", "intensity": 0.8},        # S1: PosVar 0.8 → 탐지(게이트 0.0238)
    {"action": "force_arm"},                            # S3: 범주형(회피 불가)
    {"action": "unauthorized_command"},                 # S79: 범주형(회피 불가)
]


def main() -> None:
    print("=== fried-pollack-ai · 폐루프 전투평가(BDA) — 고도화 §A ===")
    print("교리: JP 3-60 ⑥ 전투평가를 방어자(DCO) 반응까지 확장 · D8 준수(blue 룰=공유 산출물)\n")

    res = run_closed_loop(KILLCHAIN)

    print("── 킬체인 관측(BDA) ──")
    for o in res.steps:
        mark = {True: "🔴 탐지", False: "🟢 회피", None: "⚪ 사각"}[o.detected]
        extra = f" intensity={o.intensity}" if o.intensity is not None else " (범주형)"
        print(f"  {o.action:<20} → {o.rule_id or '-':<28} {mark}{extra}")

    print(f"\n최종 체인 회피(전 단계 미탐지): {res.evaded_chain}")

    print("\n── 폐루프 부산물: blue 가상값 임계 실측 보정 ──")
    print(f"  {'룰':<28}{'param':<22}{'회피≤':>9}{'탐지≥':>9}{'경계~':>9}{'blue가상값':>11}")
    for c in res.calibrations:
        print(f"  {c.rule_id:<28}{c.threshold_param:<22}"
              f"{_f(c.evaded_at):>9}{_f(c.detected_at):>9}{_f(c.boundary):>9}{_f(c.blue_assumed):>11}")

    print("\n해석: 연속 룰은 red 가 강도를 낮춰 탐지 경계를 실측 → blue 가상값을 보정.")
    print("      범주형 룰(S3/S79)은 강도로 회피 불가 = 견고 → red 는 TTP 전환 필요(교리: 재계획).")


def _f(x) -> str:
    return "-" if x is None else f"{x:g}"


if __name__ == "__main__":
    main()

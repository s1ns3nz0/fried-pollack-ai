#!/usr/bin/env python3
"""MILDEC 데모 — 고도화 §H (Information / JP 3-13.4).

    python benchmarks/deception_eval.py

미끼로 SOC 를 포화시켜 진짜 공격을 은폐. 결정론·무의존(Tier-0).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from redteam_core.deception import run_deception, SATURATION_THRESHOLD   # noqa: E402


def _run(n):
    decoys = [{"action": "active_scan", "intensity": 20} for _ in range(n)]
    return run_deception("force_arm", decoys)


def main() -> None:
    print("=== fried-pollack-ai · 군사기만(MILDEC) — 고도화 §H (JP 3-13.4) ===")
    print(f"진짜 공격=force_arm(단독이면 항상 탐지) · SOC 포화임계={SATURATION_THRESHOLD}\n")
    print(f"  {'미끼수':<8}{'미끼알림':<10}{'포화':<8}{'실공격 탐지':<12}{'기만 성공'}")
    for n in (0, 3, SATURATION_THRESHOLD, SATURATION_THRESHOLD + 3):
        r = _run(n)
        print(f"  {n:<8}{r.decoy_alerts:<10}{_b(r.soc_saturated):<8}"
              f"{_b(r.real_detected_under_mildec):<12}{_b(r.mildec_effective)}")
    print("\n교리: JP 3-13.4 MILDEC — 미끼(decoy)로 분석주의를 소모시켜 진짜 공격 은폐.")
    print("      red 가 blue 의 방어 임계(S9 SOC 용량)를 역으로 무기화.")


def _b(x) -> str:
    return "○" if x else "✗"


if __name__ == "__main__":
    main()

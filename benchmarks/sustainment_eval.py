#!/usr/bin/env python3
"""작전지속력 데모 — 고도화 §I (Sustainment / JP 3-0·4-0).

    python benchmarks/sustainment_eval.py

목표별 TTP 소모(burn) 순환으로 몇 라운드 지속 가능한지. 결정론·무의존.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from redteam_core.sustainment import run_sustained_campaign      # noqa: E402
from redteam_core.assessment import OBJECTIVES                    # noqa: E402


def main() -> None:
    print("=== fried-pollack-ai · 작전지속력(Sustainment) — 고도화 §I ===")
    print("TTP 소모(burn): 효과 나며 탐지된 TTP 는 시그니처 노출 → 재사용 불가\n")
    for obj in OBJECTIVES:
        r = run_sustained_campaign(obj, rounds=5)
        head = f"지속 {r.rounds_sustained}/{r.rounds_requested}라운드" + (" (소진)" if r.exhausted else "")
        print(f"[{obj}] {head}  · 소진 TTP={r.burned_ttps or '없음'}")
        for rnd, ttp, note in r.log:
            print(f"    R{rnd}: {ttp or '-':<20} {note}")
        print()
    print("교리: Sustainment — 지속력 = 소진 안 되는 TTP(사각지대/회피형) 수.")
    print("      무장 목표는 전 TTP 범주형 → 즉시 소진 = red 지속 불가(blue 견고).")


if __name__ == "__main__":
    main()

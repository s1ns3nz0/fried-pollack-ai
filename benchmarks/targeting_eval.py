#!/usr/bin/env python3
"""표적개발·우선순위화 데모 — 고도화 §F (JP 3-60 ②).

    python benchmarks/targeting_eval.py

CARVER HPTL → §E 교전 → 관측 취약성으로 동적 재우선순위화. 결정론·무의존.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from redteam_core.targeting import run_targeting_campaign      # noqa: E402


def main() -> None:
    hptl0, outcomes, hptl1 = run_targeting_campaign()
    print("=== fried-pollack-ai · 표적개발·우선순위화 — 고도화 §F (JP 3-60 ②) ===\n")

    print("① 초기 HPTL (CARVER 합계):")
    for i, t in enumerate(hptl0, 1):
        c = t.carver
        print(f"  {i}. {t.name:<20} 점수={t.score():<3} "
              f"(C{c.criticality} A{c.accessibility} R{c.recuperability} "
              f"V{c.vulnerability} E{c.effect} R{c.recognizability})  → {t.objective}")

    print("\n② 순차 교전(§E 적응형 재계획):")
    for o in outcomes:
        head = "✅ 달성" if o.verdict == "achieved" else "⛔ blocked"
        via = f" via {o.winning_ttp}" + ("(사각지대)" if o.via_blindspot else "") if o.winning_ttp else ""
        print(f"  {o.target.name:<20} {head}{via}  → 관측 V={o.observed_vulnerability}")

    print("\n③ 갱신 HPTL (관측 취약성 반영 재우선순위화):")
    for i, t in enumerate(hptl1, 1):
        print(f"  {i}. {t.name:<20} 점수={t.score():<3} (V={t.carver.vulnerability})")

    print("\n교리: JP 3-60 ② 표적개발·우선순위화. 교전 BDA 로 취약성 확증 → 표적 순환(HPTL 갱신).")


if __name__ == "__main__":
    main()

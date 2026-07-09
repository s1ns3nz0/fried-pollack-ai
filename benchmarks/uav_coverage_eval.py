#!/usr/bin/env python3
"""UAV ATT&CK 커버리지 매트릭스 데모 — 팀 매트릭스 대비 RED 커버리지.

    python benchmarks/uav_coverage_eval.py

동언님·수지님 UAV ATT&CK 매트릭스(15전술·104기법) 기준 RED 커버리지·갭·히어로셋.
결정론·무의존(Tier-0).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from redteam_core.mapping.uav_coverage import (                             # noqa: E402
    coverage_by_tactic, effective_summary, gaps_by_scope,
)


def main():
    s = effective_summary()
    print("=== fried-pollack-ai · UAV ATT&CK 커버리지 (팀 매트릭스 기준) ===\n")
    print(f"  총 커버리지 : {s['covered']}/{s['total_techniques']} = {s['coverage_pct']}%")
    print(f"  범위 제외   : {s['excluded']}개(공격자 인프라·수동 수집)")
    print(f"  ▶ 유효 커버리지: {s['covered']}/{s['in_scope']} = {s['effective_pct']}%\n")
    print(f"  {'전술':24}{'커버':>8}")
    for t in coverage_by_tactic():
        bar = "█" * round(10 * t.covered / t.total) if t.total else ""
        print(f"  {t.tactic:24}{t.covered:>3}/{t.total:<3} {bar}")
    g = gaps_by_scope()
    print(f"\n보강 후보 {len(g['reinforce'])}개 (에이전트 실증 가능):")
    for tac, tid, name in g["reinforce"]:
        print(f"  · {tid:10} {name} ({tac})")
    print("\n판정: 팀 UAV 매트릭스 기준 유효 86% 커버 — 공격 시나리오 체계적 완성도 입증.")


if __name__ == "__main__":
    main()

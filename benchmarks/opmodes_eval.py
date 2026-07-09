#!/usr/bin/env python3
"""운용 방식별 공격 데모 — S111~S126 (임무·제어·모드·기종).

    python benchmarks/opmodes_eval.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from redteam_core.opmodes import OPMODE_SCENARIOS, categories, run_opmode   # noqa: E402


def main() -> None:
    print("=== UAV 운용 방식별 공격 (4차원 16개, MITRE 정박) ===\n")
    for cat, sids in categories().items():
        print(f"[{cat}]")
        for sid in sids:
            r = run_opmode(sid)
            print(f"   {sid} {r.name:<26} {r.mitre:<8} {r.effect}")
        print()

    print("=== 운용방식별 캠페인 ===")
    from redteam_core.campaigns import run_chain
    icon = {"stealthy": "🥷은밀", "detected": "🔴탐지", "blocked": "⛔차단"}
    nm = {"C30": "임무탈취", "C31": "제어강탈", "C32": "착륙강제", "C33": "자율무력"}
    for cid in ("C30", "C31", "C32", "C33"):
        cr = run_chain(cid)
        flow = "→".join(s for s, _, _ in cr.stages)
        print(f"  {cid} {nm[cid]:<8} {icon[cr.verdict]}  {flow}")


if __name__ == "__main__":
    main()

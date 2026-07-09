#!/usr/bin/env python3
"""편대/군집 비행 공격 데모 — S101~S108 (MITRE ATT&CK 기반).

    python benchmarks/swarm_eval.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from redteam_core.swarm import SWARM_SCENARIOS, run_swarm      # noqa: E402


def main() -> None:
    print("=== 편대/군집 비행 공격 (9대 군집, MITRE ATT&CK 기반) ===\n")
    print(f"  {'#':<6}{'시나리오':<26}{'MITRE':<9}{'결과'}")
    for sid in SWARM_SCENARIOS:
        r = run_swarm(sid, n=9, malicious=3)
        icon = "💥집단붕괴" if r.swarm_failure else "⚠️저하"
        print(f"  {sid:<6}{r.name:<26}{r.mitre:<9}{icon} · {r.effect}")
    print("\n=== 확장 군집/편대 캠페인 (다단계 킬체인) ===")
    from redteam_core.campaigns import run_chain
    from redteam_core.campaigns.chains import CHAINS
    _names = {"C23": "군집 붕괴", "C24": "리더 참수", "C25": "합의 전복",
              "C26": "분단 격파", "C27": "공급망 전파", "C28": "물리 파괴", "C29": "대량 유출"}
    icon = {"stealthy": "🥷은밀", "detected": "🔴탐지", "blocked": "⛔차단"}
    for cid in ("C23", "C24", "C25", "C26", "C27", "C28", "C29"):
        cr = run_chain(cid)
        flow = "→".join(s for s, _, _ in cr.stages)
        print(f"  {cid} {_names[cid]:<8} {icon[cr.verdict]}  {flow}")

    print("\n핵심: 개별 기체가 아니라 리더·분산합의·충돌회피·메시 등 '집단 조정 로직'을 노림.")
    print("      군집 공격을 단일UAV·EW·공급망·유출과 엮어 다단계 킬체인화.")


if __name__ == "__main__":
    main()

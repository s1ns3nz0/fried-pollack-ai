#!/usr/bin/env python3
"""편대/군집 비행 공격 데모 — S103~S110 (MITRE ATT&CK 기반).

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
    print("\n핵심: 개별 기체가 아니라 리더·분산합의·충돌회피·메시 등 '집단 조정 로직'을 노림.")
    print("      군집 고유 공격면 = blue Sentinel 미감시 사각지대.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Web/API·Linux 권한상승 신규 시나리오 데모 — S42~S47 + §T 분석.

    python benchmarks/web_privesc_eval.py

red 익스플로잇(§N) → §T 정적 분석 판정. blue Sentinel 사각지대를 §T 가 커버.
결정론·무의존(Tier-0).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from redteam_core.payloads.exploits import (                                 # noqa: E402
    craft_ssrf, craft_idor, craft_webshell, craft_pickle,
    craft_suid, craft_container_escape, craft_cron_hijack,
)
from redteam_core.sandbox import analyze                                     # noqa: E402

CASES = [
    craft_ssrf(), craft_idor(), craft_webshell(), craft_pickle(),
    craft_suid("find"), craft_container_escape("docker_sock"), craft_cron_hijack(),
]


def main():
    print("=== fried-pollack-ai · Web/API·Linux 권한상승 (S42~S47) + §T 분석 ===\n")
    print(f"  {'시나리오':<6}{'기법':<10}{'판정':<12}{'지표'}")
    for p in CASES:
        r = analyze(p)
        mark = {"malicious": "🔴", "suspicious": "🟠", "benign": "🟢"}[r.verdict]
        tag = mark + (" ⚪사각" if r.blind_spot else "")
        ind = r.indicators[0] if r.indicators else "-"
        print(f"  {p.scenario:<6}{p.kind:<10}{tag:<12}{ind}")
    print("\n판정: SSRF(IMDS)·웹셸·역직렬화·컨테이너 escape·SUID·cron = §T 탐지.")
    print("      IDOR 등 전용 탐지기 없는 건 blue 사각지대(방어 공백) 산출.")
    print("      전부 blue UAV Sentinel 룰 밖 IT 계층 → §T 샌드박스가 방어 seam.")


if __name__ == "__main__":
    main()

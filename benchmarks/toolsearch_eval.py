#!/usr/bin/env python3
"""GitHub 툴 자동검색 §X 데모 — 블로커 자동연동·갭 배치·온디맨드.

    python benchmarks/toolsearch_eval.py

공격 막힐 때(blocked/사각) GitHub 도구 자동 추천. GITHUB_TOKEN 없으면 큐레이션 시드.
읽기전용. 결정론(시드).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from redteam_core.toolsearch import (                            # noqa: E402
    discover_for_gaps, discover_for_objective, search_github,
)


def _fmt(tools):
    return " · ".join(f"{t['repo']}(★{t['stars']})" for t in tools) or "-"


def main() -> None:
    print("=== fried-pollack-ai · GitHub 툴 자동검색 §X ===\n")

    print("① 온디맨드 검색: 'gnss spoof drone'")
    for t in search_github("gnss spoof drone", 3):
        print(f"   {t['repo']:<32}★{t['stars']:<6} {t['desc']}")

    print("\n② 블로커 자동연동(진행 어려울 때)")
    for obj in ("weapon_effect", "rc_link_hijack", "recon_access"):
        d = discover_for_objective(obj)
        tag = "🔍 막힘→검색" if d["triggered"] else "✅ 달성(검색 불필요)"
        print(f"   {obj:<16} [{d['verdict']:<9}] {tag}")
        if d["triggered"]:
            print(f"       → {_fmt(d['tools'])}")

    print("\n③ 커버리지 갭 배치(사각/차단 목표 일괄)")
    gaps = discover_for_gaps(limit=1)
    print(f"   갭 목표 {len(gaps)}개 — 상위 예시:")
    for g in gaps[:5]:
        print(f"   {g['objective']:<16} [{g['verdict']:<9}] → {_fmt(g['tools'])}")

    print("\n안전: 읽기전용(검색만). 실 라이브=GITHUB_TOKEN, 없으면 큐레이션 시드.")
    print("      자율루프 훅: suggest_on_block(objective, verdict) — 코어 불변(외부 호출).")


if __name__ == "__main__":
    main()

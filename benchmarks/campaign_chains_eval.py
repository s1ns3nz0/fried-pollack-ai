#!/usr/bin/env python3
"""캠페인 체인 실행 데모 — 고도화 §M (C1~C10 탐지 프로파일).

    python benchmarks/campaign_chains_eval.py

각 체인을 시나리오 시퀀스로 실행해 어느 단계에서 blue 가 잡는지 관측.
결정론·무의존(Tier-0).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from redteam_core.campaigns import CHAINS, run_chain          # noqa: E402


def main() -> None:
    print("=== fried-pollack-ai · 캠페인 체인 실행 — 고도화 §M ===\n")
    for cid in CHAINS:
        r = run_chain(cid)
        head = {"stealthy": "🥷 은밀 관통", "detected": "🔴 탐지 관통", "blocked": "⛔ 차단"}[r.verdict]
        flow = " → ".join(
            f"{s}{'(사각)' if d is None else '(탐지)' if d else '(회피)'}"
            for s, _, d in r.stages)
        note = f"  ← 탐지 단계: {', '.join(r.detected_at)}" if r.detected_at else ""
        print(f"[{cid}] {head}")
        print(f"     {flow}{note}\n")
    print("핵심: C9(SOC LLM 인젝션→군집포화)는 전 단계 사각 = 완전 은밀(최대 방어 공백).")
    print("      C8/C10은 재밍(사각)으로 시작하나 하류(AOI이탈·스푸핑·SAR)에서 탐지됨.")


if __name__ == "__main__":
    main()

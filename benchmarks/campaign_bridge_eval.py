#!/usr/bin/env python3
"""신규 캠페인 체인 C14~C18 데모 — IT(사각)↔OT 브릿지.

    python benchmarks/campaign_bridge_eval.py

IT 계층(S53~S60)은 UAV Sentinel 사각, OT 계층(S1~S89)에서 탐지 — blue 가 어디서
잡는지 보여준다. 결정론·무의존(Tier-0).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from redteam_core.campaigns import run_chain                                 # noqa: E402
from redteam_core.campaigns.chains import CHAINS                             # noqa: E402

DESC = {
    "C14": "아카이브 공급망(Zip Slip)→펌웨어 변조→항법거부",
    "C15": "웹셸→컨테이너escape→임무 자기승인→무장 (IT→OT)",
    "C16": "웹셸→SUID→escape→cron (순수 IT 권한상승)",
    "C17": "아카이브 전달→웹셸→SAR 유출",
    "C18": "인증우회(IDOR)→무장 (범주형 견고차단)",
}


def main():
    print("=== fried-pollack-ai · 신규 캠페인 체인 C14~C18 (IT↔OT 브릿지) ===\n")
    for c in ("C14", "C15", "C16", "C17", "C18"):
        r = run_chain(c)
        mark = {"stealthy": "🥷", "detected": "🔴", "blocked": "⛔"}[r.verdict]
        chain = "→".join(CHAINS[c])
        first = r.detected_at[0] if r.detected_at else "—"
        print(f"{mark} {c} [{r.verdict}] {chain}")
        print(f"     {DESC[c]}")
        print(f"     최초 탐지: {first}\n")
    print("핵심: C16 = 순수 IT 권한상승은 UAV SOC 에 완전 사각(🥷).")
    print("      C15 = IT 발판은 사각이나 OT 임무층(S36) 닿는 순간 탐지 = 방어 경계선.")
    print("      C18 = 인증우회로도 무장(S3)은 범주형 견고차단(탐지).")


if __name__ == "__main__":
    main()

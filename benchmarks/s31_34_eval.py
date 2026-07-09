#!/usr/bin/env python3
"""S24~S97 — 신규 시나리오 에이전트 실행 데모.

    python benchmarks/s31_34_eval.py

S24 C2 재밍 · S90 SOC LLM 프롬프트 인젝션 · S91 모델 추출 · S97 능동 정찰.
각 시나리오를 에이전트로 실행해 효과·탐지·종합을 관측. 결정론·무의존(Tier-0).

핵심 발견: EW·AI 계열(S24~S91)은 blue 룰 미매핑 = 사각지대 클러스터.
S97 정찰만 S6로 탐지(회피창 존재).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from redteam_core.assessment import adaptive_engage          # noqa: E402

SCENARIOS = [
    ("S24 C2 링크 재밍", "c2_jam_denial"),
    ("S90 SOC LLM 프롬프트 인젝션", "soc_llm_inject"),
    ("S91 모델 추출·탈취", "model_extraction"),
    ("S97 능동 정찰·스캔", "network_recon"),
]


def main() -> None:
    print("=== fried-pollack-ai · S24~S97 신규 시나리오 실행 ===\n")
    print(f"  {'시나리오':<28}{'TTP':<18}{'결과':<10}{'탐지 여부'}")
    for label, obj in SCENARIOS:
        r = adaptive_engage(obj)
        head = "✅ 달성" if r.verdict == "achieved" else "⛔ 차단"
        # 마지막 시도의 탐지 상태
        detected = r.trace[-1][2].detected
        det = {True: "🔴 탐지(S34)", False: "🟢 회피", None: "⚪ 사각지대"}[detected]
        print(f"  {label:<28}{r.winning_ttp or '-':<18}{head:<10}{det}")

    print("\n판정: S24~S91(EW·AI)은 blue 미매핑=사각지대 → 무조건 은밀 달성(방어 공백).")
    print("      S97 정찰은 S34 연속임계로 탐지되나 저율 회피 가능.")
    print("      → 5장 방어 보강: 재밍·프롬프트인젝션·모델추출 탐지 신설 + 누적 정찰 탐지.")


if __name__ == "__main__":
    main()

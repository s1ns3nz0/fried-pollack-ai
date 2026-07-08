#!/usr/bin/env python3
"""시나리오 실 실행기 데모 — §U (dry-run: 실 아티팩트 생성만).

    python benchmarks/execute_eval.py

각 시나리오가 실제로 만드는 공격 아티팩트를 출력(전송 안 함). 실 전송은 env 표적 +
§T 샌드박스 게이트 통과 시에만(dry_run=False). 결정론.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from redteam_core.execute import execute_all      # noqa: E402


def main() -> None:
    print("=== fried-pollack-ai · 시나리오 실 실행기 §U (dry-run) ===")
    print("각 시나리오가 만드는 실제 공격 아티팩트(전송 X). 실 전송=env+§T 샌드박스.\n")
    print(f"  {'#':<5}{'카테고리':<11}{'아티팩트'}")
    for r in execute_all(dry_run=True):
        print(f"  {r.scenario:<5}{r.category:<11}{r.artifact}")
    print("\n안전: dry-run 기본(생성만) · 실 전송은 MAVLINK_ENDPOINT/STUB_*/C2_HOST/AI_TARGET_URL")
    print("      + §T 샌드박스 격리·스코프내·non-malicious 통과 시에만(fail-closed). 실 RF 금지.")


if __name__ == "__main__":
    main()

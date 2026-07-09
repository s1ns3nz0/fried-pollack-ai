#!/usr/bin/env python3
"""외부 연동 계층 데모 — 고도화 §O (opt-in seam).

    python benchmarks/integrations_eval.py

각 연동의 가용성·모드를 출력하고 폴백 실행을 시연. env 미지정 = 폴백.
실연동: AI_ATTACK_PROVIDER/AI_TARGET_URL · CALDERA_URL/CALDERA_API_KEY · MAVLINK_ENDPOINT.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from redteam_core.integrations import ai_attack, caldera, integration_status, sitl  # noqa: E402


def main() -> None:
    print("=== fried-pollack-ai · 외부 연동 계층 §O (opt-in seam) ===\n")
    print("① 연동 상태")
    for name, st in integration_status().items():
        mode = st["mode"]
        mark = "🟢 real" if mode == "real" else "⚪ fallback"
        print(f"   {name:<12}: {mark}  {({k: v for k, v in st.items() if k != 'mode'})}")

    print("\n② 폴백 실행 시연 (env 미지정)")
    a = ai_attack.run_ai_attack("prompt_injection")
    print(f"   AI공격(S90)  : mode={a['mode']} detected={a['detected']} ({a['mitre']})")
    c = caldera.run_operation("C9")
    print(f"   Caldera(C9)  : mode={c['mode']} verdict={c['verdict']}")
    s = sitl.inject_gps_spoof()
    print(f"   SITL(GPS)    : mode={s['mode']} {s.get('note','')}")

    print("\n실연동: env 지정 시 각 어댑터가 real 모드로 전환(PyRIT/Garak·Caldera·mavlink-router).")


if __name__ == "__main__":
    main()

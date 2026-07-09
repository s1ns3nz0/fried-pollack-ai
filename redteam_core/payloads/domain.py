"""도메인 특화 시나리오 — Cross-segment ISR 핸드오프·ESC 펌웨어 (S80~S16).

세그먼트 분석 사각지대 보강(cloud 제외). 방산 UAV 도메인 고유 공격면:
- S80 Cross-segment ISR 핸드오프 변조: 공군 KUS-FS → 육군 지작사 ISR 신뢰경계에서
  SAR 표적좌표·상황도 변조 → 오표적 유도. (도메인 문서상 '보호경계')
- S16 ESC 펌웨어 변조: DShot 신호 조작(S8) 너머 ESC 펌웨어(BLHeli 등) 플래시로
  지속적 모터 거동 왜곡·파괴. 결정론.
"""
from __future__ import annotations

from .exploits import ExploitPayload


def craft_isr_handoff_tamper() -> ExploitPayload:       # S80
    return ExploitPayload(
        "S80", "isr_handoff",
        {"boundary": "공군 KUS-FS → 육군 지작사 ISR", "op": "SAR 표적좌표·상황도 변조",
         "effect": "오표적 유도", "note": "cross-segment 신뢰경계"},
        "T1565/T0832", "공군→육군 ISR 핸드오프 신뢰경계에서 표적정보 변조(오표적)")


def craft_esc_firmware() -> ExploitPayload:             # S16
    return ExploitPayload(
        "S16", "esc_firmware",
        {"target": "ESC(BLHeli)", "op": "malicious firmware flash",
         "effect": "모터 거동 왜곡·강제정지·과회전→추락", "persist": "재부팅 생존"},
        "T1495/T0879", "ESC 펌웨어 변조로 모터 지속 장악(신호조작 S8 너머 펌웨어층)")


DOMAIN_SCENARIOS = {
    "S80": craft_isr_handoff_tamper,
    "S16": craft_esc_firmware,
}

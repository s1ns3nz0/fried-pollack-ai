"""MILDEC — 미끼로 SOC 주의를 포화시켜 진짜 공격을 은폐.

모델: 각 미끼가 탐지되면 알림 1건 → 분석주의 소모. 동시 알림이 SOC 처리한계
(SATURATION_THRESHOLD)를 넘으면 포화 → 진짜 공격에 배정될 주의가 분산돼 실제
탐지가 억제된다(§A 단독이면 탐지될 공격이 기만 하에 생존).

SATURATION_THRESHOLD 는 blue S19(SOC 용량 베이스라인)과 대응하는 값 — red 는
blue 의 방어 임계를 역으로 무기화한다.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from ..assessment import assess_action

# SOC 동시 알림 처리한계(분석주의 예산). blue S19 용량 임계와 대응.
SATURATION_THRESHOLD = 5


@dataclass
class DeceptionResult:
    real_action: str
    real_alone_detected: bool     # 실공격 단독이면 탐지되나
    decoy_alerts: int             # 미끼가 유발한 알림 수
    saturation_threshold: int
    soc_saturated: bool           # SOC 포화 여부
    real_detected_under_mildec: bool   # 기만 하 실제 탐지 여부
    mildec_effective: bool        # 기만으로 실공격 생존(단독이면 탐지될 것을)?
    decoys: List[Tuple[str, bool]] = field(default_factory=list)  # (action, detected)


def run_deception(real_action: str, decoys: List[dict],
                  real_intensity: float = 1.0) -> DeceptionResult:
    """decoys: [{"action": str, "intensity": float}] — 탐지될수록 좋은 미끼."""
    decoy_log: List[Tuple[str, bool]] = []
    alerts = 0
    for d in decoys:
        det = assess_action(d["action"], intensity=d.get("intensity", 1.0)).detected
        decoy_log.append((d["action"], bool(det)))
        if det:
            alerts += 1

    saturated = alerts >= SATURATION_THRESHOLD
    real_alone = bool(assess_action(real_action, intensity=real_intensity).detected)
    # 포화 시 분석주의 분산 → 진짜 공격 탐지 억제.
    real_under = real_alone and not saturated
    effective = real_alone and not real_under      # 단독 탐지 → 기만으로 미탐지 전환

    return DeceptionResult(
        real_action=real_action, real_alone_detected=real_alone,
        decoy_alerts=alerts, saturation_threshold=SATURATION_THRESHOLD,
        soc_saturated=saturated, real_detected_under_mildec=real_under,
        mildec_effective=effective, decoys=decoy_log)

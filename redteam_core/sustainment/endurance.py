"""작전지속력 — TTP 소모(burn) 순환으로 목표를 몇 라운드 지속 가능한가.

TTP 가 '효과를 내며 탐지'되면 시그니처 노출 → 소진(burn) → 재사용 불가.
회피형(연속임계 회피창)·사각지대 TTP 는 탐지 안 돼 소진되지 않음 → 지속 가능.
범주형 TTP 는 효과 시 항상 탐지 → 1회로 소진.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Set, Tuple

from ..assessment import OBJECTIVES
from ..assessment.rules import action_to_rule
from ..assessment.replan import EFFECT_FLOOR


@dataclass
class CapabilityInventory:
    burned: Set[str] = field(default_factory=set)

    def burn(self, action: str) -> None:
        self.burned.add(action)

    def is_available(self, action: str) -> bool:
        return action not in self.burned


def _detected_when_effective(action: str) -> Optional[bool]:
    """이 TTP 를 효과 나게 쓰면 탐지되나. None=사각지대(미매핑 룰)."""
    spec = action_to_rule(action)
    if spec is None:
        return None                                   # 사각지대 — 미탐지
    if spec.kind == "categorical":
        return True                                   # 효과=탐지(회피 불가)
    # 연속: 효과바닥 < 탐지임계면 회피창 존재 → 미탐지 가능.
    floor = EFFECT_FLOOR.get(action, 0.0)
    thr = spec.threshold if spec.threshold is not None else 0.0
    return not (floor < thr)                           # 회피창 없으면 탐지


@dataclass
class SustainmentResult:
    objective: str
    rounds_requested: int
    rounds_sustained: int
    exhausted: bool
    burned_ttps: List[str] = field(default_factory=list)
    log: List[Tuple[int, Optional[str], str]] = field(default_factory=list)  # (round, ttp, 결과)


def run_sustained_campaign(objective: str, rounds: int = 5) -> SustainmentResult:
    inv = CapabilityInventory()
    ttps = OBJECTIVES[objective]
    sustained = 0
    exhausted = False
    log: List[Tuple[int, Optional[str], str]] = []

    for rnd in range(1, rounds + 1):
        survived = False
        for t in ttps:
            if not inv.is_available(t):
                continue
            det = _detected_when_effective(t)
            if det is True:
                inv.burn(t)                            # 탐지 → 소진, 다음 대안 시도
                continue
            survived = True                            # 미탐지 TTP 로 생존(재사용 가능)
            log.append((rnd, t, "지속(미탐지)"))
            break
        if survived:
            sustained += 1
        else:
            exhausted = True
            log.append((rnd, None, "소진 — 신선한 TTP 없음"))
            break

    return SustainmentResult(objective, rounds, sustained, exhausted,
                             sorted(inv.burned), log)

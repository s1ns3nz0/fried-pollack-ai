"""HPTL 우선순위화 + 동적 표적 순환 (JP 3-60 ②).

초기 HPTL 은 CARVER 합계로 정렬. 이후 각 표적을 §E 적응형 재계획으로 교전하고,
관측된 취약성(사각지대 달성/차단)으로 V 를 갱신해 **재우선순위화**한다 —
persistent engagement 의 표적 순환.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from ..assessment import adaptive_engage
from ..assessment.rules import action_to_rule
from .carver import CATALOG, Target


def prioritize(targets) -> List[Target]:
    """CARVER 합계 내림차순(동점은 criticality)으로 HPTL 정렬."""
    return sorted(targets, key=lambda t: (t.score(), t.carver.criticality), reverse=True)


@dataclass
class TargetOutcome:
    target: Target
    verdict: str                 # achieved | blocked
    winning_ttp: Optional[str]
    via_blindspot: bool          # 사각지대(미매핑 룰)로 달성?
    observed_vulnerability: int  # 교전으로 관측·갱신된 V


def _observed_vulnerability(verdict: str, winning_ttp: Optional[str]) -> int:
    if verdict != "achieved":
        return 1                                  # 차단됨 = 견고(저취약)
    if winning_ttp and action_to_rule(winning_ttp) is None:
        return 5                                  # 사각지대로 달성 = 고취약(확증)
    return 4                                       # 회피로 달성 = 취약


def run_targeting_campaign(catalog=CATALOG):
    """초기 HPTL → 순차 교전(§E) → 관측 V 로 재우선순위화.

    반환: (초기 HPTL, 교전결과 목록, 갱신 HPTL).
    """
    hptl0 = prioritize(catalog)
    outcomes: List[TargetOutcome] = []
    updated: List[Target] = []
    for t in hptl0:
        r = adaptive_engage(t.objective)
        via_blind = bool(r.winning_ttp and action_to_rule(r.winning_ttp) is None)
        v = _observed_vulnerability(r.verdict, r.winning_ttp)
        outcomes.append(TargetOutcome(t, r.verdict, r.winning_ttp, via_blind, v))
        updated.append(Target(t.tid, t.name, t.objective,
                              t.carver.with_vulnerability(v), t.note))
    return hptl0, outcomes, prioritize(updated)

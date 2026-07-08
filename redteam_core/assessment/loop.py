"""폐루프 — plan → execute(emit) → observe(BDA) → adapt, 그리고 임계 보정.

교리: OCO(공격)의 OODA 를 방어자(DCO) 반응에 대해 orient 한다. 탐지되면 강도를
낮춰(이분 탐색) 재시도해 blue 룰의 탐지 경계를 실측하고, 그 경계로 blue 가상값
임계를 보정한다(= JP 3-60 ⑥단계 산출: 재타격 권고 + 방어 보정).

동언님 코어 그래프는 건드리지 않는다. 이 루프는 액션 시퀀스(그의 planner 산출 또는
시나리오)를 받아 감싸는 '전투평가 하네스'로 동작한다(그의 182 테스트 불변).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .bda import DetectionOutcome, assess_action
from .rules import action_to_rule


@dataclass
class CalibrationRecord:
    """폐루프 부산물: 룰별 탐지/회피 경계 실측 + blue 가상값 대조."""
    rule_id: str
    threshold_param: str
    detected_at: Optional[float] = None     # 이 값 이상에서 탐지됨(관측된 최소)
    evaded_at: Optional[float] = None       # 이 값 이하에서 회피됨(관측된 최대)
    blue_assumed: Optional[float] = None     # 룰의 씨앗 임계(대조)
    outcomes: List[DetectionOutcome] = field(default_factory=list)

    @property
    def boundary(self) -> Optional[float]:
        if self.detected_at is not None and self.evaded_at is not None:
            return round((self.detected_at + self.evaded_at) / 2, 6)
        return None


def probe_boundary(action: str, start_intensity: float, floor: float = 1e-4,
                   backoff: float = 0.5, max_iters: int = 12) -> CalibrationRecord:
    """연속 룰: 강도를 backoff 로 낮춰가며 탐지→회피 경계를 이분 탐색."""
    spec = action_to_rule(action)
    rec = CalibrationRecord(
        rule_id=spec.rule_id if spec else action,
        threshold_param=spec.threshold_param if spec else "intensity",
        blue_assumed=spec.threshold if spec else None)

    intensity = start_intensity
    for _ in range(max_iters):
        out = assess_action(action, intensity=intensity)
        rec.outcomes.append(out)
        if out.detected:
            rec.detected_at = intensity if rec.detected_at is None else min(rec.detected_at, intensity)
            intensity = round(intensity * backoff, 6)
            if intensity < floor:
                break
        else:
            rec.evaded_at = intensity if rec.evaded_at is None else max(rec.evaded_at, intensity)
            break                       # 회피 도달 = 경계 하한 확보
    return rec


@dataclass
class LoopResult:
    steps: List[DetectionOutcome] = field(default_factory=list)
    calibrations: List[CalibrationRecord] = field(default_factory=list)
    evaded_chain: bool = False          # 모든 단계에서 최종 회피 성공 여부


def run_closed_loop(actions: List[dict]) -> LoopResult:
    """액션 시퀀스(킬체인)를 폐루프로 수행.

    actions 항목: {"action": str, "intensity": float(연속 룰만)}.
    - 연속 룰: probe_boundary 로 경계 탐색 → calibration.
    - 범주형 룰: 강도 회피 불가 → 탐지 확정 기록(TTP 전환 권고).
    """
    res = LoopResult(evaded_chain=True)
    for item in actions:
        action = item["action"]
        spec = action_to_rule(action)
        if spec and spec.kind == "continuous":
            rec = probe_boundary(action, float(item.get("intensity", 1.0)))
            res.calibrations.append(rec)
            final = rec.outcomes[-1]
            res.steps.append(final)
            if final.detected:
                res.evaded_chain = False        # 바닥까지 낮춰도 탐지 → 이 단계 blocked
        else:
            out = assess_action(action, categorical_attack=True)
            res.steps.append(out)
            if out.detected:
                res.evaded_chain = False         # 범주형은 강도로 회피 불가
    return res

"""BDA — red 의 전투평가: '방어자가 이 강도의 공격을 탐지했나'.

주어진 액션 + 강도(intensity)로 관측 가능한 UAV*_CL 행 필드를 구성하고, 매칭되는
blue 룰의 술어로 탐지여부를 판정한다. 이것이 폐루프의 '관측(observe)' 단계이며,
JP 3-60 ⑥단계(전투평가)를 방어자 반응까지 확장한 부분이다.

주: 여기서 행 필드는 강도에 따라 구성된다(오프라인 룰-평가 리플레이). 라이브에서는
동언님 bridge/telemetry_tap.py 가 audit_log 에서 실제 방출한 행으로 대체되고,
관측은 Sentinel Incident 조회로 스왑된다(본선). blue 룰 로직 자체는 동일.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .rules import RuleSpec, action_to_rule


@dataclass
class DetectionOutcome:
    action: str
    rule_id: Optional[str]
    detected: Optional[bool]        # None = 관측 대상 룰 없음
    kind: Optional[str]             # continuous | categorical
    threshold_param: Optional[str]
    intensity: Optional[float]      # 이번에 사용한 강도(연속 룰만 의미)
    threshold: Optional[float]      # blue 임계 씨앗(대조용)
    note: str = ""


def _observable(action: str, spec: RuleSpec, intensity: float, categorical_attack: bool) -> dict:
    """액션+강도로부터 blue 룰이 볼 관측 행 필드를 구성."""
    if spec.kind == "continuous":
        return {spec.threshold_param: intensity}
    # categorical: 공격이면 위반 플래그 on(임계로 회피 불가). 관측 표면은 논리 확정.
    if spec.rule_id == "S11_Unauthorized_Weapon_Cmd":
        return {"is_self_approval": categorical_attack, "is_unknown_op": categorical_attack}
    if spec.rule_id == "S15_OffHours_C4I_Cmd":
        return {"offhours": categorical_attack, "unauthorized": categorical_attack}
    return {}


def assess_action(action: str, intensity: float = 1.0,
                  categorical_attack: bool = True) -> DetectionOutcome:
    spec = action_to_rule(action)
    if spec is None:
        return DetectionOutcome(action, None, None, None, None, intensity, None,
                                note="관측 대상 blue 룰 없음(사각지대 후보)")
    row = _observable(action, spec, intensity, categorical_attack)
    detected = bool(spec.predicate(row)) if spec.predicate else None
    return DetectionOutcome(
        action=action, rule_id=spec.rule_id, detected=detected, kind=spec.kind,
        threshold_param=spec.threshold_param if spec.kind == "continuous" else None,
        intensity=intensity if spec.kind == "continuous" else None,
        threshold=spec.threshold,
        note=spec.provenance)

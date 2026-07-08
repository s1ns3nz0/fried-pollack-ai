"""sustainment — 지속/작전지속력 (고도화 §I, 합동기능 Sustainment).

에이전트의 약했던 '지속' 기능 보강. TTP 소모(burn)를 모델링한다: 탐지된 TTP 는
시그니처가 노출돼 소진(재사용 시 즉시 탐지) → 신선한 대안으로 순환해야 작전을
지속할 수 있다. 목표별 red 의 작전지속력(endurance)을 산정.

교리:
  - 합동기능 Sustainment (JP 3-0) · 군수/지속 (JP 4-0): 지구력·능력 재보급.
  - 통찰: 목표별 지속력 = f(소진 안 된 TTP 대안 수). 사각지대/회피형 TTP 는
    탐지되지 않아 소진되지 않음 → 무한 지속. 범주형은 1회 사용에 소진.
"""
from .endurance import CapabilityInventory, SustainmentResult, run_sustained_campaign

__all__ = ["CapabilityInventory", "SustainmentResult", "run_sustained_campaign"]

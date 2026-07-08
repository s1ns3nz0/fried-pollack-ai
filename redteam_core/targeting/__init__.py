"""targeting — 표적개발·우선순위화 (고도화 §F, JP 3-60 ②).

동언님 정적 engagement_profile 을 CARVER 기반 동적 표적우선순위(HPTL)로 확장.
교리:
  - JP 3-60 ②: 표적개발·우선순위화. HPTL(고가치표적목록)/HVT.
  - CARVER: Criticality·Accessibility·Recuperability·Vulnerability·Effect·Recognizability.
동적성: §A 탐지커버리지·§E 교전결과(사각지대/차단)를 피드백받아 취약성(V)을
갱신하고 재우선순위화 → persistent engagement 의 표적 순환.
"""
from .carver import Carver, Target, CATALOG
from .prioritize import prioritize, run_targeting_campaign, TargetOutcome

__all__ = ["Carver", "Target", "CATALOG", "prioritize",
           "run_targeting_campaign", "TargetOutcome"]

"""deception — 군사기만(MILDEC)/정보활동 (고도화 §H, 합동기능 Information).

에이전트의 약했던 '정보활동' 기능 보강. 탐지 '회피'를 넘어 방어자를 적극 '기만'한다:
미끼(decoy) 공격으로 blue SOC 의 분석주의를 포화시켜 진짜 공격을 은폐한다.
이는 blue 가 모델링한 S8/S9(군집포화·SOC 과부하) 위협을 red 가 역이용하는 것.

교리:
  - JP 3-13 Information Operations · JP 3-13.4 Military Deception(MILDEC).
  - 기만수단: feint(양동)·demonstration(시위)·decoy(미끼)·display.
  - 목표: 방어자가 잘못된 인식을 형성해 자기 이익에 반해 행동하게 함.
"""
from .mildec import DeceptionResult, SATURATION_THRESHOLD, run_deception

__all__ = ["DeceptionResult", "SATURATION_THRESHOLD", "run_deception"]

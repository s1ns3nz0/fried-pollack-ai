"""opmodes — UAV 운용 방식별 공격 (S111~S126).

단일 기체를 운용 4차원으로 확장:
  - 임무 수행 방식(임무수행): 선회·복귀·추적·측량
  - 조종 및 제어 방식(조종제어): 제어권 전환·자세제어·BLOS·자율결심
  - 조작 모드(조작모드): 비행모드 강제변경·페일세이프 차단·모드 위조보고
  - 비행 종류별(비행종류): 고정익 실속·회전익 요·VTOL 천이·이착륙 위상
전부 ICS/Enterprise ATT&CK 정박, blue 미배포 사각지대.
"""
from .scenarios import OPMODE_SCENARIOS, categories, run_opmode

__all__ = ["OPMODE_SCENARIOS", "run_opmode", "categories"]

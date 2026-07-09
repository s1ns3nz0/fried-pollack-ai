"""simtest — 시뮬 기반 공격 고도화 (§Z, AutoSimTestFramework 영감).

방어측 sUAS 시뮬 테스트 프레임(S/M/Env/Analytics 에이전트)을 레드팀으로 전이:
  - sensors     : 다중센서 폴트인젝션 S9~S12(IMU·기압·지자기·에어스피드)
  - environment : 환경 공격 증폭(바람·도심협곡·지형 → 스푸핑/재밍 효과 증폭)
  - incident_kb : 실 sUAS 인시던트 KB → 공격 시나리오 도출·근거화(S-Agent)
  - log_oracle  : 비행로그 분석으로 공격효과 검증(Analytics-Agent, BDA 오라클)

안전: 폴트 아티팩트만(dry). 실 주입은 SITL/HIL + env + §T 샌드박스 통과 시에만.
"""
from .sensors import SENSOR_SCENARIOS, run_sensor_fault
from .environment import ENVIRONMENTS, amplify
from .incident_kb import INCIDENT_KB, scenarios_from_incidents
from .log_oracle import analyze_flightlog

__all__ = ["SENSOR_SCENARIOS", "run_sensor_fault", "ENVIRONMENTS", "amplify",
           "INCIDENT_KB", "scenarios_from_incidents", "analyze_flightlog"]

"""execute — 시나리오 실 실행기 (§U).

인가된 해커톤 레드팀(팀 소유 uav-sim-env 대상) 범위에서 모든 시나리오를 실제 공격
아티팩트(MAVLink 프레임·HTTP 페이로드·명령·유출 바이트)로 실행한다.

안전(기존 자세 유지):
  - dry_run=True 기본: 실 아티팩트를 **생성만** 하고 전송 안 함(감사·검증용).
  - 실 표적은 env 게이트(MAVLINK_ENDPOINT/STUB_*_URL/C2_HOST/AI_TARGET_URL). 미설정=dry.
  - 실 RF 방사 없음(EMSO는 물리계산+텔레메트리). 물리 비가역은 코어 HITL 게이트.
"""
from .executor import ExecResult, SCENARIO_EXEC, execute_all, execute_scenario

__all__ = ["ExecResult", "SCENARIO_EXEC", "execute_all", "execute_scenario"]

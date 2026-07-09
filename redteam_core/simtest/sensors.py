"""다중센서 폴트인젝션 — S9~S12 (IMU·기압계·지자기·에어스피드).

GNSS(S1) 넘어 관성/기압/지자기/에어스피드 센서를 스푸핑·폴트 → 오토파일럿 EKF가
오염 데이터로 상태추정 오류 → 자세 불안정·고도 오판·항로 이탈. 점진 주입(ramp)이면
EKF innovation 게이트를 통과(은밀), 급변이면 거부. 실 주입은 SITL/HIL+§T 샌드박스.
"""
from __future__ import annotations

from dataclasses import dataclass

SENSOR_SCENARIOS = {
    "S9": {"name": "IMU 스푸핑/폴트(자이로·가속도)", "objective": "imu_spoof",
            "sensor": "imu", "effect": "자세추정 오류→불안정/추락", "mitre": "T0806 / ICS 센서조작",
            "ekf_gate": 0.35},
    "S10": {"name": "기압계 스푸핑(고도)", "objective": "baro_spoof",
            "sensor": "baro", "effect": "고도 오판→지형충돌/실속", "mitre": "T0806",
            "ekf_gate": 0.30},
    "S11": {"name": "지자기 스푸핑(방위)", "objective": "mag_spoof",
            "sensor": "mag", "effect": "방위 오류→항로 이탈(toilet-bowling)", "mitre": "T0806",
            "ekf_gate": 0.40},
    "S12": {"name": "에어스피드 스푸핑", "objective": "airspeed_spoof",
            "sensor": "airspeed", "effect": "실속/과속 오판→비행제어 상실", "mitre": "T0806",
            "ekf_gate": 0.25},
}


@dataclass
class SensorFault:
    scenario: str
    sensor: str
    ramp_rate: float          # 초당 주입 오프셋(작을수록 은밀)
    accepted: bool            # EKF innovation 게이트 통과 여부
    effect: str
    stealthy: bool


def run_sensor_fault(scenario_id: str, ramp_rate: float = 0.1) -> SensorFault:
    """센서 폴트 주입 모델. ramp_rate < ekf_gate 면 EKF 수용(은밀 효과)."""
    m = SENSOR_SCENARIOS[scenario_id]
    accepted = ramp_rate <= m["ekf_gate"]          # 점진 주입 = 게이트 통과
    return SensorFault(scenario_id, m["sensor"], ramp_rate, accepted,
                       m["effect"] if accepted else "EKF 거부(급변 탐지)",
                       stealthy=accepted)

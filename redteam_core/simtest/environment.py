"""환경 공격 증폭 — 바람·기상·도심협곡·지형이 공격효과를 증폭.

Env-Agent 전이: 환경은 방어 조건이자 공격 증폭기다. 예: 도심협곡 GNSS 멀티패스로
스푸핑 성공률↑, 고풍 시 센서잡음↑로 폴트인젝션 은폐↑, 산악 시 재밍 LOS 차폐.
"""
from __future__ import annotations

# 환경 → 공격유형별 효과 배수(gain) + 탐지 은폐(masking)
ENVIRONMENTS = {
    "clear": {"gnss_spoof": 1.0, "jam": 1.0, "sensor_fault": 1.0, "masking": 0.0},
    "urban_canyon": {"gnss_spoof": 1.6, "jam": 0.8, "sensor_fault": 1.2, "masking": 0.3,
                     "note": "멀티패스→GNSS 스푸핑↑, LOS 차폐→재밍↓"},
    "mountainous": {"gnss_spoof": 1.2, "jam": 1.4, "sensor_fault": 1.1, "masking": 0.2,
                    "note": "지형 차폐·반사→재밍/스푸핑↑"},
    "high_wind": {"gnss_spoof": 1.0, "jam": 1.0, "sensor_fault": 1.5, "masking": 0.4,
                  "note": "센서잡음↑→폴트인젝션 은폐↑"},
    "storm": {"gnss_spoof": 1.1, "jam": 1.2, "sensor_fault": 1.6, "masking": 0.5,
              "note": "악천후→전 공격 은폐·증폭"},
}


def amplify(attack: str, environment: str, base_effect: float = 1.0) -> dict:
    """공격효과를 환경으로 증폭하고 탐지 은폐율 산출."""
    env = ENVIRONMENTS.get(environment, ENVIRONMENTS["clear"])
    gain = env.get(attack, 1.0)
    return {"attack": attack, "environment": environment,
            "effect": round(base_effect * gain, 3), "gain": gain,
            "detection_masking": env.get("masking", 0.0),
            "note": env.get("note", "표준 조건")}

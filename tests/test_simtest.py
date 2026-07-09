"""simtest §Z 테스트 — 센서·환경·인시던트KB·로그오라클. 결정론·무의존."""
from __future__ import annotations

from redteam_core.assessment import OBJECTIVES, adaptive_engage
from redteam_core.simtest import (
    ENVIRONMENTS, SENSOR_SCENARIOS, amplify, analyze_flightlog,
    run_sensor_fault, scenarios_from_incidents,
)


def test_sensor_scenarios_and_objectives():
    assert set(SENSOR_SCENARIOS) == {"S9", "S10", "S11", "S12"}
    for obj in ("imu_spoof", "baro_spoof", "mag_spoof", "airspeed_spoof"):
        assert obj in OBJECTIVES


def test_gradual_injection_bypasses_ekf():
    r = run_sensor_fault("S9", ramp_rate=0.1)     # 점진 → 게이트 통과
    assert r.accepted is True and r.stealthy is True


def test_abrupt_injection_rejected():
    r = run_sensor_fault("S10", ramp_rate=1.0)     # 급변 → EKF 거부
    assert r.accepted is False and "거부" in r.effect


def test_environment_amplifies_gnss_spoof():
    base = amplify("gnss_spoof", "clear")["effect"]
    urban = amplify("gnss_spoof", "urban_canyon")["effect"]
    assert urban > base                            # 도심협곡 멀티패스 증폭
    assert amplify("sensor_fault", "storm")["gain"] > 1.0


def test_incident_kb_grounds_scenarios():
    scs = scenarios_from_incidents()
    assert any(s["scenario"] == "S11" and "toilet" in s["from_incident"].lower() for s in scs)
    assert all(s["provenance"] for s in scs)


def test_log_oracle_detects_effect():
    o = analyze_flightlog([{"pos_dev_m": 120, "alt_err_m": 35, "attitude_var": 0.7, "mode": "RTL"}])
    assert o["effect"] is True and o["signatures"]
    assert analyze_flightlog([{"pos_dev_m": 2, "alt_err_m": 1}])["effect"] is False


def test_sensor_spoof_is_agent_blindspot():
    r = adaptive_engage("imu_spoof")
    assert r.verdict == "achieved" and r.trace[-1][2].detected is None

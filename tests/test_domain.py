"""도메인 특화 시나리오 S72~S73 (사각지대 보강) 테스트. 결정론·무의존."""
from __future__ import annotations

from redteam_core.payloads.domain import DOMAIN_SCENARIOS
from redteam_core.sandbox import analyze
from redteam_core.mapping.uav_coverage import RED_COVER


def test_two_domain_scenarios():
    assert set(DOMAIN_SCENARIOS) == {"S72", "S73"}


def test_s72_isr_handoff_cross_segment():
    p = DOMAIN_SCENARIOS["S72"]()
    assert "육군" in p.data["boundary"] and analyze(p).verdict == "malicious"


def test_s73_esc_firmware_beyond_signal():
    p = DOMAIN_SCENARIOS["S73"]()
    assert "펌웨어" in p.note and analyze(p).verdict == "malicious"


def test_scenarios_reflected_in_red_cover():
    assert "S72" in RED_COVER["T1565"] and "S72" in RED_COVER["T0832"]
    assert "S73" in RED_COVER["T1495"] and "S73" in RED_COVER["T0879"]

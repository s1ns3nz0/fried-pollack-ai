"""dronesploit 영감 §V 테스트 — WiFi·프로파일·모듈·CVE. 결정론·무의존."""
from __future__ import annotations

from redteam_core.assessment import OBJECTIVES, adaptive_engage
from redteam_core.dronesploit import (
    COTS_PROFILES, MODULE_REGISTRY, WIFI_SCENARIOS, build_deauth_frame,
    cves_for, load_module, run_wifi,
)


def test_wifi_scenarios_and_objectives():
    assert set(WIFI_SCENARIOS) == {"S25", "S26", "S27", "S28"}
    for obj in ("wifi_deauth", "wifi_evil_twin", "wifi_jam", "wifi_cred"):
        assert obj in OBJECTIVES


def test_deauth_frame_built():
    f = build_deauth_frame()
    assert b"DEAUTH" in f and len(f) > 0


def test_wifi_dry_no_transmission():
    r = run_wifi("S25", dry=True)
    assert r.transmitted is False and "deauth" in r.artifact


def test_wifi_is_blindspot_in_agent():
    # WiFi 계층은 blue 전용 탐지룰 미배포 → 사각지대 은밀 달성.
    r = adaptive_engage("wifi_evil_twin")
    assert r.verdict == "achieved" and r.trace[-1][2].detected is None


def test_cots_profiles_include_tactical():
    assert "tactical_small_uas" in COTS_PROFILES
    assert "S25" in COTS_PROFILES["cots_wifi_micro"]["scenarios"]


def test_module_framework_run():
    m = load_module("exploit/wifi/S26")
    m.set("DRY", "true")
    assert m.run()["scenario"] == "S26"
    assert len(MODULE_REGISTRY) > 20        # 실행기 시나리오 + WiFi 모듈


def test_cve_registry_maps_scenarios():
    assert any(c["scenario"] == "S28" for c in [c for s in ("S28",) for c in cves_for(s)])

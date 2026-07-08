"""고급 드론 공격 §W 테스트 — RC·DShot·anti-forensics·카탈로그. 결정론·무의존."""
from __future__ import annotations

from redteam_core.advanced import (
    AF_SCENARIOS, EVASION_TECHNIQUES, RF_SCENARIOS, TECHNIQUE_TOOLS,
    run_antiforensics, run_rf, tools_for_scenario,
)
from redteam_core.assessment import OBJECTIVES, adaptive_engage


def test_rf_scenarios_and_objectives():
    assert set(RF_SCENARIOS) == {"S43", "S44", "S45", "S46"}
    for obj in ("rc_link_hijack", "rc_override", "rc_downgrade", "dshot_motor", "antiforensics"):
        assert obj in OBJECTIVES


def test_rf_dry_no_transmission():
    r = run_rf("S43", dry=True)
    assert r.transmitted is False and "bind" in r.artifact.lower()


def test_dshot_motor_artifact():
    r = run_rf("S46", dry=True)
    assert "DShot" in r.artifact or "MOTOR" in r.artifact


def test_antiforensics_methods():
    af = run_antiforensics(dry=True)
    assert "dataflash_wipe" in af.methods and af.executed is False


def test_advanced_scenarios_are_blindspots():
    for obj in ("rc_link_hijack", "dshot_motor", "antiforensics"):
        r = adaptive_engage(obj)
        assert r.verdict == "achieved" and r.trace[-1][2].detected is None


def test_catalog_maps_tools():
    assert any(t["scenario"] == "S43" for t in TECHNIQUE_TOOLS)
    assert tools_for_scenario("S6")[0]["tools"]
    assert len(EVASION_TECHNIQUES) >= 3

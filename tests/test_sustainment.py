"""작전지속력 테스트 — 고도화 §I. 결정론·무의존."""
from __future__ import annotations

from redteam_core.sustainment import run_sustained_campaign


def test_nav_denial_sustains_via_blindspot():
    # gnss_spoof 는 효과=탐지 → 소진되나, jam(사각지대)으로 전 라운드 지속.
    r = run_sustained_campaign("nav_denial", rounds=5)
    assert r.rounds_sustained == 5 and r.exhausted is False
    assert "gnss_spoof" in r.burned_ttps           # 스푸핑은 소진됨
    assert all(t == "jam" or t is None for _, t, _ in r.log)  # 지속은 jam 으로


def test_recon_access_sustains_via_evasion():
    # active_scan 은 회피창 존재 → 미탐지 → 소진 안 됨 → 지속.
    r = run_sustained_campaign("recon_access", rounds=4)
    assert r.rounds_sustained == 4 and not r.exhausted
    assert r.burned_ttps == []


def test_weapon_effect_exhausts_quickly():
    # force_arm·unauthorized_command 둘 다 범주형 → 효과=탐지 → 즉시 소진 → 지속 0.
    r = run_sustained_campaign("weapon_effect", rounds=5)
    assert r.rounds_sustained == 0 and r.exhausted is True
    assert set(r.burned_ttps) == {"force_arm", "unauthorized_command"}


def test_core_untouched():
    from redteam_core.graph.build import build_graph  # noqa: F401

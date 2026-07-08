"""EMSO(전자전) 효과 모델 테스트 — 고도화 §C. 결정론·무의존.

재밍 J/S·GNSS 포획 물리, 대역 분류, 그리고 §A BDA 로의 연결(effect→S1)까지.
"""
from __future__ import annotations

from redteam_core.emso import gnss_spoof_effect, jam_effect, plan_emso
from redteam_core.assessment import assess_action


def test_strong_gnss_spoof_captures_receiver():
    e = gnss_spoof_effect(spoof_eirp_dbm=20, spoof_dist_m=100)
    assert e.achieved is True
    assert e.telemetry_hint["pos_horiz_variance"] > 0.0238   # blue S1 게이트 상회


def test_weak_distant_gnss_spoof_fails_capture():
    e = gnss_spoof_effect(spoof_eirp_dbm=-20, spoof_dist_m=20000)
    assert e.achieved is False
    assert e.telemetry_hint["pos_horiz_variance"] == 0.0


def test_strong_close_jam_denies_link():
    e = jam_effect(2437.0, jammer_eirp_dbm=40, jammer_dist_m=100,
                   signal_eirp_dbm=20, signal_dist_m=200)
    assert e.achieved is True and e.metric_db >= 6.0


def test_weak_far_jam_fails():
    e = jam_effect(2437.0, jammer_eirp_dbm=10, jammer_dist_m=3000,
                   signal_eirp_dbm=20, signal_dist_m=200)
    assert e.achieved is False


def test_plan_emso_classifies_band():
    o = plan_emso("gnss_spoof", {"spoof_eirp_dbm": 20, "spoof_dist_m": 100})
    assert o.band == "1.5GHz" and o.ea_type == "EA"


def test_emso_effect_feeds_bda_detection():
    # §C 물리 → 강도 → §A BDA → blue S1 판정 (완결 체인).
    o = plan_emso("gnss_spoof", {"spoof_eirp_dbm": 20, "spoof_dist_m": 100})
    intensity = o.effect.telemetry_hint["pos_horiz_variance"]
    bda = assess_action("gnss_spoof", intensity=intensity)
    assert bda.rule_id == "S1_GNSS_Spoofing" and bda.detected is True


def test_rf_symmetry_with_blue_model():
    # blue counter-uas 와 같은 log-distance 모델(거리↑ → RSSI↓ 단조).
    from redteam_core.emso.rf import rssi_dbm
    assert rssi_dbm(20, 100, 2437) > rssi_dbm(20, 1000, 2437)

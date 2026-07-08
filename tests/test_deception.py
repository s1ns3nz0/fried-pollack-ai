"""MILDEC 테스트 — 고도화 §H. 결정론·무의존."""
from __future__ import annotations

from redteam_core.deception import run_deception, SATURATION_THRESHOLD


def _decoys(n):
    # active_scan intensity 20 = 확실히 탐지되는 미끼.
    return [{"action": "active_scan", "intensity": 20} for _ in range(n)]


def test_enough_decoys_saturate_and_hide_real_attack():
    # 실공격(force_arm)은 단독이면 항상 탐지되지만, 충분한 미끼로 포화 → 생존.
    r = run_deception("force_arm", _decoys(SATURATION_THRESHOLD))
    assert r.real_alone_detected is True
    assert r.soc_saturated is True
    assert r.real_detected_under_mildec is False
    assert r.mildec_effective is True


def test_insufficient_decoys_do_not_saturate():
    r = run_deception("force_arm", _decoys(SATURATION_THRESHOLD - 1))
    assert r.soc_saturated is False
    assert r.real_detected_under_mildec is True      # 여전히 탐지
    assert r.mildec_effective is False


def test_undetectable_decoys_do_not_count():
    # 낮은 강도 미끼(intensity 1 < 임계 5)는 탐지 안 돼 알림 미발생 → 포화 실패.
    decoys = [{"action": "active_scan", "intensity": 1} for _ in range(SATURATION_THRESHOLD + 2)]
    r = run_deception("force_arm", decoys)
    assert r.decoy_alerts == 0 and r.soc_saturated is False


def test_core_untouched():
    from redteam_core.graph.build import build_graph  # noqa: F401

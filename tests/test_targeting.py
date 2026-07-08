"""표적개발·우선순위화 테스트 — 고도화 §F. 결정론·무의존."""
from __future__ import annotations

from redteam_core.targeting import CATALOG, prioritize, run_targeting_campaign


def test_hptl_sorted_by_carver_score_desc():
    hptl = prioritize(CATALOG)
    scores = [t.score() for t in hptl]
    assert scores == sorted(scores, reverse=True)


def test_dynamic_reprioritization_boosts_blindspot_target():
    hptl0, outcomes, hptl1 = run_targeting_campaign()
    by_id = {o.target.tid: o for o in outcomes}
    # GNSS: nav_denial 은 재밍 사각지대로 달성 → 고취약 확증(V=5).
    assert by_id["GNSS"].via_blindspot is True
    assert by_id["GNSS"].observed_vulnerability == 5
    # WEAPON: 범주형 전부 → 차단 → 저취약(V=1).
    assert by_id["WEAPON"].verdict == "blocked"
    assert by_id["WEAPON"].observed_vulnerability == 1


def test_reprioritized_hptl_ranks_blindspot_target_first():
    _, _, hptl1 = run_targeting_campaign()
    # 사각지대 확증(GNSS)이 갱신 HPTL 최상위.
    assert hptl1[0].tid == "GNSS"


def test_core_untouched():
    from redteam_core.graph.build import build_graph  # noqa: F401

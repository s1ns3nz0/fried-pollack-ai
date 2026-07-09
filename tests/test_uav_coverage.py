"""UAV ATT&CK 커버리지 매트릭스 테스트 — 팀 매트릭스 대비 RED. 결정론·무의존."""
from __future__ import annotations

from redteam_core.mapping.uav_coverage import (
    UAV_MATRIX, RED_COVER, coverage_by_tactic, summary, effective_summary,
    gaps, gaps_by_scope, hero_set,
)


def test_matrix_and_coverage_counts_stable():
    s = summary()
    assert s["total_techniques"] == len(UAV_MATRIX)
    assert s["covered"] == sum(1 for _, tid, _, _ in UAV_MATRIX if tid in RED_COVER)
    assert s["coverage_pct"] >= 70.0                      # 팀 매트릭스 70%+ 커버


def test_effective_coverage_excludes_out_of_scope():
    e = effective_summary()
    assert e["excluded"] >= 1 and e["in_scope"] == e["total_techniques"] - e["excluded"]
    assert e["effective_pct"] >= e["coverage_pct"]        # 범위제외 빼면 유효율 ↑


def test_every_gap_is_classified():
    g = gaps_by_scope()
    assert g["unclassified"] == []                        # 모든 갭이 excluded/reinforce 분류됨
    assert len(g["excluded"]) + len(g["reinforce"]) == len(gaps())


def test_coverage_by_tactic_sums_to_total():
    tacs = coverage_by_tactic()
    assert sum(t.total for t in tacs) == len(UAV_MATRIX)
    assert sum(t.covered for t in tacs) == summary()["covered"]


def test_no_dangling_red_cover_ids():
    matrix_ids = {tid for _, tid, _, _ in UAV_MATRIX}
    assert set(RED_COVER) <= matrix_ids                   # RED_COVER 는 매트릭스 기법만 참조


def test_impact_tactic_high_coverage():
    impact = next(t for t in coverage_by_tactic() if t.tactic == "Impact")
    assert impact.covered >= 15                           # Impact(물리 타격)은 우리 강점

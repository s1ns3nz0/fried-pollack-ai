"""KPI 4~6순위 테스트 — 결정론·무의존."""
from __future__ import annotations

from redteam_core.kpi import mitre_coverage, reattack_efficiency, roe_compliance


def test_mitre_coverage_counts_frameworks():
    mc = mitre_coverage()
    assert mc["total_techniques"] > 0
    fw = mc["by_framework"]
    assert fw["ICS"] > 0 and fw["ATLAS"] > 0        # OT + AI 계열 둘 다 커버


def test_roe_blocks_ew_and_weapon():
    rc = roe_compliance()
    # JCEOI 미승인·ConOps 밖이라 BLOCKED 이 다수(EW·무장).
    assert rc["verdicts"]["BLOCKED"] >= 2
    assert rc["evaluated"] == sum(rc["verdicts"].values())


def test_reattack_efficiency_reports_avg():
    re_ = reattack_efficiency()
    assert re_["achieved_objectives"] >= 1
    assert re_["avg_attempts_to_achieve"] is not None and re_["avg_attempts_to_achieve"] >= 1.0

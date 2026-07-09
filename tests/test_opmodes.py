"""운용 방식별 공격 테스트 — S111~S126 (임무·제어·모드·기종). 결정론·무의존."""
from __future__ import annotations

from redteam_core.assessment import OBJECTIVES, adaptive_engage
from redteam_core.campaigns import run_chain
from redteam_core.opmodes import OPMODE_SCENARIOS, categories, run_opmode


def test_sixteen_scenarios_four_categories():
    assert set(OPMODE_SCENARIOS) == {f"S{n}" for n in range(111, 127)}
    cats = categories()
    assert set(cats) == {"임무수행", "조종제어", "조작모드", "비행종류"}
    assert all(len(v) == 4 for v in cats.values())          # 차원별 4개씩


def test_objectives_registered_and_blindspot():
    for sid, (obj, *_) in OPMODE_SCENARIOS.items():
        assert obj in OBJECTIVES
        r = adaptive_engage(obj)
        assert r.verdict == "achieved" and r.trace[-1][2].detected is None


def test_airframe_scenarios_cover_types():
    # 고정익·회전익·VTOL·이착륙 위상.
    names = " ".join(m[1] for m in OPMODE_SCENARIOS.values())
    for kw in ("고정익", "회전익", "VTOL", "이착륙"):
        assert kw in names


def test_opmode_campaigns_run():
    for cid in ("C30", "C31", "C32", "C33"):
        r = run_chain(cid)
        assert r.verdict in ("stealthy", "detected", "blocked")
        assert len(r.stages) >= 3


def test_mitre_grounded():
    assert all(m[2].startswith("T") for m in OPMODE_SCENARIOS.values())

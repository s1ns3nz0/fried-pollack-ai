"""편대/군집 비행 공격 테스트 — S103~S110. 결정론·무의존."""
from __future__ import annotations

from redteam_core.assessment import OBJECTIVES, adaptive_engage
from redteam_core.campaigns import run_chain
from redteam_core.swarm import SWARM_SCENARIOS, run_swarm


def test_eight_swarm_scenarios():
    assert set(SWARM_SCENARIOS) == {f"S{n}" for n in range(103, 111)}


def test_objectives_registered_and_blindspot():
    for sid, (obj, *_) in SWARM_SCENARIOS.items():
        assert obj in OBJECTIVES
        r = adaptive_engage(obj)
        assert r.verdict == "achieved" and r.trace[-1][2].detected is None


def test_leader_spoof_captures_followers():
    r = run_swarm("S103", n=9)
    assert r.swarm_failure and r.detail["captured"] == 8


def test_consensus_poison_exceeds_bft():
    # n=9 → BFT 허용 f=2. 악성 3 > 2 → 합의 붕괴.
    assert run_swarm("S104", n=9, malicious=3).swarm_failure is True
    assert run_swarm("S104", n=9, malicious=2).swarm_failure is False   # 허용 이내


def test_mesh_partition_fragments_swarm():
    assert run_swarm("S110", n=9, malicious=3).swarm_failure is True     # 3 >= 9//3


def test_swarm_collapse_campaign():
    assert run_chain("C23").verdict in ("stealthy", "detected")


def test_mitre_grounded():
    # 각 시나리오가 ICS/Enterprise ATT&CK 기법에 정박.
    assert all(m[2].startswith("T") for m in SWARM_SCENARIOS.values())

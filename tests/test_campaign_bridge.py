"""신규 캠페인 체인 C14~C18 (IT↔OT 브릿지) 테스트. 결정론·무의존."""
from __future__ import annotations

from redteam_core.campaigns import run_chain
from redteam_core.campaigns.chains import CHAINS


def test_new_chains_registered():
    for c in ("C14", "C15", "C16", "C17", "C18"):
        assert c in CHAINS


def test_c14_archive_supply_chain_detected_downstream():
    r = run_chain("C14")                     # S58(사각)→S33→S1
    assert r.verdict == "detected"
    assert ("S58", True, None) in r.stages   # 아카이브 전달은 사각
    assert "S33" in r.detected_at             # 펌웨어 변조에서 탐지


def test_c15_it_to_ot_bridge_caught_at_mission_layer():
    r = run_chain("C15")                     # S54→S56(사각)→S36→S3
    assert r.verdict == "detected"
    assert "S54" not in r.detected_at and "S56" not in r.detected_at   # IT 계층 사각
    assert "S36" in r.detected_at                                      # OT 임무층에서 탐지


def test_c16_pure_it_privesc_fully_stealthy():
    r = run_chain("C16")                     # S54→S55→S56→S57 전부 사각
    assert r.verdict == "stealthy" and r.detected_at == []


def test_c17_supply_web_exfil_caught_at_exfil():
    r = run_chain("C17")                     # S58→S54(사각)→S92
    assert r.verdict == "detected" and r.detected_at == ["S92"]


def test_c18_idor_to_arming_robust_block():
    r = run_chain("C18")                     # S53(사각)→S3(범주형)
    assert r.verdict == "detected" and "S3" in r.detected_at   # 인증우회로도 무장 탐지

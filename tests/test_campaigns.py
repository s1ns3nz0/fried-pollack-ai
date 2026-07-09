"""캠페인 체인 실행 테스트 — 고도화 §M. 결정론·무의존."""
from __future__ import annotations

from redteam_core.campaigns import CHAINS, run_chain


def test_new_chains_registered():
    for c in ("C8", "C9", "C10"):
        assert c in CHAINS


def test_c9_fully_stealthy_ai_campaign():
    # S90(프롬프트인젝션 사각) → S100(군집포화 미배포 사각) = 완전 은밀.
    r = run_chain("C9")
    assert r.verdict == "stealthy" and r.detected_at == []


def test_c8_starts_blind_but_detected_downstream():
    # S23(재밍 사각) → S109(AOI 배포룰 탐지) → S5(Failsafe 배포룰 탐지).
    r = run_chain("C8")
    assert r.verdict == "detected"
    assert "S109" in r.detected_at and "S5" in r.detected_at
    assert ("S23", True, None) == r.stages[0]      # 첫 단계는 사각


def test_c10_spoof_and_sar_detected():
    r = run_chain("C10")
    assert r.verdict == "detected"
    assert "S1" in r.detected_at and "S92" in r.detected_at


def test_c1_weapon_chain_detected():
    # 무장 체인은 범주형(S3/S79) 탐지로 잡힘.
    r = run_chain("C1")
    assert r.verdict == "detected" and "S3" in r.detected_at

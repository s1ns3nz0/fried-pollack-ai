"""S24~S97 신규 시나리오 배선 테스트 — 결정론·무의존."""
from __future__ import annotations

from redteam_core.assessment import OBJECTIVES, adaptive_engage, assess_action


def test_new_objectives_registered():
    for obj in ("c2_jam_denial", "soc_llm_inject", "model_extraction", "network_recon"):
        assert obj in OBJECTIVES


def test_s31_c2_jam_is_blindspot_stealthy():
    r = adaptive_engage("c2_jam_denial")
    assert r.verdict == "achieved" and r.winning_ttp == "jam"
    assert r.trace[-1][2].detected is None            # 사각지대


def test_s32_prompt_injection_blindspot():
    out = assess_action("ml_prompt_inject")
    assert out.rule_id is None and out.detected is None   # blue 미매핑
    r = adaptive_engage("soc_llm_inject")
    assert r.verdict == "achieved"


def test_s33_model_extraction_blindspot():
    r = adaptive_engage("model_extraction")
    assert r.verdict == "achieved" and r.trace[-1][2].detected is None


def test_s34_recon_detected_but_evadable():
    # active_scan → S34(연속임계) → 강도 하향으로 회피 달성.
    r = adaptive_engage("network_recon")
    assert r.verdict == "achieved" and r.winning_ttp == "active_scan"

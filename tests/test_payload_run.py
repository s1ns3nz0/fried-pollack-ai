"""페이로드 실행 배선 테스트 — 고도화 §N 배선. 결정론·무의존."""
from __future__ import annotations

from redteam_core.payloads import (
    bypass_rate, run_adversarial, run_model_extraction, run_prompt_injection,
)


def test_prompt_injection_all_bypass_blindspot():
    outs = run_prompt_injection(converters=["none", "base64"])
    assert len(outs) >= 6
    assert all(o.detected is None for o in outs)      # blue 미매핑 = 사각지대
    assert bypass_rate(outs) == 1.0                    # 우회율 100%


def test_model_extraction_ladder_bypasses():
    outs = run_model_extraction()
    assert len(outs) == 5 and bypass_rate(outs) == 1.0
    assert outs[0].scenario == "S33"


def test_adversarial_specs_execute():
    outs = run_adversarial()
    assert len(outs) == 4 and bypass_rate(outs) == 1.0


def test_outcome_carries_concrete_payload_preview():
    outs = run_prompt_injection(converters=["none"], )
    assert any(o.preview for o in outs) and outs[0].payload_id.startswith("PI-")

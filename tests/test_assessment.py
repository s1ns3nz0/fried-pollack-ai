"""폐루프 전투평가(BDA) 계층 테스트 — 고도화 §A.

동언님 기존 테스트와 동일하게 결정론·무의존. blue 룰 씨앗(연속/범주형) 판정,
경계 이분 탐색, 킬체인 폐루프, D8(코어 그래프 불변)까지 확인.
"""
from __future__ import annotations

from redteam_core.assessment import (
    assess_action, action_to_rule, probe_boundary, run_closed_loop, DETECTION_RULES,
)


def test_continuous_rule_detects_above_threshold():
    # S1: PosVar 0.8 은 게이트(0.0238) 초과 → 탐지.
    out = assess_action("gnss_spoof", intensity=0.8)
    assert out.rule_id == "S1_GNSS_Spoofing" and out.detected is True


def test_continuous_rule_evades_below_threshold():
    out = assess_action("gnss_spoof", intensity=0.01)   # 게이트 아래
    assert out.detected is False


def test_categorical_rule_cannot_be_evaded_by_intensity():
    # S11: 공격이면 강도와 무관하게 탐지 확정.
    out = assess_action("force_arm", categorical_attack=True)
    assert out.kind == "categorical" and out.detected is True
    assert out.intensity is None            # 연속 강도 개념 없음


def test_probe_boundary_brackets_blue_threshold():
    # S6: FailCount 20 에서 시작 → 5 미만으로 내려가며 경계 브래킷.
    rec = probe_boundary("active_scan", start_intensity=20)
    assert rec.detected_at is not None and rec.evaded_at is not None
    assert rec.evaded_at < rec.blue_assumed <= rec.detected_at   # 경계가 가상값을 감쌈


def test_run_closed_loop_produces_calibrations_and_verdict():
    res = run_closed_loop([
        {"action": "active_scan", "intensity": 20},
        {"action": "force_arm"},                # 범주형 → 체인 회피 실패 유발
    ])
    assert any(c.rule_id == "S6_Operator_BruteForce" for c in res.calibrations)
    assert res.evaded_chain is False            # 범주형 단계 때문에 전체 회피 실패


def test_unmapped_action_is_blind_spot():
    out = assess_action("param_read")           # 관측 룰 없음
    assert out.rule_id is None and out.detected is None


def test_rule_specs_have_provenance():
    # D8: 모든 룰 스펙은 blue 공유 산출물 출처를 명시(코드 결합 아님).
    for spec in DETECTION_RULES.values():
        assert spec.provenance and (".json" in spec.provenance)


def test_core_graph_untouched_importable():
    # 고도화가 동언님 코어 그래프를 깨지 않았는지(임포트 가능) 확인.
    from redteam_core.graph.build import build_graph  # noqa: F401

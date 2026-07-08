"""GitHub 툴 자동검색 §X 테스트 — 시드 폴백(무네트워크) 결정론."""
from __future__ import annotations

import pytest

from redteam_core.toolsearch import (
    discover_for_gaps, discover_for_objective, search_github, suggest_on_block,
)


@pytest.fixture(autouse=True)
def _no_token(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)   # 시드 폴백 강제


def test_search_matches_curated_seed():
    r = search_github("gnss gps spoof", 3)
    assert r and any("gps-sdr-sim" in t["repo"] for t in r)
    assert all(t["source"] == "curated" for t in r)


def test_blocker_triggers_search():
    # weapon_effect 는 blocked(전 TTP 범주형 탐지) → 검색 트리거.
    d = discover_for_objective("weapon_effect")
    assert d["verdict"] == "blocked" and d["triggered"] is True and d["tools"]


def test_achieved_does_not_trigger():
    d = suggest_on_block("soc_llm_inject", "achieved")
    assert d["triggered"] is False and d["tools"] == []


def test_rc_search_returns_rc_tools():
    # rc_link_hijack 은 사각지대라 achieved(안 막힘) → 검색 미트리거. 온디맨드로 확인.
    r = search_github("rc frsky elrs bind", 3)
    assert any("ExpressLRS" in t["repo"] for t in r)


def test_gap_batch_returns_candidates():
    gaps = discover_for_gaps(limit=1)
    assert len(gaps) >= 3
    assert all(g["tools"] for g in gaps)

"""AI 공격 provider 정직성 정책 (고도화 작업 3, 안 A).

기존엔 AI_ATTACK_PROVIDER=pyrit|garak|http 가 모두 generic HTTP probe 로 처리되어
native 호출처럼 오인될 수 있었음. 안 A: 실 live 경로는 http 로만 명확히 제한하고,
pyrit/garak 은 native wrapper 미구현임을 not_available 로 정직하게 반환한다.
"""
from __future__ import annotations

import pytest

from redteam_core.integrations import ai_attack

IN_SCOPE = "10.50.0.50"


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch):
    monkeypatch.delenv("AI_ATTACK_PROVIDER", raising=False)
    monkeypatch.delenv("AI_TARGET_URL", raising=False)


@pytest.mark.parametrize("prov", ["pyrit", "garak"])
def test_native_provider_not_available(monkeypatch, prov):
    monkeypatch.setenv("AI_ATTACK_PROVIDER", prov)
    monkeypatch.setenv("AI_TARGET_URL", f"http://{IN_SCOPE}:8000/score")
    assert ai_attack.available() is False                 # native 는 live 아님


@pytest.mark.parametrize("prov", ["pyrit", "garak"])
def test_native_provider_returns_not_available_without_posting(monkeypatch, prov):
    posted = []
    monkeypatch.setenv("AI_ATTACK_PROVIDER", prov)
    monkeypatch.setenv("AI_TARGET_URL", f"http://{IN_SCOPE}:8000/score")
    monkeypatch.setattr(ai_attack, "post_json",
                        lambda *a, **k: posted.append(1) or {})
    r = ai_attack.run_ai_attack("prompt_injection", "x")
    assert r["mode"] == "not_available" and posted == []
    assert r["provider"] == prov
    assert "http" in r["note"].lower()                    # http 로 전환 안내


def test_http_provider_still_available_and_real(monkeypatch):
    calls = []
    monkeypatch.setenv("AI_ATTACK_PROVIDER", "http")
    monkeypatch.setenv("AI_TARGET_URL", f"http://{IN_SCOPE}:8000/score")
    monkeypatch.setattr(ai_attack, "post_json",
                        lambda *a, **k: calls.append(1) or {"verdict": "ok"})
    assert ai_attack.available() is True
    assert ai_attack.run_ai_attack("prompt_injection", "x")["mode"] == "real"


def test_status_reports_native_unsupported(monkeypatch):
    monkeypatch.setenv("AI_ATTACK_PROVIDER", "pyrit")
    monkeypatch.setenv("AI_TARGET_URL", f"http://{IN_SCOPE}:8000/score")
    st = ai_attack.status()
    assert st["available"] is False
    assert st["native_supported"] is False


def test_no_env_still_blindspot_fallback(monkeypatch):
    assert ai_attack.run_ai_attack("prompt_injection")["mode"] == "fallback"

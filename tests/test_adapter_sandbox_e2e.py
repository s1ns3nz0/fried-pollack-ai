"""공개 진입점 × §T 샌드박스 가드 end-to-end 검증 (고도화 작업 2).

`_run_real()` 직접 테스트(test_integrations)와 guard 단위 테스트(test_sandbox_guard)는
있으나, 공개 API(run_operation/run_tool/run_module/lookup_cve/run_ai_attack)가
가드를 통과/차단하는 전 경로는 미검증이었음. 여기서 in-scope live vs
out-of-scope blocked 를 adapter 별로 배선까지 검증한다.

scope_cidr = 10.50.0.0/24 (engagement_profile.yaml, default_policy 폴백 동일).
"""
from __future__ import annotations

import pytest

from redteam_core.integrations import (
    ai_attack,
    caldera,
    cve_intel,
    metasploit,
    pentest_mcp,
)

IN_SCOPE = "10.50.0.50"      # scope_cidr 내 → guard 통과
OUT_SCOPE = "203.0.113.10"   # scope_cidr 밖 → egress 차단 → blocked_by_sandbox


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch):
    for k in ("AI_ATTACK_PROVIDER", "AI_TARGET_URL", "CALDERA_URL", "CALDERA_API_KEY",
              "CVE_MCP_URL", "PENTEST_MCP_URL", "MSF_MCP_URL", "MSF_RPC_HOST",
              "MSF_RPC_PORT", "MSF_RPC_PASSWORD"):
        monkeypatch.delenv(k, raising=False)


# --- caldera.run_operation ---------------------------------------------------

def test_caldera_public_in_scope_reaches_live(monkeypatch):
    calls = []
    monkeypatch.setenv("CALDERA_URL", f"http://{IN_SCOPE}:8888")
    monkeypatch.setenv("CALDERA_API_KEY", "k")
    monkeypatch.setattr(caldera, "post_json",
                        lambda url, body, headers=None: calls.append(url) or {"id": "op"})
    r = caldera.run_operation("C1")
    assert r["mode"] == "real" and calls and r["response"]["id"] == "op"


def test_caldera_public_out_of_scope_blocked(monkeypatch):
    calls = []
    monkeypatch.setenv("CALDERA_URL", f"http://{OUT_SCOPE}:8888")
    monkeypatch.setenv("CALDERA_API_KEY", "k")
    monkeypatch.setattr(caldera, "post_json",
                        lambda url, body, headers=None: calls.append(url) or {})
    r = caldera.run_operation("C1")
    assert r["mode"] == "blocked_by_sandbox" and calls == []


# --- pentest_mcp.run_tool ----------------------------------------------------

def test_pentest_public_in_scope_reaches_live(monkeypatch):
    calls = []
    monkeypatch.setenv("PENTEST_MCP_URL", f"http://{IN_SCOPE}:8000")
    monkeypatch.setattr(pentest_mcp, "post_json",
                        lambda url, body, headers=None: calls.append(url) or {"ok": True})
    r = pentest_mcp.run_tool("nuclei", {"target": "gcs.sim.dah.internal"})
    assert r["mode"] == "real" and calls and r["response"]["ok"] is True


def test_pentest_public_out_of_scope_blocked(monkeypatch):
    calls = []
    monkeypatch.setenv("PENTEST_MCP_URL", f"http://{OUT_SCOPE}:8000")
    monkeypatch.setattr(pentest_mcp, "post_json",
                        lambda url, body, headers=None: calls.append(url) or {})
    r = pentest_mcp.run_tool("nuclei", {"target": "gcs.sim.dah.internal"})
    assert r["mode"] == "blocked_by_sandbox" and calls == []


def test_pentest_public_out_of_allowlist_rejected_before_guard(monkeypatch):
    """allowlist 밖 도구는 서버·스코프와 무관하게 거부(fail-closed, 가드 전 차단)."""
    monkeypatch.setenv("PENTEST_MCP_URL", f"http://{IN_SCOPE}:8000")
    r = pentest_mcp.run_tool("hydra", {"target": "gcs.sim.dah.internal"})
    assert r["mode"] == "rejected"


# --- metasploit.run_module (MCP 경로) ----------------------------------------

def test_msf_public_in_scope_reaches_live(monkeypatch):
    calls = []
    monkeypatch.setenv("MSF_MCP_URL", f"http://{IN_SCOPE}:8000")
    monkeypatch.setattr(metasploit, "post_json",
                        lambda url, body, headers=None: calls.append(url) or {"job": 1})
    r = metasploit.run_module("auxiliary/scanner/portscan/tcp", {"RHOSTS": "10.50.0.9"})
    assert r["mode"] == "real" and calls and r["response"]["job"] == 1


def test_msf_public_out_of_scope_blocked(monkeypatch):
    calls = []
    monkeypatch.setenv("MSF_MCP_URL", f"http://{OUT_SCOPE}:8000")
    monkeypatch.setattr(metasploit, "post_json",
                        lambda url, body, headers=None: calls.append(url) or {})
    r = metasploit.run_module("auxiliary/scanner/portscan/tcp", {"RHOSTS": "x"})
    assert r["mode"] == "blocked_by_sandbox" and calls == []


# --- cve_intel.lookup_cve ----------------------------------------------------

def test_cve_public_in_scope_reaches_live(monkeypatch):
    calls = []
    monkeypatch.setenv("CVE_MCP_URL", f"http://{IN_SCOPE}:443")
    monkeypatch.setattr(cve_intel, "post_json",
                        lambda url, body, headers=None: calls.append(url) or {"cvss": 9.8})
    r = cve_intel.lookup_cve("CVE-2020-0001")
    assert r["mode"] == "real" and calls and r["record"]["cvss"] == 9.8


def test_cve_public_out_of_scope_blocked(monkeypatch):
    calls = []
    monkeypatch.setenv("CVE_MCP_URL", f"http://{OUT_SCOPE}:443")
    monkeypatch.setattr(cve_intel, "post_json",
                        lambda url, body, headers=None: calls.append(url) or {})
    r = cve_intel.lookup_cve("CVE-2020-0001")
    assert r["mode"] == "blocked_by_sandbox" and calls == []


# --- ai_attack.run_ai_attack -------------------------------------------------

def test_ai_attack_public_in_scope_reaches_live(monkeypatch):
    calls = []
    monkeypatch.setenv("AI_ATTACK_PROVIDER", "http")
    monkeypatch.setenv("AI_TARGET_URL", f"http://{IN_SCOPE}:8000/score")
    monkeypatch.setattr(ai_attack, "post_json",
                        lambda url, body, headers=None: calls.append(url) or {"verdict": "ok"})
    r = ai_attack.run_ai_attack("prompt_injection", "ignore previous")
    assert r["mode"] == "real" and calls and r["response"]["verdict"] == "ok"


def test_ai_attack_public_out_of_scope_blocked(monkeypatch):
    calls = []
    monkeypatch.setenv("AI_ATTACK_PROVIDER", "http")
    monkeypatch.setenv("AI_TARGET_URL", f"http://{OUT_SCOPE}:8000/score")
    monkeypatch.setattr(ai_attack, "post_json",
                        lambda url, body, headers=None: calls.append(url) or {})
    r = ai_attack.run_ai_attack("prompt_injection", "x")
    assert r["mode"] == "blocked_by_sandbox" and calls == []


# --- 실 경로 result shape 표준화 (작업 5 배선) --------------------------------

_ERR = {"error": {"type": "transport", "reason": "boom"}}


def test_caldera_real_ok_and_error_promoted(monkeypatch):
    monkeypatch.setenv("CALDERA_URL", f"http://{IN_SCOPE}:8888")
    monkeypatch.setenv("CALDERA_API_KEY", "k")
    monkeypatch.setattr(caldera, "post_json", lambda *a, **k: {"id": "op"})
    assert caldera.run_operation("C1")["ok"] is True
    monkeypatch.setattr(caldera, "post_json", lambda *a, **k: dict(_ERR))
    r = caldera.run_operation("C1")
    assert r["ok"] is False and r["error"]["type"] == "transport"


def test_pentest_real_ok_and_error_promoted(monkeypatch):
    monkeypatch.setenv("PENTEST_MCP_URL", f"http://{IN_SCOPE}:8000")
    monkeypatch.setattr(pentest_mcp, "post_json", lambda *a, **k: {"ok": True})
    assert pentest_mcp.run_tool("nuclei", {"target": "t"})["ok"] is True
    monkeypatch.setattr(pentest_mcp, "post_json", lambda *a, **k: dict(_ERR))
    assert pentest_mcp.run_tool("nuclei", {"target": "t"})["ok"] is False


def test_msf_real_ok_and_error_promoted(monkeypatch):
    monkeypatch.setenv("MSF_MCP_URL", f"http://{IN_SCOPE}:8000")
    monkeypatch.setattr(metasploit, "post_json", lambda *a, **k: {"job": 1})
    assert metasploit.run_module("auxiliary/x/y", {})["ok"] is True
    monkeypatch.setattr(metasploit, "post_json", lambda *a, **k: dict(_ERR))
    assert metasploit.run_module("auxiliary/x/y", {})["ok"] is False


def test_cve_real_ok_and_error_promoted(monkeypatch):
    monkeypatch.setenv("CVE_MCP_URL", f"http://{IN_SCOPE}:443")
    monkeypatch.setattr(cve_intel, "post_json", lambda *a, **k: {"cvss": 9.8})
    assert cve_intel.lookup_cve("CVE-1")["ok"] is True
    monkeypatch.setattr(cve_intel, "post_json", lambda *a, **k: dict(_ERR))
    assert cve_intel.lookup_cve("CVE-1")["ok"] is False


def test_ai_attack_real_ok_and_error_promoted(monkeypatch):
    monkeypatch.setenv("AI_ATTACK_PROVIDER", "http")
    monkeypatch.setenv("AI_TARGET_URL", f"http://{IN_SCOPE}:8000/score")
    monkeypatch.setattr(ai_attack, "post_json", lambda *a, **k: {"verdict": "ok"})
    assert ai_attack.run_ai_attack("prompt_injection", "x")["ok"] is True
    monkeypatch.setattr(ai_attack, "post_json", lambda *a, **k: dict(_ERR))
    assert ai_attack.run_ai_attack("prompt_injection", "x")["ok"] is False

"""외부 연동 계층 테스트 — 고도화 §O. env 없는 폴백 경로 검증(결정론)."""
from __future__ import annotations

import os

import pytest

from redteam_core.integrations import ai_attack, archive_tools, caldera, integration_status, sitl


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch):
    for k in ("AI_ATTACK_PROVIDER", "AI_TARGET_URL", "CALDERA_URL", "CALDERA_API_KEY",
              "MAVLINK_ENDPOINT", "TAXII_URL", "TAXII_COLLECTION", "CTID_PLAN_URL",
              "ARCHIVE_TOOL", "ARCHIVE_TOOL_CMD"):
        monkeypatch.delenv(k, raising=False)


def test_all_fallback_without_env():
    st = integration_status()
    assert all(v["mode"] == "fallback" for v in st.values())
    # 핵심 연동은 포함(부분집합) — 신규 연동 추가에 견고. 전부 fallback 은 위에서 검증.
    assert {"ai_attack", "caldera", "sitl", "threat_intel", "apt_emulation"} <= set(st)


def test_ai_attack_fallback_is_blindspot():
    r = ai_attack.run_ai_attack("prompt_injection")
    assert r["mode"] == "fallback" and r["detected"] is None   # 사각지대
    assert r["mitre"] == "AML.T0051"


def test_ai_attack_configured_live_path_posts_probe(monkeypatch):
    calls = []
    monkeypatch.setenv("AI_ATTACK_PROVIDER", "http")
    monkeypatch.setenv("AI_TARGET_URL", "http://ai-target.local/score")
    monkeypatch.setattr(ai_attack, "post_json",
                        lambda url, body, headers=None: calls.append((url, body, headers)) or {"verdict": "ok"})
    r = ai_attack._run_real("prompt_injection", "ignore previous", "AML.T0051")
    assert r["mode"] == "real"
    assert calls[0][0] == "http://ai-target.local/score"
    assert calls[0][1]["payload"] == "ignore previous"
    assert r["response"]["verdict"] == "ok"


def test_caldera_fallback_runs_internal_chain():
    r = caldera.run_operation("C9")
    assert r["mode"] == "fallback" and r["verdict"] == "stealthy"


def test_sitl_fallback_no_transmission():
    r = sitl.inject_gps_spoof()
    assert r["mode"] == "fallback" and r["frame_bytes"] > 0


def test_env_flips_availability(monkeypatch):
    monkeypatch.setenv("CALDERA_URL", "http://caldera.local:8888")
    monkeypatch.setenv("CALDERA_API_KEY", "k")
    assert caldera.available() is True
    assert caldera.status()["mode"] == "real"


def test_caldera_configured_live_path_posts_operation(monkeypatch):
    calls = []
    monkeypatch.setenv("CALDERA_URL", "http://caldera.local:8888")
    monkeypatch.setenv("CALDERA_API_KEY", "k")
    monkeypatch.setattr(caldera, "post_json",
                        lambda url, body, headers=None: calls.append((url, body, headers)) or {"id": "op-1"})
    r = caldera._run_real("C9")
    assert r["mode"] == "real"
    assert calls[0][0] == "http://caldera.local:8888/api/v2/operations"
    assert calls[0][1]["chain_id"] == "C9"
    assert calls[0][2]["KEY"] == "k"
    assert r["response"]["id"] == "op-1"


def test_sitl_endpoints_read_env(monkeypatch):
    monkeypatch.setenv("MAVLINK_ENDPOINT", "10.0.0.5:14550")
    assert sitl.endpoints()["mavlink"] == "10.0.0.5:14550"


def test_archive_tool_env_without_command_remains_fallback(monkeypatch):
    monkeypatch.setenv("ARCHIVE_TOOL", "evilarc")
    assert archive_tools.available() is True
    assert archive_tools.status()["mode"] == "fallback"
    r = archive_tools.craft("zip_slip")
    assert r["mode"] == "fallback"
    assert r["external_tool_implemented"] is False


def test_archive_tool_command_is_invoked(monkeypatch):
    calls = []

    class Result:
        returncode = 0
        stdout = "ok"
        stderr = ""

    monkeypatch.setenv("ARCHIVE_TOOL", "evilarc")
    monkeypatch.setenv("ARCHIVE_TOOL_CMD", "/opt/tools/archive-wrapper")   # 절대경로 → 정책 통과
    monkeypatch.setattr(archive_tools.subprocess, "run",
                        lambda cmd, **kw: calls.append(cmd) or Result())
    r = archive_tools.craft("zip_slip", "../../../x")
    assert r["mode"] == "real"
    assert calls[0] == ["/opt/tools/archive-wrapper", "zip_slip", "../../../x"]
    assert r["external_tool"]["returncode"] == 0 and r["external_tool"]["ok"] is True

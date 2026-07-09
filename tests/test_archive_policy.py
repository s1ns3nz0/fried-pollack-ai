"""archive external wrapper 로컬 실행 정책 (고도화 작업 6).

ARCHIVE_TOOL_CMD 는 로컬 명령 실행이므로 §T 네트워크 샌드박스와 별개 정책이 필요.
- 절대경로 allowlist (상대경로/PATH 탐색 거부)
- 선택적 ARCHIVE_TOOL_ALLOWED 로 경로 화이트리스트 좁힘
- cwd/env 격리 (상속 차단)
- stdout/stderr 크기 상한
- nonzero returncode / exec 실패 구조화
"""
from __future__ import annotations

import subprocess

import pytest

from redteam_core.integrations import archive_tools


@pytest.fixture(autouse=True)
def _tool_env(monkeypatch):
    monkeypatch.setenv("ARCHIVE_TOOL", "evilarc")
    monkeypatch.delenv("ARCHIVE_TOOL_ALLOWED", raising=False)


def _no_run(monkeypatch):
    """subprocess.run 이 호출되면 실패시켜 '실행 안 됨'을 증명."""
    def _boom(*a, **k):
        raise AssertionError("subprocess.run must not be called")
    monkeypatch.setattr(archive_tools.subprocess, "run", _boom)


def test_relative_command_rejected_without_exec(monkeypatch):
    _no_run(monkeypatch)
    monkeypatch.setenv("ARCHIVE_TOOL_CMD", "evilarc")   # 절대경로 아님
    ext = archive_tools._run_external("zip_slip")
    assert ext["ok"] is False and ext["error"]["type"] == "policy"


def test_command_not_in_allowlist_rejected(monkeypatch):
    _no_run(monkeypatch)
    monkeypatch.setenv("ARCHIVE_TOOL_CMD", "/opt/tools/archive-wrapper")
    monkeypatch.setenv("ARCHIVE_TOOL_ALLOWED", "/usr/local/bin/evilarc")
    ext = archive_tools._run_external("zip_slip")
    assert ext["ok"] is False and ext["error"]["type"] == "policy"


def test_allowlisted_command_runs(monkeypatch):
    seen = {}

    class R:
        returncode = 0
        stdout = "done"
        stderr = ""

    def _run(cmd, capture_output, text, timeout, cwd, env):
        seen.update(cmd=cmd, cwd=cwd, env=env, timeout=timeout)
        return R()

    monkeypatch.setattr(archive_tools.subprocess, "run", _run)
    monkeypatch.setenv("ARCHIVE_TOOL_CMD", "/opt/tools/archive-wrapper")
    monkeypatch.setenv("ARCHIVE_TOOL_ALLOWED", "/opt/tools/archive-wrapper")
    ext = archive_tools._run_external("zip_slip", "../../x")
    assert ext["ok"] is True and ext["returncode"] == 0
    assert seen["cmd"] == ["/opt/tools/archive-wrapper", "zip_slip", "../../x"]
    assert seen["cwd"] and seen["cwd"] != "."           # 격리 cwd
    assert "PATH" in seen["env"] and "ARCHIVE_TOOL_CMD" not in seen["env"]  # 최소 env


def test_stdout_truncated_when_oversized(monkeypatch):
    class R:
        returncode = 0
        stdout = "A" * (200 * 1024)
        stderr = ""

    monkeypatch.setattr(archive_tools.subprocess, "run",
                        lambda *a, **k: R())
    monkeypatch.setenv("ARCHIVE_TOOL_CMD", "/opt/tools/archive-wrapper")
    ext = archive_tools._run_external("zip_slip")
    assert ext["truncated"] is True
    assert len(ext["stdout"]) <= archive_tools._MAX_OUTPUT


def test_nonzero_returncode_flagged(monkeypatch):
    class R:
        returncode = 2
        stdout = ""
        stderr = "fail"

    monkeypatch.setattr(archive_tools.subprocess, "run", lambda *a, **k: R())
    monkeypatch.setenv("ARCHIVE_TOOL_CMD", "/opt/tools/archive-wrapper")
    ext = archive_tools._run_external("zip_slip")
    assert ext["ok"] is False and ext["error"]["type"] == "returncode"


def test_exec_failure_structured(monkeypatch):
    def _raise(*a, **k):
        raise FileNotFoundError("no such tool")

    monkeypatch.setattr(archive_tools.subprocess, "run", _raise)
    monkeypatch.setenv("ARCHIVE_TOOL_CMD", "/opt/tools/archive-wrapper")
    ext = archive_tools._run_external("zip_slip")
    assert ext["ok"] is False and ext["error"]["type"] == "exec"


def test_timeout_is_structured_not_raised(monkeypatch):
    def _timeout(*a, **k):
        raise subprocess.TimeoutExpired(cmd="x", timeout=30)

    monkeypatch.setattr(archive_tools.subprocess, "run", _timeout)
    monkeypatch.setenv("ARCHIVE_TOOL_CMD", "/opt/tools/archive-wrapper")
    ext = archive_tools._run_external("zip_slip")
    assert ext["ok"] is False and ext["error"]["type"] == "exec"


def test_craft_policy_block_stays_fallback(monkeypatch):
    """정책 거부 시 craft 는 real 로 승격하지 않고 fallback 유지."""
    _no_run(monkeypatch)
    monkeypatch.setenv("ARCHIVE_TOOL_CMD", "evilarc")   # 상대경로 → 거부
    r = archive_tools.craft("zip_slip", "../../x")
    assert r["mode"] == "fallback"
    assert r["external_tool_implemented"] is False
    assert r["external_tool"]["error"]["type"] == "policy"

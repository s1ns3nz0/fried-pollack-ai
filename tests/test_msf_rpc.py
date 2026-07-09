"""Metasploit RPC 경로 검증 (고도화 작업 7) — fake pymetasploit3 주입.

MCP 경로는 test_msf_cve 에서 검증됨. RPC 경로(_run_real 의 MsfRpcClient 분기)는
코드만 있고 fake 테스트가 약했음. fake MsfRpcClient 를 sys.modules 로 주입해
modules.use / options 대입 / module.execute() 결과 배선을 검증한다.
"""
from __future__ import annotations

import sys
import types

import pytest

from redteam_core.integrations import metasploit

IN_SCOPE = "10.50.0.50"


class _FakeModule(dict):
    """msf 모듈 = dict 형 옵션 컨테이너 + execute()."""

    def __init__(self):
        super().__init__()
        self.executed = False

    def execute(self):
        self.executed = True
        return {"job_id": 7, "uuid": "abc", "options": dict(self)}


class _FakeModules:
    def __init__(self):
        self.used = []
        self.module = _FakeModule()

    def use(self, kind, name):
        self.used.append((kind, name))
        return self.module


class _FakeClient:
    last = None

    def __init__(self, password, server="", port=0, ssl=False):
        self.password = password
        self.server = server
        self.port = port
        self.modules = _FakeModules()
        _FakeClient.last = self


@pytest.fixture
def _fake_pymsf(monkeypatch):
    """fake pymetasploit3(.msfrpc.MsfRpcClient) 를 import 경로에 주입."""
    pkg = types.ModuleType("pymetasploit3")
    msfrpc = types.ModuleType("pymetasploit3.msfrpc")
    msfrpc.MsfRpcClient = _FakeClient
    pkg.msfrpc = msfrpc
    monkeypatch.setitem(sys.modules, "pymetasploit3", pkg)
    monkeypatch.setitem(sys.modules, "pymetasploit3.msfrpc", msfrpc)
    _FakeClient.last = None
    return _FakeClient


@pytest.fixture(autouse=True)
def _rpc_env(monkeypatch):
    monkeypatch.delenv("MSF_MCP_URL", raising=False)   # RPC 경로 강제
    monkeypatch.setenv("MSF_RPC_HOST", IN_SCOPE)
    monkeypatch.setenv("MSF_RPC_PORT", "55553")
    monkeypatch.setenv("MSF_RPC_PASSWORD", "secret")


def test_rpc_available_when_lib_and_env_present(_fake_pymsf):
    assert metasploit.available() is True
    assert metasploit.status()["transport"] == "rpc"


def test_rpc_run_module_uses_module_and_sets_options(_fake_pymsf):
    r = metasploit.run_module("auxiliary/scanner/portscan/tcp", {"RHOSTS": "10.50.0.9"})
    client = _fake_pymsf.last
    assert client is not None
    assert client.password == "secret" and client.server == IN_SCOPE and client.port == 55553
    assert client.modules.used == [("auxiliary", "scanner/portscan/tcp")]
    assert client.modules.module["RHOSTS"] == "10.50.0.9"          # 옵션 대입
    assert client.modules.module.executed is True                  # execute() 호출


def test_rpc_run_module_response_and_ok(_fake_pymsf):
    r = metasploit.run_module("auxiliary/scanner/portscan/tcp", {"RHOSTS": "10.50.0.9"})
    assert r["mode"] == "real" and r["transport"] == "rpc"
    assert r["response"]["job_id"] == 7                            # execute() 결과 배선
    assert r["ok"] is True and r["error"] is None                  # 작업 5 shape


def test_rpc_out_of_scope_blocked_before_client(_fake_pymsf, monkeypatch):
    monkeypatch.setenv("MSF_RPC_HOST", "203.0.113.10")
    r = metasploit.run_module("auxiliary/scanner/portscan/tcp", {"RHOSTS": "x"})
    assert r["mode"] == "blocked_by_sandbox"
    assert _fake_pymsf.last is None                                # 클라이언트 미생성


def test_rpc_unavailable_falls_back_when_lib_missing(monkeypatch):
    """pymetasploit3 미설치면 available()=False → dry 플랜 폴백."""
    monkeypatch.setitem(sys.modules, "pymetasploit3", None)        # import 실패 유발
    r = metasploit.run_module("auxiliary/scanner/portscan/tcp", {"RHOSTS": "x"})
    assert r["mode"] == "fallback(dry)"

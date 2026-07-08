"""detonation 샌드박스 테스트 — 고도화 §T. 결정론·무의존."""
from __future__ import annotations

import os

from redteam_core.sandbox import DetonationSandbox, SandboxPolicy


def _sbx(cidrs=None):
    return DetonationSandbox(SandboxPolicy(allowed_cidrs=cidrs or ["10.50.0.0/24"]))


def test_persistence_implant_flagged_malicious_and_contained():
    r = _sbx().detonate({"name": "impl", "files": [(".implant", b"x")],
                         "params": {"BRD_SAFETYENABLE": 0}})
    assert r.verdict == "malicious"
    assert any("지속성" in i for i in r.indicators)
    assert any("안전 파라미터" in i for i in r.indicators)
    assert r.contained is True                   # FS 롤백 봉인


def test_egress_outside_scope_blocked():
    r = _sbx(["10.50.0.0/24"]).detonate({"name": "c2", "network": [("203.0.113.66", 8080)]})
    assert r.egress_blocked == ["203.0.113.66:8080"] and r.egress_allowed == []
    assert r.verdict == "suspicious"


def test_egress_within_scope_allowed():
    r = _sbx(["10.50.0.0/24"]).detonate({"name": "c2", "network": [("10.50.0.20", 5790)]})
    assert r.egress_allowed == ["10.50.0.20:5790"] and r.egress_blocked == []


def test_default_deny_when_no_allowlist():
    r = DetonationSandbox(SandboxPolicy(allowed_cidrs=[])).detonate(
        {"name": "c2", "network": [("10.50.0.20", 5790)]})
    assert r.egress_blocked == ["10.50.0.20:5790"]      # allowlist 비면 전부 차단


def test_domain_target_failclosed():
    r = _sbx().detonate({"name": "c2", "network": [("sim.pollak.store", 443)]})
    assert "sim.pollak.store:443" in r.egress_blocked   # 도메인=해석필요→차단


def test_rollback_leaves_no_files():
    r = _sbx().detonate({"name": "impl", "files": [("payload.bin", b"data")]})
    assert r.files_written == ["payload.bin"] and r.contained is True


def test_benign_when_no_indicators():
    r = _sbx().detonate({"name": "scan", "network": [("10.50.0.10", 5790)]})
    assert r.verdict == "benign"

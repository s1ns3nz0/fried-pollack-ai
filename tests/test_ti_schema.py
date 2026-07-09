"""TAXII/CTID schema 대응 강화 (고도화 작업 4).

실 피드 파서를 fake get_json 주입으로 검증한다:
- TAXII 2.1 collection objects (intrusion-set 추출)
- CTID JSON manifest 두 형태({actor:[sids]} / {"plans":[{actor,chain}]})
- malformed/error schema → seed fallback + warning 필드
"""
from __future__ import annotations

import pytest

from redteam_core.integrations import apt_emulation, threat_intel


# ── TAXII (threat_intel) ─────────────────────────────────────────────────────

@pytest.fixture
def _taxii_env(monkeypatch):
    monkeypatch.setenv("TAXII_URL", "http://ti.local/taxii2/collections/x/objects")
    monkeypatch.setenv("TAXII_COLLECTION", "x")


def test_taxii21_objects_parsed(monkeypatch, _taxii_env):
    feed = {"objects": [
        {"type": "intrusion-set", "name": "APT-Feed-1"},
        {"type": "malware", "name": "ignore-me"},
        {"type": "intrusion-set", "name": "APT-Feed-2"},
    ]}
    monkeypatch.setattr(threat_intel, "get_json", lambda url, **k: feed)
    d = threat_intel.taxii_actors_detail()
    assert d["source"] == "taxii" and d["warning"] is None
    assert d["actors"] == ["APT-Feed-1", "APT-Feed-2"]
    assert threat_intel.active_actors() == ["APT-Feed-1", "APT-Feed-2"]


def test_taxii_malformed_missing_objects_falls_back_with_warning(monkeypatch, _taxii_env):
    monkeypatch.setattr(threat_intel, "get_json", lambda url, **k: {"unexpected": 1})
    d = threat_intel.taxii_actors_detail()
    assert d["source"] == "seed_fallback"
    assert d["warning"] and "objects" in d["warning"]
    assert d["actors"] == list(threat_intel.THREAT_ACTORS)     # 시드 유지


def test_taxii_http_error_falls_back_with_warning(monkeypatch, _taxii_env):
    err = {"error": {"type": "transport", "reason": "conn refused"}}
    monkeypatch.setattr(threat_intel, "get_json", lambda url, **k: err)
    d = threat_intel.taxii_actors_detail()
    assert d["source"] == "seed_fallback" and "error" in d["warning"].lower()


def test_taxii_non_dict_response_falls_back(monkeypatch, _taxii_env):
    monkeypatch.setattr(threat_intel, "get_json", lambda url, **k: {"data": [1, 2]})
    d = threat_intel.taxii_actors_detail()
    assert d["source"] == "seed_fallback" and d["warning"]


# ── CTID (apt_emulation) ─────────────────────────────────────────────────────

@pytest.fixture
def _ctid_env(monkeypatch):
    monkeypatch.setenv("CTID_PLAN_URL", "http://ctid.local/plan.json")


def test_ctid_actor_keyed_manifest(monkeypatch, _ctid_env):
    monkeypatch.setattr(apt_emulation, "get_json",
                        lambda url, **k: {"APT28 (G0007)": ["S1", "S2", "S3"]})
    d = apt_emulation.ctid_plan_detail("APT28 (G0007)")
    assert d["source"] == "ctid" and d["chain"] == ["S1", "S2", "S3"]
    assert apt_emulation.emulation_plan("APT28 (G0007)") == ["S1", "S2", "S3"]


def test_ctid_plans_array_manifest(monkeypatch, _ctid_env):
    feed = {"plans": [
        {"actor": "Other", "chain": ["Z1"]},
        {"actor": "APT28 (G0007)", "chain": ["S9", "S8"]},
    ]}
    monkeypatch.setattr(apt_emulation, "get_json", lambda url, **k: feed)
    d = apt_emulation.ctid_plan_detail("APT28 (G0007)")
    assert d["source"] == "ctid" and d["chain"] == ["S9", "S8"]


def test_ctid_actor_not_found_falls_back_with_warning(monkeypatch, _ctid_env):
    monkeypatch.setattr(apt_emulation, "get_json",
                        lambda url, **k: {"plans": [{"actor": "Other", "chain": ["Z1"]}]})
    d = apt_emulation.ctid_plan_detail("APT28 (G0007)")
    assert d["source"] == "seed_fallback"
    assert d["warning"] and "APT28" in d["warning"]
    assert d["chain"] == apt_emulation.APT_EMULATION["APT28 (G0007)"]


def test_ctid_http_error_falls_back_with_warning(monkeypatch, _ctid_env):
    monkeypatch.setattr(apt_emulation, "get_json",
                        lambda url, **k: {"error": {"type": "http_status", "status": 500}})
    d = apt_emulation.ctid_plan_detail("APT28 (G0007)")
    assert d["source"] == "seed_fallback" and "error" in d["warning"].lower()


def test_ctid_non_dict_falls_back(monkeypatch, _ctid_env):
    monkeypatch.setattr(apt_emulation, "get_json", lambda url, **k: {"data": [1]})
    d = apt_emulation.ctid_plan_detail("APT28 (G0007)")
    assert d["source"] == "seed_fallback" and d["warning"]

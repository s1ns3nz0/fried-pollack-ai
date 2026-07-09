"""integration result 공통 shape 검증 (고도화 작업 5).

http_json 은 실패 시 {"error": {...}} 를 반환하지만, adapter 들은 그것을 그대로
response/record 로 담을 뿐 ok/error 의미를 표준화하지 않았음. finalize() 로
공통 필드(ok, error)를 승격한다.
"""
from __future__ import annotations

from redteam_core.integrations.result import finalize


def test_finalize_promotes_transport_error():
    r = finalize({"mode": "real", "response": {"error": {"type": "transport", "reason": "boom"}}},
                 "response")
    assert r["ok"] is False
    assert r["error"] == {"type": "transport", "reason": "boom"}


def test_finalize_promotes_http_status_error():
    r = finalize({"mode": "real", "record": {"error": {"type": "http_status", "status": 500}}},
                 "record")
    assert r["ok"] is False
    assert r["error"]["status"] == 500


def test_finalize_ok_when_payload_has_no_error():
    r = finalize({"mode": "real", "response": {"id": "op-1"}}, "response")
    assert r["ok"] is True
    assert r["error"] is None


def test_finalize_ok_when_payload_missing_or_none():
    r = finalize({"mode": "real", "record": None}, "record")
    assert r["ok"] is True
    assert r["error"] is None


def test_finalize_preserves_existing_fields_and_returns_same_dict():
    src = {"mode": "real", "chain": "C1", "response": {"id": "x"}}
    out = finalize(src, "response")
    assert out is src
    assert out["chain"] == "C1" and out["response"] == {"id": "x"}

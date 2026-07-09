"""integration result shape 표준화 — 공통 ok/error 필드.

http_json 은 실패를 {"error": {...}} 로 반환한다. adapter 실 경로는 그 payload 를
response/record 로 담는데, 소비자가 성공/실패를 판정하려면 매번 payload 를 뒤져야 했다.
finalize() 는 payload 안의 error 를 top-level 로 승격해 결과 계약을 통일한다:

    {..., "ok": bool, "error": dict | None}

- payload 에 {"error": ...} 있으면 ok=False, error=그 dict.
- 없거나 payload 가 None/비-dict 면 ok=True, error=None.
"""
from __future__ import annotations


def finalize(result: dict, payload_key: str) -> dict:
    """result[payload_key] 안의 transport-level error 를 ok/error 로 승격(in-place)."""
    payload = result.get(payload_key)
    err = payload.get("error") if isinstance(payload, dict) else None
    result["ok"] = err is None
    result["error"] = err
    return result

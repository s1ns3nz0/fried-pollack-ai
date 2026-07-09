"""Small stdlib JSON HTTP helpers for optional integrations."""

from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def post_json(url: str, body: dict, headers: dict | None = None, timeout_s: float = 10.0) -> dict:
    data = json.dumps(body).encode("utf-8")
    req = Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, str(v))
    return _request_json(req, timeout_s)


def get_json(url: str, headers: dict | None = None, timeout_s: float = 10.0) -> dict:
    req = Request(url, method="GET")
    req.add_header("Accept", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, str(v))
    return _request_json(req, timeout_s)


def _request_json(req: Request, timeout_s: float) -> dict:
    try:
        with urlopen(req, timeout=timeout_s) as resp:  # nosec: callers scope-gate live endpoints
            return _decode_json(resp.read())
    except HTTPError as exc:
        return {"error": {"type": "http_status", "status": exc.code,
                          "reason": exc.reason, "body": _decode_body(exc.read())}}
    except (URLError, TimeoutError, OSError) as exc:
        return {"error": {"type": "transport", "reason": str(exc)}}


def _decode_json(raw: bytes) -> dict:
    if not raw:
        return {}
    text = raw.decode("utf-8", errors="replace")
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return {"error": {"type": "invalid_json", "body": text}}
    return value if isinstance(value, dict) else {"data": value}


def _decode_body(raw: bytes):
    if not raw:
        return ""
    text = raw.decode("utf-8", errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text

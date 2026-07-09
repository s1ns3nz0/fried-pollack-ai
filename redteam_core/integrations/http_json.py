"""Small stdlib JSON HTTP helpers for optional integrations."""

from __future__ import annotations

import json
from urllib.request import Request, urlopen


def post_json(url: str, body: dict, headers: dict | None = None, timeout_s: float = 10.0) -> dict:
    data = json.dumps(body).encode("utf-8")
    req = Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, str(v))
    with urlopen(req, timeout=timeout_s) as resp:  # nosec: URL is scope-gated by callers
        raw = resp.read()
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8"))


def get_json(url: str, headers: dict | None = None, timeout_s: float = 10.0) -> dict:
    req = Request(url, method="GET")
    req.add_header("Accept", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, str(v))
    with urlopen(req, timeout=timeout_s) as resp:  # nosec: caller controls integration endpoint
        raw = resp.read()
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8"))

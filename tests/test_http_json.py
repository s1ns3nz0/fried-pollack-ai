"""HTTP JSON integration helper contract tests."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from redteam_core.integrations.http_json import get_json, post_json


def _serve(handler_cls):
    srv = HTTPServer(("127.0.0.1", 0), handler_cls)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    host, port = srv.server_address
    return srv, f"http://{host}:{port}"


class _JSONHandler(BaseHTTPRequestHandler):
    seen = {}

    def do_POST(self):
        ln = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(ln)
        type(self).seen = {
            "path": self.path,
            "body": json.loads(body.decode("utf-8")),
            "content_type": self.headers.get("Content-Type"),
            "custom": self.headers.get("X-Test"),
        }
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok": true}')

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"items": [1, 2]}')

    def log_message(self, *_args):
        pass


def test_post_json_sends_headers_body_and_parses_response():
    srv, base = _serve(_JSONHandler)
    try:
        result = post_json(base + "/tools/run", {"module": "x"}, headers={"X-Test": "yes"})
    finally:
        srv.shutdown()
        srv.server_close()
    assert result == {"ok": True}
    assert _JSONHandler.seen == {
        "path": "/tools/run",
        "body": {"module": "x"},
        "content_type": "application/json",
        "custom": "yes",
    }


def test_get_json_parses_response():
    srv, base = _serve(_JSONHandler)
    try:
        assert get_json(base + "/feed") == {"items": [1, 2]}
    finally:
        srv.shutdown()
        srv.server_close()


class _NoContentHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(204)
        self.end_headers()

    def log_message(self, *_args):
        pass


def test_empty_success_body_returns_empty_dict():
    srv, base = _serve(_NoContentHandler)
    try:
        assert post_json(base + "/empty", {}) == {}
    finally:
        srv.shutdown()
        srv.server_close()


class _ErrorHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(500)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"message": "broken"}')

    def log_message(self, *_args):
        pass


def test_http_error_returns_structured_error():
    srv, base = _serve(_ErrorHandler)
    try:
        result = get_json(base + "/bad")
    finally:
        srv.shutdown()
        srv.server_close()
    assert result["error"]["type"] == "http_status"
    assert result["error"]["status"] == 500
    assert result["error"]["body"] == {"message": "broken"}


class _InvalidJsonHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b"not-json")

    def log_message(self, *_args):
        pass


def test_invalid_json_returns_structured_error():
    srv, base = _serve(_InvalidJsonHandler)
    try:
        result = get_json(base + "/bad-json")
    finally:
        srv.shutdown()
        srv.server_close()
    assert result["error"]["type"] == "invalid_json"
    assert result["error"]["body"] == "not-json"

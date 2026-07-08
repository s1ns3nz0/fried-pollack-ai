"""ArduPilot SITL 연동 — §K/§C 실 텔레메트리 (env 표적).

§K 전송의 env 미구현을 바로잡는다: MAVLINK_ENDPOINT/C2_HOST/STUB_URL 을 env 에서
읽어 실 표적(uav-sim-env)으로 전송하고, 미지정 시 loopback/결정론 폴백.
"""
from __future__ import annotations

import os
from typing import Optional


def endpoints() -> dict:
    """env 기반 실 표적 엔드포인트(미지정 시 빈 값 = 폴백)."""
    return {
        "mavlink": os.environ.get("MAVLINK_ENDPOINT", ""),
        "c2_host": os.environ.get("C2_HOST", ""),
        "c2_port": int(os.environ.get("C2_PORT", "0") or 0),
        "stub_url": os.environ.get("STUB_URL", ""),
    }


def available() -> bool:
    if not endpoints()["mavlink"]:
        return False
    try:
        import pymavlink  # noqa: F401
        return True
    except Exception:
        return False


def status() -> dict:
    ep = endpoints()
    return {"available": available(), "mavlink_endpoint": ep["mavlink"] or None,
            "mode": "real" if available() else "fallback"}


def inject_gps_spoof(lat_e7: int = 367100000, lon_e7: int = 1261300000,
                     alt_m: float = 80.0) -> dict:
    """GNSS 스푸핑 프레임을 실 mavlink-router 로 전송(env), 아니면 폴백."""
    from ..transport import build_mavlink_gps_frame, udp_deliver
    frame = build_mavlink_gps_frame(lat_e7, lon_e7, alt_m)
    ep = endpoints()
    if available():  # pragma: no cover
        host, _, port = ep["mavlink"].partition(":")
        n = udp_deliver(host, int(port or 14550), frame)
        return {"mode": "real", "endpoint": ep["mavlink"], "bytes": n}
    return {"mode": "fallback", "frame_bytes": len(frame),
            "note": "MAVLINK_ENDPOINT 미지정 → 전송 안 함(결정론 폴백)"}

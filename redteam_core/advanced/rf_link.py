"""RC 조종링크 + DShot 모터 공격 — S43~S46 (Awesome-Drone-Hacking).

RC 링크(DSMX/FrSky/ELRS)와 DShot/ESC 모터 프로토콜은 WiFi/MAVLink와 별개인
공격면이다. 실 RF/모터 조작은 SDR/ESC 어댑터+env+§T 샌드박스 통과 시에만.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass

RF_SCENARIOS = {
    "S43": {"name": "RC 링크 바인딩 탈취", "objective": "rc_link_hijack",
            "mitre": "T1557 / RC bind", "proto": "DSMX/FrSky/ELRS"},
    "S44": {"name": "RC override 명령 주입", "objective": "rc_override",
            "mitre": "T0831 / RC override", "proto": "RC channels"},
    "S45": {"name": "RC 프로토콜 다운그레이드", "objective": "rc_downgrade",
            "mitre": "T1600 / downgrade", "proto": "무암호 폴백"},
    "S46": {"name": "DShot/ESC 모터 조작", "objective": "dshot_motor",
            "mitre": "T0855 / actuator", "proto": "DShot600"},
}


@dataclass
class RfResult:
    scenario: str
    artifact: str
    transmitted: bool
    note: str = ""


def _build(sid: str) -> str:
    m = RF_SCENARIOS[sid]
    if sid == "S43":
        return "bind pkt " + json.dumps({"proto": m["proto"], "action": "steal_bind"})
    if sid == "S44":
        return "RC override ch=[1500,1500,2000,1500] (throttle↑)"
    if sid == "S45":
        return "downgrade→무암호 RC 재바인딩 유도"
    return "DShot600 cmd=[MOTOR_STOP] (오토파일럿 우회 직접 ESC)"


def run_rf(scenario_id: str, dry: bool = True) -> RfResult:
    art = _build(scenario_id)
    iface = os.environ.get("SDR_IFACE" if scenario_id != "S46" else "ESC_IFACE", "")
    sent = False
    if not dry and iface:
        from ..sandbox import guarded
        r = guarded({"name": f"rf:{scenario_id}", "network": []}, lambda: {"sent": True})
        sent = "sent" in r
    return RfResult(scenario_id, art, sent,
                    "실 RF/모터 조작=하드웨어 어댑터+§T 샌드박스(무동작 기본)")

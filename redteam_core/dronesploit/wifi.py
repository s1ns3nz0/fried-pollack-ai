"""WiFi 계층 공격 — deauth·evil twin·WiFi 재밍·비콘 (S25~S28).

소형/전술 UAS(COTS WiFi 제어)의 802.11 공격면. 실 주입은 monitor 어댑터+env+§T
샌드박스 통과 시에만(기본 dry: 아티팩트만). 실 RF/deauth 무방사 기본.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass

# S25~S28 시나리오 메타
WIFI_SCENARIOS = {
    "S25": {"name": "WiFi Deauth(링크 거부)", "objective": "wifi_deauth",
            "mitre": "T1499 / 802.11 deauth", "action": "wifi_deauth"},
    "S26": {"name": "Evil Twin(C2 하이재킹)", "objective": "wifi_evil_twin",
            "mitre": "T1557 / rogue AP", "action": "wifi_evil_twin"},
    "S27": {"name": "WiFi 재밍(통제 상실)", "objective": "wifi_jam",
            "mitre": "T1499 / RF DoS", "action": "wifi_jam"},
    "S28": {"name": "기본 자격증명/SSID 변조", "objective": "wifi_cred",
            "mitre": "T1078 / default creds", "action": "wifi_cred"},
}


@dataclass
class WifiResult:
    scenario: str
    artifact: str
    transmitted: bool
    note: str = ""


def build_deauth_frame(bssid: str = "aa:bb:cc:dd:ee:ff", client: str = "ff:ff:ff:ff:ff:ff"):
    """802.11 deauth 관리프레임(요지). 실 주입은 scapy/aircrack + monitor 어댑터."""
    return b"IEEE80211_DEAUTH:" + json.dumps(
        {"type": "mgmt/deauth", "bssid": bssid, "client": client, "reason": 7}).encode()


def build_evil_twin(ssid: str = "MPD-GCS", channel: int = 6):
    """rogue AP(evil twin) 설정 — 동일 SSID로 드론 재접속 유도."""
    return {"ssid": ssid, "channel": channel, "open": True, "rogue": True,
            "note": "동일 SSID rogue AP → 드론 C2 하이재킹"}


def run_wifi(scenario_id: str, dry: bool = True) -> WifiResult:
    """WiFi 시나리오 실행(dry=아티팩트만). 실 주입은 env WIFI_IFACE + §T 샌드박스."""
    meta = WIFI_SCENARIOS[scenario_id]
    act = meta["action"]
    if act == "wifi_deauth":
        art = f"deauth frame {len(build_deauth_frame())}B"
    elif act == "wifi_evil_twin":
        art = f"evil twin AP {build_evil_twin()['ssid']}"
    elif act == "wifi_jam":
        art = "WiFi 재밍(2.4/5G) — 물리(무방사)"
    else:
        art = "기본 자격증명 스프레이/SSID 변조"

    iface = os.environ.get("WIFI_IFACE", "")
    transmitted = False
    if not dry and iface and act != "wifi_jam":     # 재밍은 무방사
        from ..sandbox import guarded
        spec = {"name": f"wifi:{act}", "network": []}
        r = guarded(spec, lambda: {"sent": True})
        transmitted = "sent" in r
    return WifiResult(scenario_id, art, transmitted,
                      "실 802.11 주입=monitor 어댑터+§T 샌드박스" if act != "wifi_jam" else "실 RF 금지")

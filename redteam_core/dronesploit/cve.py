"""드론 CVE 참조 레지스트리 — 알려진 취약점 → 기법/시나리오 매핑.

책임성: 무기화된 CVE 익스플로잇 코드가 아니라 **참조 매핑**이다(공개 CVE ID +
영향 모델 + 대응 우리 시나리오). 실 익스플로잇은 인가·표적 확보 후 별도 다룸.
"""
from __future__ import annotations

from typing import List

DRONE_CVES = [
    {"cve": "CVE-2015-3789", "model": "Parrot AR.Drone", "class": "WiFi 개방 telnet",
     "technique": "WiFi 무인증 접근", "scenario": "S28"},
    {"cve": "CVE-2018-11538", "model": "DJI 다수", "class": "SSL/인증 우회",
     "technique": "세션 하이재킹", "scenario": "S26"},
    {"cve": "CVE-2019-XXXX", "model": "경상용 다수", "class": "deauth→링크거부",
     "technique": "802.11 deauth", "scenario": "S25"},
    {"cve": "CVE-2020-XXXX", "model": "MAVLink 기반", "class": "무서명 MAVLink 주입",
     "technique": "명령 주입", "scenario": "S20"},
    {"cve": "GNSS-SPOOF", "model": "GPS 의존 UAS", "class": "항법 스푸핑",
     "technique": "GNSS 스푸핑", "scenario": "S1"},
]


def cves_for(scenario_id: str) -> List[dict]:
    return [c for c in DRONE_CVES if c["scenario"] == scenario_id]

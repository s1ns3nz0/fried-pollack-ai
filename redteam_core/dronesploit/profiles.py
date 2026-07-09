"""소형/COTS UAS 표적 프로파일 — dronesploit 영감.

군도 COTS 소형드론(WiFi 제어·평문 텔레메트리)을 운용하므로 표적면을 확대.
각 프로파일에 공격면과 적용 가능 시나리오를 매핑.
"""
from __future__ import annotations

COTS_PROFILES = {
    "cots_wifi_micro": {
        "class": "소비자 WiFi 마이크로드론",
        "control": "802.11(2.4GHz)", "telemetry": "평문",
        "surface": ["WiFi deauth", "evil twin", "기본 자격증명", "WiFi 재밍"],
        "scenarios": ["S25", "S26", "S27", "S28"],
    },
    "tactical_small_uas": {
        "class": "전술 소형 UAS(COTS 파생)",
        "control": "802.11 + 일부 MAVLink", "telemetry": "부분 암호화",
        "surface": ["WiFi deauth", "evil twin", "MAVLink 주입", "GNSS 스푸핑"],
        "scenarios": ["S25", "S26", "S1", "S20"],
    },
    "male_muav": {
        "class": "MALE(KUS-FS) — 기존 표적",
        "control": "LOS RF + SATCOM(MAVLink)", "telemetry": "암호화",
        "surface": ["MAVLink 주입", "SATCOM MITM", "GNSS 스푸핑/재밍", "GCS 침해"],
        "scenarios": ["S1", "S17", "S18", "S34", "S23"],
    },
}


def profiles_for_surface(keyword: str) -> list:
    """공격면 키워드로 해당 표적 프로파일 검색."""
    return [name for name, p in COTS_PROFILES.items()
            if any(keyword in s for s in p["surface"])]

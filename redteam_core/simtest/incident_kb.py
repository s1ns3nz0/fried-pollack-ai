"""인시던트 지식베이스 → 공격 시나리오 도출·근거화 (S-Agent 전이).

실 sUAS 사고/보안 인시던트 패턴을 KB로 두고, 각 인시던트를 재현하는 공격 시나리오를
매핑한다. 시나리오에 '실 인시던트 근거(provenance)'를 부여(발표 정당성).
"""
from __future__ import annotations

from typing import List

# 인시던트 클래스 → (원인, 재현 공격 시나리오, 근거)
INCIDENT_KB = [
    {"incident": "GPS loss flyaway", "cause": "GNSS 상실/스푸핑", "scenario": "S1",
     "provenance": "다수 소비자·군용 드론 flyaway 사고"},
    {"incident": "Compass toilet-bowling", "cause": "지자기 간섭/오류", "scenario": "S58",
     "provenance": "자기간섭 원형선회 사고 다발"},
    {"incident": "Baro altitude drift", "cause": "기압 급변/폴트", "scenario": "S57",
     "provenance": "고도 오판 지형충돌"},
    {"incident": "IMU vibration fault", "cause": "관성센서 오염", "scenario": "S56",
     "provenance": "자세추정 실패 추락"},
    {"incident": "RC link loss failsafe", "cause": "조종링크 상실", "scenario": "S43",
     "provenance": "RC 상실 failsafe 오작동"},
    {"incident": "Airspeed stall", "cause": "에어스피드 오류", "scenario": "S59",
     "provenance": "고정익 실속 사고"},
    {"incident": "GCS command hijack", "cause": "MAVLink 무인증 주입", "scenario": "S18",
     "provenance": "MAVLink 무서명 취약(MAVSec)"},
]


def scenarios_from_incidents() -> List[dict]:
    """인시던트 KB에서 근거화된 공격 시나리오 목록 도출."""
    return [{"scenario": i["scenario"], "from_incident": i["incident"],
             "cause": i["cause"], "provenance": i["provenance"]} for i in INCIDENT_KB]

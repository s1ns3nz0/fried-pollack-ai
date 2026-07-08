"""dronesploit — WiFi 계층 공격 + COTS UAS 표적 + 모듈 프레임 + CVE (§V).

dronesploit(sploitkit 기반 드론 펜테스트) 영감. 우리 에이전트의 MAVLink/EMSO/AI
공격면에 **802.11 WiFi 계층**과 **소형·COTS UAS 표적**을 더한다.

안전: WiFi 프레임/AP 는 아티팩트만 생성(dry). 실 802.11 주입은 monitor 어댑터
+ env + §T 샌드박스 통과 시에만(실 RF/deauth 무방사 기본, fail-closed).
"""
from .wifi import WIFI_SCENARIOS, build_deauth_frame, build_evil_twin, run_wifi
from .profiles import COTS_PROFILES
from .module import Module, MODULE_REGISTRY, load_module
from .cve import DRONE_CVES, cves_for

__all__ = [
    "WIFI_SCENARIOS", "build_deauth_frame", "build_evil_twin", "run_wifi",
    "COTS_PROFILES", "Module", "MODULE_REGISTRY", "load_module",
    "DRONE_CVES", "cves_for",
]

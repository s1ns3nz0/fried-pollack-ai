"""groundseg — 지상 세그먼트 소프트웨어 공격 (공격면 도메인).

UAV 기체(공중 세그먼트) 외 **지상/인프라 소프트웨어** 공격면. 4요소:
  - GCS 애플리케이션 S41~S44 (QGC/Mission Planner)
  - 컴패니언/ROS       S45~S47 (온보드 Linux·ROS/MAVROS)
  - 지상 인프라/데이터링크 S48~S50 (모뎀·SATCOM·GDT)
  - 함대/인프라 백엔드   S81~S84 (함대API·영상스트림·C4I)

발견: UAV Sentinel(blue)은 텔레메트리/공중 평면만 감시 → 지상 소프트웨어 = 사각지대.
안전: 아티팩트만(dry). 실 공격은 표적 env + §T 샌드박스 통과 시에만.
"""
from .attacks import GROUND_SCENARIOS, build_artifact, run_ground, surfaces
from .executor import (
    build_ntp_spoof, build_rtsp_describe, execute_real, payload_bytes,
)

__all__ = ["GROUND_SCENARIOS", "build_artifact", "run_ground", "surfaces",
           "execute_real", "payload_bytes", "build_ntp_spoof", "build_rtsp_describe"]

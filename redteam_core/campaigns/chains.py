"""캠페인 체인 실행 — 시나리오 시퀀스를 순서 수행하고 탐지 프로파일 산출.

각 단계 시나리오를 대표 실행(action+intensity)하거나, 에이전트 미배선·배포룰만
있는 시나리오는 알려진 탐지상태(static)로 처리한다.
  - completed: 전 단계가 효과 달성(공격 실행됨).
  - stealthy : 어느 단계도 탐지 True 아님(전 단계 사각/회피).
  - 탐지 관통: completed 이나 일부 단계 탐지 → 방어 상관룰이 잡을 수 있음.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .. import assessment as A
from ..assessment.bda import assess_action

# 시나리오 → 대표 실행 (action, intensity). intensity None = 범주형/사각.
_SCENARIO_ACTION = {
    "S1": ("gnss_spoof", 0.8),          # 스푸핑(탐지)
    "S34": ("active_scan", 2.5),         # 정찰(회피된 저율)
    "S3": ("force_arm", None),         # 무장(범주형 탐지)
    "S79": ("unauthorized_command", None),
    "S23": ("jam", None),               # GNSS 재밍(사각)
    "S24": ("jam", None),               # C2 재밍(사각)
    "S90": ("ml_prompt_inject", None),  # 프롬프트 인젝션(사각)
    "S91": ("ml_extract_secret", None), # 모델 추출(사각)
    "S97": ("active_scan", 2.5),
}

# 배포룰은 있으나 에이전트 미배선 → 알려진 탐지상태(배포=탐지 / 미배포=사각).
_SCENARIO_STATIC = {
    "S33": True, "S36": True, "S37": True, "S78": True,   # 배포룰 → 탐지
    "S109": True, "S92": True, "S5": True,               # 배포룰 → 탐지
    "S100": None,                                          # 미배포 → 사각지대
    # 유출 계열 신규(S93~S96) — 전용 탐지룰 미배포 = 사각지대.
    "S93": None, "S94": None, "S95": None, "S96": None,
    # WiFi 계층(S25~S28, §V) — 802.11 전용 탐지룰 미배포 = 사각지대.
    "S25": None, "S26": None, "S27": None, "S28": None,
    # 고급(S29~S40, §W) — RC링크·DShot·anti-forensics 전용 탐지룰 미배포 = 사각지대.
    "S29": None, "S30": None, "S31": None, "S8": None, "S40": None,
    # Web/API·Linux 권한상승(S53~S57) — UAV Sentinel 밖 IT 계층 = 사각지대(§T 탐지).
    "S53": None, "S54": None, "S55": None, "S56": None, "S57": None,
    # 아카이브 경로순회(S58~S60) — 파일추출 계층 = 사각지대(§T 탐지).
    "S58": None, "S59": None, "S60": None,
    # 다중센서 폴트인젝션(S9~S12, §Z) — EKF 계층 전용 탐지룰 미배포 = 사각지대.
    "S9": None, "S10": None, "S11": None, "S12": None,
    # 지상 세그먼트 소프트웨어(S41~S84) — UAV Sentinel 텔레메트리 평면 미감시 = 사각지대.
    "S41": None, "S42": None, "S43": None, "S44": None,   # GCS 앱
    "S45": None, "S46": None, "S47": None,                # 컴패니언/ROS
    "S48": None, "S49": None, "S50": None,                # 데이터링크
    "S81": None, "S82": None, "S83": None, "S84": None,   # 인프라
    # 빈 번호 채움(extended, S6·S7·S98~S15·S110~S77) — 전부 사각지대.
    "S6": None, "S7": None, "S98": None, "S99": None, "S15": None,  # 공중·정찰·기체
    "S110": None, "S67": None, "S68": None, "S69": None, "S70": None,  # 페이로드·공급망
    "S71": None, "S72": None, "S73": None, "S74": None,               # 공급망
    "S75": None, "S76": None, "S77": None,                            # 미들웨어
    # 편대/군집 비행(swarm, S101~S108) — 집단 조정 로직 = 사각지대.
    "S101": None, "S102": None, "S103": None, "S104": None,
    "S105": None, "S106": None, "S107": None, "S108": None,
    # 운용 방식별(opmodes, S111~S126) — 임무·제어·모드·기종 = 사각지대.
    "S111": None, "S112": None, "S113": None, "S114": None,  # 임무수행
    "S115": None, "S116": None, "S117": None, "S118": None,  # 조종제어
    "S119": None, "S120": None, "S121": None, "S122": None,  # 조작모드
    "S123": None, "S124": None, "S125": None, "S126": None,  # 비행종류
}

# 캠페인 체인(신규 C8~C10 포함). C1~C7 은 대조용 일부만.
CHAINS = {
    "C1": ["S34", "S37", "S79", "S3"],
    "C2": ["S78", "S33", "S1"],
    "C4": ["S34", "S36", "S3"],
    "C8": ["S23", "S109", "S5"],        # GNSS재밍→항법거부→AOI이탈/임무실패
    "C9": ["S90", "S100"],                # SOC LLM 인젝션→군집포화(대응 무력화)
    "C10": ["S23", "S1", "S92"],        # GNSS재밍(사각)→은밀 스푸핑→SAR 유출
    "C11": ["S34", "S96", "S92"],        # 자격증명→암호키 유출→(서명위조로 S18우회)인증 유출
    "C12": ["S34", "S95", "S93"],        # 자격증명→스테이징→대량 영상/SAR 유출
    "C13": ["S34", "S54", "S56", "S57"],  # 자격증명→웹셸업로드→컨테이너escape→cron지속(IT 킬체인)
    # ── 신규 C14~C18: IT(S53~S60 사각)↔OT(S1~S89) 브릿지 ──
    "C14": ["S58", "S33", "S1"],          # 아카이브 공급망(Zip Slip)→펌웨어 변조→항법거부
    "C15": ["S54", "S56", "S36", "S3"],  # 웹셸→컨테이너escape→임무 자기승인→무장(IT→OT)
    "C16": ["S54", "S55", "S56", "S57"],  # 웹셸→SUID→escape→cron(순수 IT 권한상승·완전 사각)
    "C17": ["S58", "S54", "S92"],        # 아카이브 전달→웹셸→SAR 유출
    "C18": ["S53", "S3"],               # 인증우회(IDOR)→무장(범주형 견고차단 실증)
    # ── 신규 C19~C20: 지상 세그먼트 소프트웨어 킬체인(전부 Sentinel 사각) ──
    "C19": ["S41", "S47", "S84"],        # GCS 악성미션→MAVROS 명령주입→C4I 위조명령(지상 관통)
    "C20": ["S81", "S82", "S83"],        # 함대API 인증우회→텔레메트리 오염→영상스트림 하이재킹
    # ── 신규 C21~C22: 공급망 킬체인 · 기체 정밀타격(채움 시나리오) ──
    "C21": ["S68", "S67", "S33", "S1"],   # CI/CD 침해→레지스트리 변조→펌웨어→항법거부(공급망 관통)
    "C22": ["S99", "S15", "S6", "S5"], # 수동정찰→BMS 스푸핑→파라미터 리셋→Failsafe 억제
    # ── 신규 C23: 군집 붕괴 킬체인 ──
    "C23": ["S101", "S102", "S103"],     # 리더 하이재킹→합의 포이즈닝→충돌 유도(군집 붕괴)
    # ── 확장 군집/편대 캠페인 C24~C29 (군집 시나리오 × 단일UAV·EW·공급망·유출) ──
    "C24": ["S99", "S101", "S107", "S104"],  # 리더참수: 수동정찰→리더 스푸핑→명령 1:N 증폭→편대 분산
    "C25": ["S105", "S102", "S7", "S79"],   # 합의전복: Sybil→합의 포이즈닝→위조 영상/상황도→C4I 위조명령
    "C26": ["S24", "S108", "S1", "S103"],    # 분단격파: C2재밍→메시 파티션→고립멤버 GNSS 스푸핑→충돌
    "C27": ["S68", "S33", "S101", "S107"],    # 공급망전파: CI/CD 침해→펌웨어 백도어→리더 장악→전군집 전파
    "C28": ["S106", "S103", "S108"],         # 물리파괴: flocking 변조→충돌 유도→메시 분단(회복 차단)
    "C29": ["S101", "S107", "S93"],          # 대량유출: 리더 장악→명령 1:N→전군집 SAR/영상 동시 유출
    # ── 운용방식별 캠페인 C30~C33 ──
    "C30": ["S99", "S119", "S113", "S92"],   # 임무탈취: 정찰→GUIDED 강제→추적락 탈취→SAR 유출
    "C31": ["S17", "S115", "S116", "S123"],   # 제어강탈: C2 하이재킹→제어권 전환→자세오염→고정익 실속
    "C32": ["S120", "S112", "S126"],         # 착륙강제: 페일세이프 차단→RTB 강제→이착륙 위상 공격
    "C33": ["S117", "S118", "S125"],         # 자율무력: BLOS 명령위조→자율 하이재킹→VTOL 천이 실패
}


@dataclass
class ChainResult:
    chain_id: str
    verdict: str                        # stealthy | detected | blocked
    stages: List[Tuple[str, bool, Optional[bool]]] = field(default_factory=list)  # (sid, achieved, detected)
    detected_at: List[str] = field(default_factory=list)


def _exec_scenario(sid: str) -> Tuple[bool, Optional[bool]]:
    if sid in _SCENARIO_ACTION:
        action, intensity = _SCENARIO_ACTION[sid]
        out = assess_action(action, intensity=intensity if intensity is not None else 1.0)
        return True, out.detected
    if sid in _SCENARIO_STATIC:
        return True, _SCENARIO_STATIC[sid]
    return True, None                    # 미상 → 사각 가정


def run_chain(chain_id: str) -> ChainResult:
    stages: List[Tuple[str, bool, Optional[bool]]] = []
    detected_at: List[str] = []
    for sid in CHAINS[chain_id]:
        achieved, detected = _exec_scenario(sid)
        stages.append((sid, achieved, detected))
        if detected is True:
            detected_at.append(sid)
    completed = all(a for _, a, _ in stages)
    if not completed:
        verdict = "blocked"
    elif detected_at:
        verdict = "detected"             # 탐지 관통(상관룰이 잡음)
    else:
        verdict = "stealthy"             # 은밀 관통(전 단계 사각/회피)
    return ChainResult(chain_id, verdict, stages, detected_at)

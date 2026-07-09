"""운용 방식별 공격 시나리오 — S111~S126 (4차원 16개).

각: (objective, 이름, MITRE, 카테고리, 효과). 전부 사각지대(모델 판정).
"""
from __future__ import annotations

from dataclasses import dataclass

OPMODE_SCENARIOS = {
    # ── 임무 수행 방식 ──
    "S111": ("loiter_center_spoof", "선회(Loiter) 중심 스푸핑", "T0836", "임무수행",
             "ISR 체공 중심 이동 → 표적 감시 이탈"),
    "S112": ("rtb_force", "RTB 복귀 강제 트리거", "T0855", "임무수행",
             "복귀 강제 → 임무 조기중단(정찰 공백)"),
    "S113": ("track_lock_hijack", "표적 추적(Follow) 락 탈취", "T0831", "임무수행",
             "추적 락 조작 → 엉뚱한/미끼 표적 추적"),
    "S114": ("survey_grid_tamper", "측량 격자 변조", "T0836", "임무수행",
             "격자 경로 변조 → 커버리지 공백(감시 사각)"),
    # ── 조종 및 제어 방식 ──
    "S115": ("control_mode_transition", "제어권 전환 공격(Manual↔Auto)", "T0827", "조종제어",
             "나쁜 타이밍 제어권 강제 전환 → 통제 상실"),
    "S116": ("stabilization_poison", "자세제어(Stabilization) 루프 오염", "T0835", "조종제어",
             "제어 루프 입력 오염 → 진동/발산"),
    "S117": ("blos_command_forge", "BLOS(SATCOM) 자율명령 지연/위조", "T0856", "조종제어",
             "가시선 밖 명령 지연·위조 → 자율 오작동"),
    "S118": ("autonomy_hijack", "온보드 자율 결심 하이재킹", "T0831", "조종제어",
             "companion 자율 판단 override → 의도대로 비행"),
    # ── 조작 모드(비행모드) ──
    "S119": ("mode_force_guided", "비행모드 강제 변경(GUIDED 주입)", "T0855", "조작모드",
             "GUIDED 주입 → 제어권 탈취(실시간 조종)"),
    "S120": ("failsafe_mode_block", "RTL/LAND 페일세이프 차단", "T0838", "조작모드",
             "복구 모드 발동 차단 → 위험비행 지속(복구 억제)"),
    "S121": ("mode_report_spoof", "비행모드 위조 보고", "T0832", "조작모드",
             "실제 GUIDED인데 AUTO로 표시 → 운영자 기만"),
    "S122": ("acro_destabilize", "ACRO/수동 강제 불안정화", "T0836", "조작모드",
             "안정화 없는 모드 강제 → 조종 불능"),
    # ── 비행 종류별 ──
    "S123": ("fixedwing_stall", "고정익 실속(Stall) 유도", "T0806", "비행종류",
             "조종면+에어스피드 조작 → 실속/스핀"),
    "S124": ("rotary_yaw_loss", "회전익 요(Yaw) 권한 상실", "T0855", "비행종류",
             "모터 차등 조작 → 요 통제 상실·회전"),
    "S125": ("vtol_transition_attack", "VTOL 천이(Transition) 공격", "T0827", "비행종류",
             "hover↔forward 천이 임계창 공격 → 천이 실패 추락"),
    "S126": ("takeoff_landing_phase", "이착륙 위상 공격", "T0880", "비행종류",
             "저고도 취약창(이착륙) 조작 → 안전 상실"),
}


@dataclass
class OpmodeResult:
    scenario: str
    objective: str
    name: str
    mitre: str
    category: str
    effect: str


def run_opmode(scenario_id: str) -> OpmodeResult:
    obj, name, mitre, cat, eff = OPMODE_SCENARIOS[scenario_id]
    return OpmodeResult(scenario_id, obj, name, mitre, cat, eff)


def categories() -> dict:
    out = {}
    for sid, (_o, _n, _m, cat, _e) in OPMODE_SCENARIOS.items():
        out.setdefault(cat, []).append(sid)
    return out

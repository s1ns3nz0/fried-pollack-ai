"""편대/군집 비행 공격 모델 — S103~S110.

군집(N대, 리더 1 + 팔로워 N-1). Byzantine 내결함성: 악성 노드 > N/3 이면 분산합의 붕괴.
각 공격은 집단 조정 로직에 대한 효과를 결정론으로 산출.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

# sid → (objective, 이름, MITRE, 함의)
SWARM_SCENARIOS = {
    "S103": ("swarm_leader_spoof", "편대 리더 스푸핑·하이재킹", "T0856",
             "리더 보고메시지 위장 → 전 편대가 rogue 리더 추종"),
    "S104": ("swarm_consensus_poison", "군집 합의(Consensus) 포이즈닝", "T0832",
             "Byzantine 거짓상태 주입 → 분산합의 붕괴(집단 오판)"),
    "S105": ("swarm_collision_induce", "상대위치 스푸핑 충돌 유도", "T0806",
             "멤버간 상대항법 스푸핑 → 공중충돌 유발"),
    "S106": ("swarm_formation_scatter", "대형 분산/이탈 명령 주입", "T0855",
             "비인가 scatter 명령 → 편대 분열(임무 붕괴)"),
    "S107": ("swarm_sybil_inject", "Sybil 위장 멤버 주입", "T0859",
             "가짜 스웜 노드 주입 → 투표·조정 교란"),
    "S108": ("swarm_flocking_tamper", "flocking 규칙 변조(분리/정렬/응집)", "T0836",
             "군집 규칙 파라미터 변조 → 창발적 혼돈"),
    "S109": ("swarm_command_replay", "스웜 명령 리플레이/증폭", "T0857",
             "1:N 명령 재생 → 전 멤버 동시 오작동"),
    "S110": ("swarm_mesh_partition", "메시 파티션(군집 고립·분단)", "T0814",
             "EW 메시 링크 절단 → 군집 분단·조정 상실"),
}


@dataclass
class SwarmResult:
    scenario: str
    objective: str
    name: str
    mitre: str
    swarm_size: int
    effect: str
    swarm_failure: bool          # 집단 수준 임무 붕괴
    detail: dict = field(default_factory=dict)


def _byz_tolerance(n: int) -> int:
    return (n - 1) // 3          # BFT: f < n/3


def run_swarm(scenario_id: str, n: int = 9, malicious: int = 3) -> SwarmResult:
    obj, name, mitre, _impl = SWARM_SCENARIOS[scenario_id]
    f_max = _byz_tolerance(n)
    fail, effect, detail = False, "", {}

    if scenario_id == "S103":       # 리더 스푸핑
        followers = n - 1
        captured = followers        # 리더 인증 없으면 전 팔로워 포획
        fail = captured >= followers * 0.5
        effect = f"팔로워 {captured}/{followers} rogue 리더 추종"
        detail = {"captured": captured}
    elif scenario_id == "S104":     # 합의 포이즈닝
        fail = malicious > f_max    # BFT 초과 시 합의 붕괴
        effect = f"악성 {malicious} vs 허용 {f_max}(N/3) → 합의 {'붕괴' if fail else '유지'}"
        detail = {"byzantine": malicious, "tolerance": f_max}
    elif scenario_id == "S105":     # 충돌 유도
        pairs = malicious           # 상대항법 스푸핑된 쌍
        fail = pairs >= 1
        effect = f"상대위치 스푸핑 {pairs}쌍 → 공중충돌 위험"
        detail = {"collision_pairs": pairs}
    elif scenario_id == "S106":     # 대형 분산
        scattered = n
        fail = True
        effect = f"scatter 명령 → {scattered}대 편대 분열"
        detail = {"scattered": scattered}
    elif scenario_id == "S107":     # Sybil
        # 가짜 노드가 실 노드의 f_max 초과분을 만들면 합의 장악
        fake = malicious
        fail = fake > f_max
        effect = f"Sybil 가짜노드 {fake} → 투표 {'장악' if fail else '실패'}(허용 {f_max})"
        detail = {"fake_nodes": fake}
    elif scenario_id == "S108":     # flocking 변조
        fail = True
        effect = "분리/정렬/응집 계수 변조 → 창발적 발산(군집 혼돈)"
        detail = {"rules": ["separation", "alignment", "cohesion"]}
    elif scenario_id == "S109":     # 명령 리플레이
        amplified = n               # 1:N 증폭
        fail = True
        effect = f"명령 리플레이 → {amplified}대 동시 오작동(1:N 증폭)"
        detail = {"amplified": amplified}
    else:                           # S110 메시 파티션
        severed = malicious
        # 링크 절단이 군집을 조정 불능(파티션)으로 만드는가
        fail = severed >= n // 3
        effect = f"메시 링크 {severed} 절단 → 군집 {'분단(조정상실)' if fail else '저하'}"
        detail = {"severed": severed}

    return SwarmResult(scenario_id, obj, name, mitre, n, effect, fail, detail)

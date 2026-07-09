"""swarm — 편대/군집 비행 공격 (MITRE ATT&CK 기반, S101~S108).

단일 UAV 에 없는 군집 고유 공격면: 리더-팔로워·분산합의·충돌회피·메시 조정.
개별 기체가 아니라 **집단 조정 로직**을 노린다. 전부 ICS/Enterprise ATT&CK 정박.
"""
from .formation import SWARM_SCENARIOS, run_swarm

__all__ = ["SWARM_SCENARIOS", "run_swarm"]

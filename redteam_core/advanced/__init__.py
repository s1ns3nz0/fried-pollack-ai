"""advanced — 고급 드론 공격 (§W): RC 링크·DShot·anti-forensics·기법 카탈로그.

Awesome-Drone-Hacking + ired.team/RedTeam-Tools 영감. 우리가 미커버한 UAS 공격면
(조종링크·액추에이터·포렌식)과 레드팀 지식 오버레이를 더한다.

안전: 아티팩트만(dry). 실 RF/RC 주입·모터 조작은 하드웨어 어댑터+env+§T 샌드박스
통과 시에만(실 방사/물리제어 무동작 기본, fail-closed).
"""
from .rf_link import RF_SCENARIOS, run_rf
from .antiforensics import AF_SCENARIOS, run_antiforensics
from .catalog import EVASION_TECHNIQUES, TECHNIQUE_TOOLS, tools_for_scenario

__all__ = [
    "RF_SCENARIOS", "run_rf", "AF_SCENARIOS", "run_antiforensics",
    "EVASION_TECHNIQUES", "TECHNIQUE_TOOLS", "tools_for_scenario",
]

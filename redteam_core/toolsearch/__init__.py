"""toolsearch — 공격 막힐 때 GitHub 툴 레포 자동 검색 (§X).

adaptive_engage 가 blocked/사각을 반환('진행 어려움')하면, 해당 기법·목표로 GitHub
레포를 검색해 참고/사용 가능한 실 도구를 추천한다. env GITHUB_TOKEN 시 라이브 검색,
아니면 큐레이션 시드(RedTeam-Tools·§W 카탈로그) 폴백. 읽기전용(검색만, 실행 아님).
"""
from .github import CURATED, search_github
from .discover import discover_for_gaps, discover_for_objective, suggest_on_block

__all__ = ["CURATED", "search_github", "discover_for_objective",
           "discover_for_gaps", "suggest_on_block"]

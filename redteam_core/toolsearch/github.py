"""GitHub 레포 검색 — 라이브 API(GITHUB_TOKEN) 또는 큐레이션 시드 폴백.

읽기전용. Tier-0(urllib). 시드는 UAV/드론 레드팀 도구 큐레이션(RedTeam-Tools·§W).
"""
from __future__ import annotations

import json
import os
import urllib.request
from typing import List

# 큐레이션 시드 — (키워드, repo, ★근사, url, 설명)
CURATED = [
    (["gnss", "gps", "spoof"], "osqzss/gps-sdr-sim", 4200,
     "https://github.com/osqzss/gps-sdr-sim", "GPS L1 신호 시뮬(스푸핑)"),
    (["mavlink", "uav", "drone"], "ArduPilot/pymavlink", 1400,
     "https://github.com/ArduPilot/pymavlink", "MAVLink 파이썬(주입/조작)"),
    (["mavlink", "router"], "mavlink-router/mavlink-router", 700,
     "https://github.com/mavlink-router/mavlink-router", "MAVLink 라우팅(엔드포인트)"),
    (["drone", "vulnerable", "lab"], "nicholasaleks/Damn-Vulnerable-Drone", 900,
     "https://github.com/nicholasaleks/Damn-Vulnerable-Drone", "취약 드론 실습랩"),
    (["wifi", "deauth"], "aircrack-ng/aircrack-ng", 5000,
     "https://github.com/aircrack-ng/aircrack-ng", "802.11 deauth/크래킹"),
    (["wifi", "drone", "pentest"], "dronesploit/dronesploit", 2000,
     "https://github.com/dronesploit/dronesploit", "드론 펜테스트 콘솔"),
    (["rc", "frsky", "elrs"], "ExpressLRS/ExpressLRS", 3500,
     "https://github.com/ExpressLRS/ExpressLRS", "RC 링크(ELRS) 프로토콜"),
    (["prompt", "injection", "llm"], "Azure/PyRIT", 2400,
     "https://github.com/Azure/PyRIT", "LLM 레드티밍(인젝션)"),
    (["llm", "scanner", "garak"], "NVIDIA/garak", 4000,
     "https://github.com/NVIDIA/garak", "LLM 취약점 스캐너"),
    (["c2", "framework"], "BishopFox/sliver", 9000,
     "https://github.com/BishopFox/sliver", "C2 프레임워크"),
    (["exfil", "tunnel"], "jpillora/chisel", 14000,
     "https://github.com/jpillora/chisel", "TCP/UDP 터널(유출)"),
    (["privesc", "linux", "enum"], "peass-ng/PEASS-ng", 16000,
     "https://github.com/peass-ng/PEASS-ng", "권한상승 열거(linpeas)"),
    (["redteam", "tools", "list"], "A-poc/RedTeam-Tools", 7000,
     "https://github.com/A-poc/RedTeam-Tools", "레드팀 도구 큐레이션"),
    (["awesome", "drone", "hacking"], "nicholasaleks/Awesome-Drone-Hacking", 1200,
     "https://github.com/nicholasaleks/Awesome-Drone-Hacking", "드론 해킹 자료 큐레이션"),
]


def _live(query: str, limit: int) -> List[dict]:
    tok = os.environ.get("GITHUB_TOKEN", "")
    url = ("https://api.github.com/search/repositories?sort=stars&per_page="
           f"{limit}&q=" + urllib.request.quote(query))
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json",
        "User-Agent": "rt-toolsearch"})
    with urllib.request.urlopen(req, timeout=5) as r:
        data = json.loads(r.read())
    return [{"repo": it["full_name"], "stars": it["stargazers_count"],
             "url": it["html_url"], "desc": it.get("description") or "", "source": "github"}
            for it in data.get("items", [])[:limit]]


def search_github(query: str, limit: int = 5) -> List[dict]:
    """GITHUB_TOKEN 있으면 라이브 검색, 아니면 시드 키워드 매칭."""
    if os.environ.get("GITHUB_TOKEN"):
        try:
            return _live(query, limit)
        except Exception:
            pass
    q = query.lower().split()
    scored = []
    for kws, repo, stars, url, desc in CURATED:
        score = sum(1 for k in q if any(k in kw or kw in k for kw in kws))
        if score:
            scored.append((score, stars, {"repo": repo, "stars": stars, "url": url,
                                          "desc": desc, "source": "curated"}))
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [d for _s, _st, d in scored[:limit]]

"""CARVER 표적가치 모델 + UAS 표적 카탈로그 (JP 3-60 ②).

각 요소 1~5. 합계(6~30)가 클수록 고가치표적(HPT). Vulnerability(V)는 우리
§A 탐지커버리지로 산정·갱신되는 동적 축이다(사각지대=고취약).
"""
from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Carver:
    criticality: int        # 적 임무에 대한 중요도
    accessibility: int      # red 접근 가능성(RF LOS·망·공급망)
    recuperability: int     # 방어자 복구난도(높을수록 복구 어려움=고가치)
    vulnerability: int      # red 능력 대비 표적 방어(사각=고취약) — 동적
    effect: int             # 우리 목표에 대한 효과 크기
    recognizability: int    # 식별·조준 용이성

    def score(self) -> int:
        return (self.criticality + self.accessibility + self.recuperability
                + self.vulnerability + self.effect + self.recognizability)

    def with_vulnerability(self, v: int) -> "Carver":
        return replace(self, vulnerability=v)


@dataclass(frozen=True)
class Target:
    tid: str
    name: str
    objective: str          # §E OBJECTIVES 키 — 이 표적을 치는 목표
    carver: Carver
    note: str = ""

    def score(self) -> int:
        return self.carver.score()


# UAS 표적 카탈로그 — objective 가 §E 적응형 재계획과 연결된다.
CATALOG = (
    Target("GNSS", "GNSS 수신기(항법)", "nav_denial",
           Carver(criticality=5, accessibility=4, recuperability=4, vulnerability=3, effect=5, recognizability=5),
           note="스푸핑 S1 커버(초기 V낮음). 재밍 사각 가능성 → 교전 후 V상향 기대"),
    Target("GCS_CRED", "GCS 운영자 자격증명", "recon_access",
           Carver(criticality=4, accessibility=3, recuperability=3, vulnerability=4, effect=3, recognizability=4),
           note="S6 연속임계 — 회피창 존재(중취약)"),
    Target("WEAPON", "무장 체계", "weapon_effect",
           Carver(criticality=5, accessibility=2, recuperability=2, vulnerability=2, effect=5, recognizability=3),
           note="S11/S15 범주형 — 강도 회피 불가(저취약, 견고)"),
)

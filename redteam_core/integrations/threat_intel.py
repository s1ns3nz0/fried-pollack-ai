"""위협 인텔 연동 — 위협행위자 프로파일링 + STIX/TAXII seam (§O 확장).

TI 소비: red 가 '지금 누가 어떤 자산을 위협하나'를 반영해 표적 우선순위(§F)를 조정.
교리: JP 2-0 정보 → JP 3-60 표적개발. (S78 'TI 소스 오염'은 TI를 *공격*하는 별개 시나리오.)

  - THREAT_ACTORS: ATT&CK Groups 기반 방산 UAV/OT/AI 위협행위자 시드(오프라인).
  - STIX/TAXII seam: env TAXII_URL/COLLECTION 지정 시 실 피드, 아니면 시드 폴백.
  - ti_prioritized_targets: 활성 위협 수로 §F CARVER 를 가중해 HPTL 재정렬.
"""
from __future__ import annotations

import os
from typing import Dict, List

from .http_json import get_json

# 방산 UAV/OT/AI 관련 위협행위자 시드(ATT&CK Group ID) → 연관 시나리오.
THREAT_ACTORS: Dict[str, dict] = {
    "Sandworm (G0034)": {"focus": "OT/ICS 파괴·공급망",
                         "scenarios": ["S17", "S33", "S4", "S51", "S52"]},
    "APT28 (G0007)": {"focus": "방산 espionage·자격증명",
                      "scenarios": ["S34", "S35", "S3", "S79", "S92"]},
    "Volt Typhoon (G1017)": {"focus": "핵심인프라 LOTL·측면이동",
                             "scenarios": ["S34", "S21", "S22"]},
    "EW Threat Cluster": {"focus": "전자전/GNSS(귀속 불확실)",
                          "scenarios": ["S1", "S18", "S19", "S23", "S24"]},
    "AML Adversary (ATLAS)": {"focus": "적대적 ML·프롬프트 인젝션",
                              "scenarios": ["S2", "S88", "S90", "S91"]},
}


# ── STIX/TAXII seam (MISP/OpenCTI/OTX 공통) ──────────────────────────────────
def _taxii() -> tuple:
    return (os.environ.get("TAXII_URL", ""), os.environ.get("TAXII_COLLECTION", ""))


def taxii_available() -> bool:
    url, coll = _taxii()
    return bool(url and coll)


def status() -> dict:
    url, coll = _taxii()
    return {"available": taxii_available(), "taxii_url": url or None,
            "mode": "real" if taxii_available() else "fallback",
            "actor_seed_count": len(THREAT_ACTORS)}


def active_actors() -> List[str]:
    """활성 위협행위자. TAXII 연동 시 피드 기반(본선), 아니면 시드 전체."""
    if taxii_available():
        return taxii_actors_detail()["actors"]
    return list(THREAT_ACTORS)


def _parse_taxii_actors(data) -> tuple:
    """TAXII 2.1 collection objects(=STIX bundle) → intrusion-set names.

    반환 (actors, warning). malformed 면 ([], warning) 로 상위가 시드 폴백.
    """
    if not isinstance(data, dict):
        return [], "TAXII response is not a JSON object"
    objects = data.get("objects")
    if not isinstance(objects, list):
        return [], "TAXII response missing 'objects' array (STIX bundle/collection expected)"
    actors = [o["name"] for o in objects
              if isinstance(o, dict) and o.get("type") == "intrusion-set" and o.get("name")]
    if not actors:
        return [], "no intrusion-set objects in TAXII collection"
    return actors, None


def taxii_actors_detail() -> dict:
    """실 TAXII pull + schema 검증. {actors, source, warning} 반환(fail-soft, 시드 폴백)."""
    seed = list(THREAT_ACTORS)
    if not taxii_available():
        return {"actors": seed, "source": "seed", "warning": None}
    url, coll = _taxii()
    sep = "&" if "?" in url else "?"
    data = get_json(f"{url}{sep}collection={coll}")
    if isinstance(data, dict) and set(data) == {"error"}:      # http_json transport/status 오류
        return {"actors": seed, "source": "seed_fallback", "warning": f"TAXII fetch error: {data['error']}"}
    actors, warn = _parse_taxii_actors(data)
    if not actors:
        return {"actors": seed, "source": "seed_fallback", "warning": warn}
    return {"actors": actors, "source": "taxii", "warning": None}


# ── 프로파일링 ───────────────────────────────────────────────────────────────
def profile_scenario(scenario_id: str) -> List[str]:
    """이 시나리오를 구사하는 위협행위자 목록."""
    return [a for a, spec in THREAT_ACTORS.items()
            if scenario_id in spec["scenarios"] and a in set(active_actors())]


def threat_count(scenario_id: str) -> int:
    return len(profile_scenario(scenario_id))


# ── §F 연결: TI 가중 표적 우선순위 ───────────────────────────────────────────
# CATALOG 목표 → 대표 시나리오(위협 수 산정용).
_OBJECTIVE_SCENARIO = {"nav_denial": "S1", "recon_access": "S34", "weapon_effect": "S3"}
_TI_WEIGHT = 2                          # 활성 위협행위자 1명당 CARVER 가산


def ti_prioritized_targets() -> List[dict]:
    """§F CATALOG 을 TI(활성 위협 수)로 가중해 재정렬한 HPTL."""
    from ..targeting import CATALOG
    rows = []
    for t in CATALOG:
        sid = _OBJECTIVE_SCENARIO.get(t.objective, "")
        n = threat_count(sid)
        rows.append({"target": t.name, "objective": t.objective, "scenario": sid,
                     "carver": t.score(), "active_threats": n,
                     "ti_actors": profile_scenario(sid),
                     "ti_score": t.score() + n * _TI_WEIGHT})
    return sorted(rows, key=lambda r: r["ti_score"], reverse=True)

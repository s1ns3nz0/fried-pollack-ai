#!/usr/bin/env python3
"""E2E 교전 시나리오 — 12층 + 페이로드를 하나의 교전으로 관통.

    python benchmarks/e2e_engagement.py

시나리오: "안흥 시험장 KUS-FS 항법 거부 교전". 표적개발→기동→교전권한→무기화→
효과·전송→탐지관측→전투평가→적응재계획→캠페인→지속을 실제 함수 호출로 수행.
결정론·무의존(Tier-0, §K 전송만 loopback).
"""
from __future__ import annotations

import socket
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from redteam_core.targeting import prioritize, CATALOG                         # noqa: E402
from redteam_core.maneuver import run_campaign, ASSETS                         # noqa: E402
from redteam_core.roe import evaluate_roe                                      # noqa: E402
from redteam_core.payloads import AdaptivePayloadGenerator, SituationContext   # noqa: E402
from redteam_core.emso import plan_emso                                        # noqa: E402
from redteam_core.transport import build_mavlink_gps_frame, udp_deliver        # noqa: E402
from redteam_core.assessment import (                                         # noqa: E402
    assess_action, run_engagement, adaptive_engage,
)
from redteam_core.campaigns import run_chain                                   # noqa: E402
from redteam_core.sustainment import run_sustained_campaign                    # noqa: E402

_ROE_PROFILE = {   # 시험창 국가통수 위임 하 EW 교전(스펙트럼 승인)
    "available_authority": "NATIONAL",
    "conops": {"permitted_effects": ["Collect", "Manipulate", "Deny(Disrupt)"]},
    "pid_required_for": ["write_highrisk", "physical_irreversible"],
    "no_strike_list": [1, 254, 255], "restricted_targets": [],
    "spectrum": {"jceoi_deconflicted": True},
}
_STATE = {"armed": True, "in_flight": True, "alt_rel": 80.0, "mode": "AUTO"}
_TGT = {"sysid": 42, "pid": True}


def _h(n, title):
    print(f"\n{'─'*66}\n[{n}] {title}\n{'─'*66}")


def main():
    print("="*66)
    print(" E2E 교전: 안흥 시험장 KUS-FS 항법 거부 (fried-pollack-ai)")
    print("="*66)

    _h(1, "표적개발 §F — CARVER/HPTL")
    hptl = prioritize(CATALOG)
    tgt = hptl[0]
    print(f"  HPTL 1순위: {tgt.name} (CARVER {tgt.score()}) → 목표={tgt.objective}")

    _h(2, "기동 §G — 지형 순회·재경로")
    camp = run_campaign("gnss_rcv")
    print(f"  {'→'.join(ASSETS[a][0] for a in camp.winning_path)}  (경로 시도 {camp.attempts}회)")
    for hp in camp.hops:
        print(f"    · [{hp.phase}] {ASSETS[hp.src][0]}→{ASSETS[hp.dst][0]} : {hp.detail}")

    _h(3, "교전권한 §B — RoE 게이트")
    d = evaluate_roe("gnss_spoof", _STATE, _TGT, _ROE_PROFILE)
    print(f"  판정={d.verdict.value} · 요구권한={d.required_authority}/위임={d.available_authority} "
          f"· CDE={d.cde_tier} · {d.rationale}")

    _h(4, "무기화 §N — 상황 맞춤 페이로드(S1 억제 인젝션)")
    ctx = SituationContext(scenario="S32", target_rule="S1_GNSS_Spoofing")
    for p in AdaptivePayloadGenerator().generate(ctx)[:1]:
        print(f"  SOC 인젝션: {p.text}")
        print(f"    ↳ {p.rationale}")

    _h(5, "효과·전송 §C/§K — EMSO 스푸핑 + MAVLink 프레임")
    geom = {"spoof_eirp_dbm": 20, "spoof_dist_m": 100}
    emso = plan_emso("gnss_spoof", geom)
    var = emso.effect.telemetry_hint["pos_horiz_variance"]
    print(f"  EMSO 포획마진={emso.effect.metric_db}dB → PosHorizVariance={var} (대역 {emso.band})")
    try:
        rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); rx.bind(("127.0.0.1", 0))
        rx.settimeout(1.0); host, port = rx.getsockname()
        n = udp_deliver(host, port, build_mavlink_gps_frame()); rx.recvfrom(9000); rx.close()
        print(f"  §K 전송: GPS_INPUT 프레임 {n}B UDP 송신(loopback 실증)")
    except OSError:
        print("  §K 전송: (loopback 불가 환경 — env 표적 지정 시 실전송)")

    _h(6, "탐지 관측 §A — blue S1 룰")
    o = assess_action("gnss_spoof", intensity=var)
    print(f"  blue {o.rule_id}: {'🔴 탐지' if o.detected else '🟢 미탐지'} (강도 {var} vs 임계 {o.threshold})")

    _h(7, "전투평가 §D — MOP/MOE·재타격")
    ca = run_engagement("gnss_spoof", geometry=geom)
    print(f"  MOP={ca.mop_executed} 효과={ca.moe_effect} 생존={ca.moe_survivability} "
          f"종합={ca.effective} → 재타격: {ca.reattack.adjustment}")

    _h(8, "적응 재계획 §E — TTP 피벗")
    r = adaptive_engage("nav_denial")
    ttps = " → ".join(t[0] for t in r.trace)
    print(f"  {ttps}  ⇒ {r.verdict} via {r.winning_ttp} (스푸핑 탐지 → 재밍 사각지대 피벗)")

    _h(9, "캠페인 §M — C10 체인 상관")
    ch = run_chain("C10")
    flow = " → ".join(f"{s}{'(사각)' if dd is None else '(탐지)' if dd else '(회피)'}"
                      for s, _, dd in ch.stages)
    print(f"  C10: {flow} ⇒ {ch.verdict}" + (f" (탐지: {','.join(ch.detected_at)})" if ch.detected_at else ""))

    _h(10, "지속 §I — 작전지속력")
    su = run_sustained_campaign("nav_denial", rounds=5)
    print(f"  지속 {su.rounds_sustained}/5라운드 · 소진 TTP={su.burned_ttps} (재밍 사각지대로 지속)")

    print(f"\n{'='*66}\n 교전 종합: 스푸핑은 blue가 탐지하나, 재밍(사각지대) 피벗으로 은밀 항법거부 달성.")
    print(" → 5장 방어 보강 1순위: GNSS 재밍 탐지룰 신설.\n"+"="*66)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""워게임 — 표적 IP 제공 시 공격 시나리오 (dry-run 계획).

    python benchmarks/wargame.py [target_ip]

스코프 권위는 코드가 아니라 engagement_profile.yaml 의 authorization 블록
(scope_cidr·target_sysids·out_of_scope·test_window)에서 온다 — 인가받은 팀이 설정.
동언님 gate(EgressController)가 scope_cidr 로 default-deny 강제. 실 외부 전송 없음(dry-run).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from redteam_core.engagement.gate import FailClosed, load_gate                 # noqa: E402
from redteam_core.transport import build_mavlink_gps_frame                     # noqa: E402
from redteam_core.assessment import assess_action                             # noqa: E402

_PROFILE = str(Path(__file__).resolve().parent.parent / "engagement_profile.yaml")

# 프로토콜/역할 → 적용 시나리오(액션). recon 사실 + 프로파일 서비스에 매핑.
_PROTO_SCEN = {
    "mavlink": [("S1/S30 GNSS 스푸핑·재밍", "gnss_spoof"), ("Execution 무장", "force_arm")],
}
_ROLE_SCEN = {"fc": [("S4 펌웨어 변조", None)]}


def _payload(action, conn):
    if action == "gnss_spoof":
        f = build_mavlink_gps_frame(lat_e7=367150000)
        return f"{conn} (GPS_INPUT)", f"{len(f)}B {f[:20].hex()}…"
    if action == "force_arm":
        return f"{conn} COMMAND_LONG", "cmd=400(ARM) params=[1,0,…]"
    return conn, "(firmware 이미지 — 본선)"


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "10.50.0.20"   # 기본=프로파일 인가 호스트
    print("=" * 68 + f"\n 워게임: 표적 = {target}\n" + "=" * 68)

    # 스코프 권위 = 프로파일(코드 아님)
    try:
        gate, profile = load_gate(_PROFILE)
    except FailClosed as e:
        print(f"⛔ [test_window] {e} — 교전 불가"); return
    auth = profile.get("authorization", {})
    print("\n── 스코프 권위: engagement_profile.yaml · authorization (인가 팀 설정) ──")
    print(f"  scope_cidr={auth.get('scope_cidr')} · target_sysids={auth.get('target_sysids')}")
    print(f"  out_of_scope={auth.get('out_of_scope')} · test_window={auth.get('test_window')}")

    # 스코프 게이트(동언 EgressController)
    if not gate.egress_allowed(target):
        print(f"\n⛔ [RoE/스코프] {target} ∉ scope_cidr → egress default-deny 차단(fail-closed).")
        print("   → 스코프는 프로파일이 정한다. 표적 추가는 인가 팀이 profile 을 갱신해야 함.")
        return
    print(f"\n✅ [RoE/스코프] {target} ∈ scope_cidr — 교전 진행(dry-run)")

    # 정찰: 프로파일 target_profile 의 호스트/서비스에서 공격면 도출
    tp = profile.get("target_profile", {})
    print("\n── 정찰: 프로파일 공격면 ──")
    surface = []
    for svc in tp.get("services", []):
        if not gate.egress_allowed(svc.get("ip", "")):
            continue
        conn = f"{svc.get('transport','tcp')}:{svc['ip']}:{svc['port']}"
        for scen, action in _PROTO_SCEN.get(svc.get("proto", ""), []):
            surface.append((scen, action, conn))
        print(f"  {conn:<26} proto={svc.get('proto')} auth={svc.get('auth')}")
    for h in tp.get("hosts", []):
        for scen, action in _ROLE_SCEN.get(h.get("role", ""), []):
            surface.append((scen, action, f"{h['ip']} (sysid {h.get('sysid')})"))

    # 킬체인: 표적 주소 페이로드 + 탐지
    print("\n── 킬체인(dry-run): 표적 주소 페이로드 ──")
    for scen, action, conn in surface:
        ep, pl = _payload(action, conn)
        det = assess_action(action).detected if action in ("gnss_spoof", "force_arm") else None
        mark = {True: "🔴 탐지", False: "🟢 회피", None: "⚪ 사각/미평가"}[det]
        print(f"\n  [{scen}] {mark}\n    → {ep}\n    payload: {pl}")

    print("\n" + "=" * 68)
    print(" 스코프는 프로파일(인가 팀)이 정하고 gate가 강제 — 코드 하드코딩 아님.")
    print(" 범위 밖 표적은 egress default-deny 로 fail-closed 차단.")
    print("=" * 68)


if __name__ == "__main__":
    main()

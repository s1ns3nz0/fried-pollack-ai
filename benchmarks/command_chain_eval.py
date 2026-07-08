#!/usr/bin/env python3
"""승인 체인 데모 — 고도화 §O (EXORD 프록시).

    python benchmarks/command_chain_eval.py

§B RoE 판정 → 승인 체인: 위임 내는 자동, 상급 필요는 승인 없이 fail-closed.
결정론·무의존(Tier-0).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from redteam_core.roe import evaluate_roe                                     # noqa: E402
from redteam_core.roe.authority import AuthorityLevel                         # noqa: E402
from redteam_core.command import AuthorizationChain                          # noqa: E402

_PROFILE = {
    "available_authority": "COMPONENT",
    "conops": {"permitted_effects": ["Collect", "Manipulate", "Deny(Disrupt)"]},
    "pid_required_for": ["write_highrisk", "physical_irreversible"],
    "no_strike_list": [1, 254, 255], "restricted_targets": [],
    "spectrum": {"jceoi_deconflicted": True},
}
_STATE = {"armed": True, "in_flight": True, "alt_rel": 80.0, "mode": "AUTO"}
_TGT = {"sysid": 42, "pid": True}


def _line(action, res):
    print(f"  {action:<16} {res.verdict:<9} 요구={res.required_authority:<9} · {res.reason}")


def main():
    print("=== fried-pollack-ai · 승인 체인 — 고도화 §O (EXORD 프록시) ===")
    print("이 요소 위임 권한 = COMPONENT\n")
    chain = AuthorizationChain(delegated=AuthorityLevel.COMPONENT)

    print("── 저권한 액션(set_mode) ──")
    d = evaluate_roe("set_mode", _STATE, _TGT, _PROFILE)
    _line("set_mode", chain.authorize("set_mode", d))

    print("\n── 고권한 액션(gnss_spoof, CDE=SEVERE→NATIONAL) ──")
    d = evaluate_roe("gnss_spoof", _STATE, _TGT, _PROFILE)
    r1 = chain.authorize("gnss_spoof", d)                       # 승인 없음
    _line("gnss_spoof", r1)
    r2 = chain.authorize("gnss_spoof", d, approvals={AuthorityLevel.NATIONAL: True})
    _line("gnss_spoof", r2)
    print(f"    ↳ 티켓 소비: 1회={chain.consume('gnss_spoof')} · 2회={chain.consume('gnss_spoof')}(재사용 거부)")

    print("\n── ConOps 밖 액션(force_arm=Deny(Destroy)) ──")
    d = evaluate_roe("force_arm", _STATE, _TGT, _PROFILE)
    r3 = chain.authorize("force_arm", d, approvals={AuthorityLevel.NATIONAL: True})
    _line("force_arm", r3)                                      # BLOCKED — 승인으로도 불가

    print("\n판정: 위임 내=자동 / 상급 필요=승인 티켓 없이 fail-closed / RoE 위반=승인 불가.")


if __name__ == "__main__":
    main()

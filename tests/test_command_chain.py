"""승인 체인 테스트 — 고도화 §O. 결정론·무의존."""
from __future__ import annotations

from redteam_core.roe import evaluate_roe
from redteam_core.roe.authority import AuthorityLevel
from redteam_core.command import AuthorizationChain

_PROFILE = {
    "available_authority": "COMPONENT",
    "conops": {"permitted_effects": ["Collect", "Manipulate", "Deny(Disrupt)"]},
    "pid_required_for": ["write_highrisk", "physical_irreversible"],
    "no_strike_list": [1, 254, 255], "restricted_targets": [],
    "spectrum": {"jceoi_deconflicted": True},
}
_STATE = {"armed": True, "in_flight": True, "alt_rel": 80.0, "mode": "AUTO"}
_TGT = {"sysid": 42, "pid": True}


def _chain():
    return AuthorizationChain(delegated=AuthorityLevel.COMPONENT)


def test_within_delegation_auto():
    d = evaluate_roe("set_mode", _STATE, _TGT, _PROFILE)
    r = _chain().authorize("set_mode", d)
    assert r.authorized and r.verdict == "AUTO"


def test_high_authority_denied_without_approval():
    d = evaluate_roe("gnss_spoof", _STATE, _TGT, _PROFILE)   # CDE SEVERE → NATIONAL
    r = _chain().authorize("gnss_spoof", d)
    assert r.authorized is False and r.verdict == "DENIED"
    assert r.required_authority == "NATIONAL"


def test_high_authority_approved_with_national():
    d = evaluate_roe("gnss_spoof", _STATE, _TGT, _PROFILE)
    r = _chain().authorize("gnss_spoof", d, approvals={AuthorityLevel.NATIONAL: True})
    assert r.authorized and r.verdict == "APPROVED" and r.ticket is not None


def test_insufficient_approval_denied():
    d = evaluate_roe("gnss_spoof", _STATE, _TGT, _PROFILE)
    r = _chain().authorize("gnss_spoof", d, approvals={AuthorityLevel.JFC: True})  # < NATIONAL
    assert r.authorized is False and r.verdict == "DENIED"


def test_ticket_consumed_once_failclosed():
    c = _chain()
    d = evaluate_roe("gnss_spoof", _STATE, _TGT, _PROFILE)
    c.authorize("gnss_spoof", d, approvals={AuthorityLevel.NATIONAL: True})
    assert c.consume("gnss_spoof") is True
    assert c.consume("gnss_spoof") is False       # 재사용 거부(fail-closed)
    assert c.consume("takeoff") is False          # 티켓 없음 → 거부


def test_roe_blocked_cannot_be_approved():
    # force_arm=Deny(Destroy) ∉ ConOps → RoE BLOCKED → 상급 승인으로도 불가.
    d = evaluate_roe("force_arm", _STATE, _TGT, _PROFILE)
    r = _chain().authorize("force_arm", d, approvals={AuthorityLevel.NATIONAL: True})
    assert r.authorized is False and r.verdict == "BLOCKED"

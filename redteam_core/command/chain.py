"""승인 체인 — 요구 권한 > 위임이면 상급 승인 티켓 필요(fail-closed).

동언님 gate 원샷 토큰 패턴을 교전권한 체계(§B AuthorityLevel)로 확장. 승인은 상급
권한자(사람/상위 요소)가 내리며, 티켓은 단발·소비형. 이 모듈은 RoE 판정을 소비만 하고
페이로드 생성·전송을 하지 않는다(임무 분리).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from ..roe.authority import AuthorityLevel
from ..roe.roe_gate import RoeDecision, RoeVerdict


@dataclass
class ApprovalTicket:
    action: str
    required: AuthorityLevel
    granted_by: AuthorityLevel
    used: bool = False


@dataclass
class AuthorizationResult:
    action: str
    authorized: bool
    verdict: str                 # AUTO | APPROVED | DENIED | BLOCKED
    required_authority: str
    reason: str
    ticket: Optional[ApprovalTicket] = None


class AuthorizationChain:
    """§B RoE 위 승인 체인. delegated = 이 요소에 위임된 최고 권한."""

    def __init__(self, delegated: AuthorityLevel = AuthorityLevel.COMPONENT):
        self.delegated = delegated
        self._tickets: Dict[str, ApprovalTicket] = {}

    def authorize(self, action: str, roe: RoeDecision,
                  approvals: Optional[Dict[AuthorityLevel, bool]] = None) -> AuthorizationResult:
        """approvals: {권한레벨: 승인여부} — 상급이 내준 승인. RoE BLOCKED 는 승인 불가."""
        approvals = approvals or {}
        if roe.verdict == RoeVerdict.BLOCKED:
            return AuthorizationResult(action, False, "BLOCKED", roe.required_authority,
                                       "RoE 위반/데컨플릭션 — 승인 불가")
        req = AuthorityLevel[roe.required_authority]

        if req <= self.delegated:
            return AuthorizationResult(action, True, "AUTO", req.name, "위임 권한 내 — 자동 승인")

        # ESCALATE: 상급 승인 필요. 승인한 권한 중 최고가 요구 이상이면 티켓 발급.
        approver = max((lvl for lvl, ok in approvals.items() if ok), default=None)
        if approver is not None and approver >= req:
            t = ApprovalTicket(action, req, approver)
            self._tickets[action] = t
            return AuthorizationResult(action, True, "APPROVED", req.name,
                                       f"{req.name} 상급 승인 획득", t)
        return AuthorizationResult(action, False, "DENIED", req.name,
                                   f"{req.name} 승인 없음 → fail-closed")

    def consume(self, action: str) -> bool:
        """executor 경계에서 1회 검증·소모. 티켓 없거나 재사용이면 거부(fail-closed)."""
        t = self._tickets.get(action)
        if not t or t.used:
            return False
        t.used = True
        return True

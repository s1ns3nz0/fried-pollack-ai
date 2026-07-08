"""command — 승인 체인 (고도화 §O, EXORD/지휘체계 프록시).

§B RoE 게이트가 '요구 권한 > 위임 권한'(ESCALATE)을 낼 때, 그 액션은 **상급 승인
티켓** 없이는 실행 못 한다(fail-closed). 동언님 gate 물리-비가역 토큰 패턴을 교전권한
체계로 확장 — 고-CDE·비가역 사이버 화력은 상급 승인을 요구(weapons-release authority).

임무 분리(separation of duties): 개발(§N payloads) ≠ 승인(§O/§B) ≠ 실행(§K transport).
이 모듈은 RoE 판정을 '소비'만 하고 페이로드 생성·전송을 하지 않는다(불변식 테스트로 강제).
"""
from .chain import ApprovalTicket, AuthorizationChain, AuthorizationResult

__all__ = ["ApprovalTicket", "AuthorizationChain", "AuthorizationResult"]

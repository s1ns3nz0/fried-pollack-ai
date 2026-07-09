"""AI 공격 도구 연동 — S90 프롬프트인젝션·S91 모델추출.

live 경로는 AI_ATTACK_PROVIDER=http + AI_TARGET_URL 인 generic HTTP probe 로만
제한한다(정직성, 안 A). PyRIT/Garak native wrapper 는 아직 미구현이라, 그 provider
값이 들어오면 실행을 가장하지 않고 not_available 로 반환한다(정직한 미지원 신호).
env 없으면 결정론 폴백(사각지대 모델). 판정권은 모델 밖 유지(조언·실행만).
"""
from __future__ import annotations

import os
from typing import Optional

from .http_json import post_json
from .result import finalize


# native wrapper 미구현 provider — 값이 오면 실행 가장 없이 not_available.
_NATIVE_UNSUPPORTED = ("pyrit", "garak")


def _provider() -> str:
    return os.environ.get("AI_ATTACK_PROVIDER", "").lower()


def _target() -> str:
    return os.environ.get("AI_TARGET_URL", "")


def available() -> bool:
    return _provider() == "http" and bool(_target())   # 실 live 는 http probe 만


def status() -> dict:
    return {"available": available(), "provider": _provider() or None,
            "target": _target() or None,
            "native_supported": False,
            "mode": "real" if available() else "fallback"}


def run_ai_attack(technique: str, payload: str = "") -> dict:
    """technique: prompt_injection | model_extraction.

    실연동 시 PyRIT/Garak 로 표적 LLM 공격 실행, 아니면 결정론 폴백.
    """
    mitre = {"prompt_injection": "AML.T0051", "model_extraction": "ATLAS(모델추출)"}
    if available():
        # §T 샌드박스 게이트: 표적이 스코프 내·격리 봉인일 때만 실 실행(fail-closed).
        from ..sandbox import ai_spec, guarded
        return guarded(ai_spec(technique, _target()),
                       lambda: _run_real(technique, payload, mitre.get(technique, "")))
    if _provider() in _NATIVE_UNSUPPORTED and _target():
        # 정직성: native 호출 미구현 → 실행 가장 없이 미지원 신호.
        return {"mode": "not_available", "technique": technique, "provider": _provider(),
                "mitre": mitre.get(technique),
                "note": "PyRIT/Garak native wrapper 미구현 — AI_ATTACK_PROVIDER=http 로 "
                        "generic HTTP probe 사용"}
    # 폴백: blue 미매핑(사각지대) — assess 로 일관 판정.
    from ..assessment.bda import assess_action
    action = "ml_prompt_inject" if technique == "prompt_injection" else "ml_extract_secret"
    out = assess_action(action)
    return {"mode": "fallback", "technique": technique, "mitre": mitre.get(technique),
            "detected": out.detected, "note": "결정론 폴백(사각지대) — 실 도구 미연동"}


def _run_real(technique: str, payload: str, mitre: str) -> dict:  # pragma: no cover
    """실 PyRIT/Garak 실행 경로(설치·표적 있을 때만)."""
    prov = _provider()
    body = {"provider": prov, "technique": technique, "mitre": mitre, "payload": payload}
    response = post_json(_target(), body)
    return finalize({"mode": "real", "provider": prov, "technique": technique,
                     "mitre": mitre, "target": _target(), "response": response}, "response")

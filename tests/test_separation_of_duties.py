"""임무 분리(separation of duties) 불변식 — 고도화 §O.

개발(§N payloads) ≠ 승인(§O command/§B roe) ≠ 실행(§K transport).
모듈 임포트 경계로 강제: 각 역할 모듈이 상대 역할 모듈을 임포트하지 않음.
"""
from __future__ import annotations

import ast
import pathlib

_ROOT = pathlib.Path(__file__).resolve().parent.parent / "redteam_core"


def _imports(pkg: str):
    mods = set()
    for f in (_ROOT / pkg).glob("*.py"):
        for node in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ImportFrom) and node.module:
                mods.add(node.module)
            elif isinstance(node, ast.Import):
                mods.update(a.name for a in node.names)
    return mods


def test_payloads_does_not_authorize_or_execute():
    # 개발(페이로드 생성)은 승인/전송 권한이 없다.
    imp = _imports("payloads")
    assert not any("command" in m for m in imp), "payloads → command 금지"
    assert not any(m == "roe" or m.endswith(".roe") or "roe." in m for m in imp), "payloads → roe 금지"
    assert not any("transport" in m for m in imp), "payloads → transport 금지"


def test_command_does_not_develop_or_execute():
    # 승인은 페이로드 생성·전송을 하지 않는다(RoE 판정 소비만).
    imp = _imports("command")
    assert not any("payloads" in m for m in imp), "command → payloads 금지"
    assert not any("transport" in m for m in imp), "command → transport 금지"


def test_transport_does_not_self_authorize():
    # 실행(전송)은 스스로 승인하지 않는다.
    imp = _imports("transport")
    assert not any("command" in m for m in imp), "transport → command 금지"
    assert not any(m == "roe" or m.endswith(".roe") or "roe." in m for m in imp), "transport → roe 금지"

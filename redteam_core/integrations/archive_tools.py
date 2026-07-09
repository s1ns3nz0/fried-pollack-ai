"""아카이브 경로순회 도구 연동 — evilarc/slipit/tarslip (S25~S27).

env ARCHIVE_TOOL(evilarc|slipit|tarslip) 지정 시 실 도구로 악성 아카이브 생성,
아니면 내부 §N 생성기 폴백. 생성물은 §T 샌드박스로 detonate(escape 탐지) 후에만
라이브 전달(공급망 아티팩트 주입). 결정론 Tier-0(실 도구는 지연 임포트).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile

_MAX_OUTPUT = 64 * 1024   # stdout/stderr 각 상한 — 무한 출력 방어
_EXEC_TIMEOUT = 30


def _tool() -> str:
    return os.environ.get("ARCHIVE_TOOL", "").lower()


def available() -> bool:
    return _tool() in ("evilarc", "slipit", "tarslip")


def _command() -> str:
    return os.environ.get("ARCHIVE_TOOL_CMD", "")


def status() -> dict:
    return {"available": available(), "tool": _tool() or None,
            "mode": "real" if available() and _command() else "fallback",
            "command": _command() or None}


def craft(variant: str = "zip_slip", escape: str = "") -> dict:
    """variant: zip_slip | zip_absolute | tar_symlink | tar_slip. §T 탐지까지 묶어 반환."""
    from ..payloads import (
        craft_zip_slip, craft_zip_absolute, craft_tar_symlink, craft_tar_slip,
    )
    from ..sandbox import detonate_archive
    fn = {"zip_slip": craft_zip_slip, "zip_absolute": craft_zip_absolute,
          "tar_symlink": craft_tar_symlink, "tar_slip": craft_tar_slip}.get(variant, craft_zip_slip)
    payload = fn(escape) if escape and variant in ("zip_slip", "zip_absolute", "tar_slip") else fn()
    report = detonate_archive(payload.data, payload.fmt)
    external = _run_external(variant, escape) if available() and _command() else None
    external_ok = bool(external and external.get("ok"))
    return {"mode": "real" if external_ok else "fallback", "tool": _tool() or "internal(§N)",
            "variant": variant, "malicious_entries": payload.malicious_entries,
            "sandbox_verdict": report.verdict, "escaping": report.escaping,
            "external_tool_implemented": external_ok,
            "external_tool": external,
            "note": "실 도구(env) 또는 §N 생성 → §T 샌드박스 탐지"}


def _allowed_commands() -> list:
    raw = os.environ.get("ARCHIVE_TOOL_ALLOWED", "")
    return [p for p in raw.replace(",", os.pathsep).split(os.pathsep) if p]


def _policy_reject(cmd_path: str) -> str:
    """로컬 실행 정책 위반 사유 반환(없으면 "")."""
    if not os.path.isabs(cmd_path):
        return f"command must be an absolute path, got {cmd_path!r}"   # PATH 탐색 차단
    allowed = _allowed_commands()
    if allowed and cmd_path not in allowed:
        return f"{cmd_path!r} not in ARCHIVE_TOOL_ALLOWED"
    return ""


def _clip(text: str):
    if text and len(text) > _MAX_OUTPUT:
        return text[:_MAX_OUTPUT], True
    return text, False


def _run_external(variant: str, escape: str = "") -> dict:
    """로컬 wrapper 실행 — allowlist·cwd/env 격리·출력 상한·구조화 오류 적용."""
    cmd_path = _command()
    reason = _policy_reject(cmd_path)
    if reason:
        return {"command": [cmd_path, variant], "ok": False,
                "error": {"type": "policy", "reason": reason}}
    cmd = [cmd_path, variant]
    if escape:
        cmd.append(escape)
    workdir = tempfile.mkdtemp(prefix="archtool_")
    env = {"PATH": "/usr/bin:/bin"}     # 최소 env — 호출자 환경 상속 차단
    try:
        result = subprocess.run(cmd, capture_output=True, text=True,
                                timeout=_EXEC_TIMEOUT, cwd=workdir, env=env)
    except (OSError, subprocess.SubprocessError) as exc:   # TimeoutExpired 포함
        return {"command": cmd, "ok": False,
                "error": {"type": "exec", "reason": str(exc) or exc.__class__.__name__}}
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
    out, out_trunc = _clip(result.stdout)
    err, err_trunc = _clip(result.stderr)
    ok = result.returncode == 0
    return {"command": cmd, "returncode": result.returncode,
            "stdout": out, "stderr": err, "truncated": out_trunc or err_trunc,
            "ok": ok,
            "error": None if ok else {"type": "returncode",
                                      "reason": f"exit {result.returncode}"}}

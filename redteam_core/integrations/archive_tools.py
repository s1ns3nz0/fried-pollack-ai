"""아카이브 경로순회 도구 연동 — evilarc/slipit/tarslip (S25~S27).

env ARCHIVE_TOOL(evilarc|slipit|tarslip) 지정 시 실 도구로 악성 아카이브 생성,
아니면 내부 §N 생성기 폴백. 생성물은 §T 샌드박스로 detonate(escape 탐지) 후에만
라이브 전달(공급망 아티팩트 주입). 결정론 Tier-0(실 도구는 지연 임포트).
"""
from __future__ import annotations

import os
import subprocess


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
    return {"mode": "real" if external else "fallback", "tool": _tool() or "internal(§N)",
            "variant": variant, "malicious_entries": payload.malicious_entries,
            "sandbox_verdict": report.verdict, "escaping": report.escaping,
            "external_tool_implemented": external is not None,
            "external_tool": external,
            "note": "실 도구(env) 또는 §N 생성 → §T 샌드박스 탐지"}


def _run_external(variant: str, escape: str = "") -> dict:
    cmd = [_command(), variant]
    if escape:
        cmd.append(escape)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return {"command": cmd, "returncode": result.returncode,
            "stdout": result.stdout, "stderr": result.stderr}

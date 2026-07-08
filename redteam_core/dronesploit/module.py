"""sploitkit식 모듈 프레임 — 시나리오를 Metasploit식 set-options/run 으로.

각 모듈: path·description·options·run(). dronesploit 콘솔 UX를 우리 시나리오에 얹어
발표/사용성을 높인다(신규 공격 아님, 조직화).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict


@dataclass
class Module:
    path: str
    description: str
    options: Dict[str, str] = field(default_factory=dict)
    _run: Callable = None

    def set(self, key: str, value: str) -> None:
        self.options[key] = value

    def run(self) -> dict:
        return self._run(self.options) if self._run else {"error": "no runner"}


def _exec_runner(scenario_id):
    def _r(opts):
        from ..execute import execute_scenario
        dry = opts.get("DRY", "true").lower() != "false"
        return execute_scenario(scenario_id, dry_run=dry).__dict__
    return _r


def _wifi_runner(scenario_id):
    def _r(opts):
        from .wifi import run_wifi
        dry = opts.get("DRY", "true").lower() != "false"
        return run_wifi(scenario_id, dry=dry).__dict__
    return _r


def _build_registry() -> Dict[str, Module]:
    from ..execute import SCENARIO_EXEC
    from .wifi import WIFI_SCENARIOS
    reg: Dict[str, Module] = {}
    for sid, (cat, _p) in SCENARIO_EXEC.items():
        reg[f"exploit/{cat}/{sid}"] = Module(
            f"exploit/{cat}/{sid}", f"{sid} ({cat})",
            {"TARGET": "", "DRY": "true"}, _exec_runner(sid))
    for sid, meta in WIFI_SCENARIOS.items():
        reg[f"exploit/wifi/{sid}"] = Module(
            f"exploit/wifi/{sid}", meta["name"],
            {"SSID": "MPD-GCS", "IFACE": "", "DRY": "true"}, _wifi_runner(sid))
    return reg


MODULE_REGISTRY = _build_registry()


def load_module(path: str) -> Module:
    return MODULE_REGISTRY[path]

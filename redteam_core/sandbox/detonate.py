"""detonation 샌드박스 — 격리 폭파 + 행위 관측 + 악성 지표 판정.

sim 백엔드(기본): 실 FS(ephemeral tempdir) 쓰기·롤백으로 '격리 폭파'를 실검증하되,
네트워크는 실제로 연결하지 않고 egress allowlist 로 판정만 한다(스코프 밖=차단·기록).
docker 백엔드: env 지정 시 실 격리 컨테이너 seam(여기선 미실행 폴백).
"""
from __future__ import annotations

import ipaddress
import os
import shutil
import tempfile
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class SandboxPolicy:
    allowed_cidrs: List[str] = field(default_factory=list)  # egress allowlist([]=default-deny)
    backend: str = "sim"                                    # sim | docker
    rollback: bool = True


@dataclass
class DetonationReport:
    artifact: str
    backend: str
    files_written: List[str] = field(default_factory=list)
    egress_allowed: List[str] = field(default_factory=list)
    egress_blocked: List[str] = field(default_factory=list)
    indicators: List[str] = field(default_factory=list)
    contained: bool = True          # FS 롤백 성공 + 실 egress 없음
    verdict: str = "benign"         # benign | suspicious | malicious


_PERSIST_HINTS = (".implant", "cron", "rc.local", "startup", "backdoor")
_SENSITIVE = ("ARMING_CHECK", "FS_GCS", "FS_THR", "BRD_SAFETYENABLE", "SIM_GPS")


def _egress_ok(host: str, cidrs: List[str]) -> bool:
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False                # 도메인 = 해석 필요 → 기본 차단(fail-closed)
    return any(ip in ipaddress.ip_network(c, strict=False) for c in cidrs)


class DetonationSandbox:
    """격리 폭파 실행기. policy.allowed_cidrs 밖 egress 는 차단·기록."""

    def __init__(self, policy: SandboxPolicy = None):
        self.policy = policy or SandboxPolicy()

    def detonate(self, spec: dict) -> DetonationReport:
        """spec: {name, files:[(path,bytes)], network:[(host,port)], params:{...}}"""
        r = DetonationReport(artifact=spec.get("name", "payload"), backend=self.policy.backend)
        if self.policy.backend == "docker":
            r.indicators.append("docker 백엔드 seam(env 지정 시 실 격리 컨테이너 실행)")

        workdir = tempfile.mkdtemp(prefix="deton_")
        try:
            # FS 폭파(격리 tempdir) — 실제 쓰지만 롤백으로 봉인
            for name, data in spec.get("files", []):
                path = os.path.join(workdir, os.path.basename(name))
                with open(path, "wb") as f:
                    f.write(data if isinstance(data, bytes) else str(data).encode())
                r.files_written.append(name)
                if any(h in name for h in _PERSIST_HINTS):
                    r.indicators.append(f"지속성 아티팩트: {name}")

            # 네트워크 — 실제 연결 안 함. egress allowlist 판정만.
            for host, port in spec.get("network", []):
                target = f"{host}:{port}"
                if _egress_ok(host, self.policy.allowed_cidrs):
                    r.egress_allowed.append(target)
                else:
                    r.egress_blocked.append(target)
                    r.indicators.append(f"차단된 egress → {target} (스코프 밖)")

            # 파라미터 변조 지표
            for key in spec.get("params", {}):
                if any(s in key for s in _SENSITIVE):
                    r.indicators.append(f"안전 파라미터 변조: {key}")
        finally:
            if self.policy.rollback:
                shutil.rmtree(workdir, ignore_errors=True)
                r.contained = not os.path.exists(workdir)
            else:
                r.contained = False

        malicious = any(("지속성" in i or "안전 파라미터" in i) for i in r.indicators)
        r.verdict = "malicious" if malicious else ("suspicious" if r.indicators else "benign")
        return r

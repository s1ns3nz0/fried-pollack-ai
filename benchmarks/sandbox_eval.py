#!/usr/bin/env python3
"""악성코드 detonation 샌드박스 데모 — 고도화 §T.

    python benchmarks/sandbox_eval.py

격리 폭파(FS 롤백 + egress default-deny) + 악성 지표 판정. 스코프는 engagement_profile
scope_cidr(인가 팀). 실 표적 영향 없음. 결정론·무의존(Tier-0).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from redteam_core.engagement.gate import load_gate                           # noqa: E402
from redteam_core.sandbox import DetonationSandbox, SandboxPolicy            # noqa: E402

_PROFILE = str(Path(__file__).resolve().parent.parent / "engagement_profile.yaml")

# 폭파할 페이로드들(§L 임플란트 / §K C2 / 유출)
PAYLOADS = [
    {"name": "펌웨어 임플란트(§L)", "files": [(".implant", b"rogue-foothold")],
     "params": {"BRD_SAFETYENABLE": 0}},
    {"name": "C2 비콘 → 외부 IP", "network": [("203.0.113.66", 8080)]},
    {"name": "C2 비콘 → 스코프 내", "network": [("10.50.0.20", 5790)]},
    {"name": "정찰 스캔(무해)", "network": [("10.50.0.10", 5790)]},
]


def main():
    try:
        _, profile = load_gate(_PROFILE)
        cidrs = profile.get("authorization", {}).get("scope_cidr", ["10.50.0.0/24"])
    except Exception:
        cidrs = ["10.50.0.0/24"]
    sbx = DetonationSandbox(SandboxPolicy(allowed_cidrs=cidrs, backend="sim"))

    print("=== fried-pollack-ai · 악성코드 detonation 샌드박스 — §T ===")
    print(f"egress allowlist(scope_cidr) = {cidrs} · 실 표적 영향 없음(격리 폭파)\n")
    for p in PAYLOADS:
        r = sbx.detonate(p)
        mark = {"malicious": "🔴", "suspicious": "🟠", "benign": "🟢"}[r.verdict]
        print(f"{mark} [{r.artifact}] 판정={r.verdict} · 격리봉인={r.contained}")
        for i in r.indicators:
            print(f"     · {i}")
        if r.egress_allowed:
            print(f"     · 허용 egress(스코프 내): {r.egress_allowed}")
        print()
    print("판정: FS 폭파는 tempdir 격리+롤백으로 봉인, egress 는 스코프 밖 전부 차단.")
    print("      SANDBOX_BACKEND=docker + env 지정 시 실 격리 컨테이너(본선 실도구 detonation).")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""run.py — UAV RedTeam 에이전트 엔트리포인트.

    python run.py                          # 기본 인게이지먼트 실행(스텁 레인지)
    python run.py --range-mode sitl        # 실 SITL로 스왑(pymavlink + 라이브 SITL 필요)
    python run.py --hardened               # 하드닝 인스턴스(PoV 페어 비교용)
    python run.py --emit-soc               # ③ 브릿지: UAV*_CL + SOC Alert 산출(out/)
    python run.py --apply-egress           # egress default-deny를 OS 방화벽에 실제 설치(root)
    python run.py --json                   # 전체 리포트 JSON 출력

range_mode/target/observables/sim 등 모든 환경 정보는 engagement_profile.yaml에서 온다.
"""

from __future__ import annotations

import argparse
import json
import os

from redteam_core.logging_util import get_logger
# 실행 로직은 service 레이어에 산다(CLI·MCP 공용). 하위호환 위해 여기로 재노출.
from redteam_core.service import (build_soc_payload, demo_approver,  # noqa: F401
                                  run_engagement)

DEFAULT_PROFILE = os.path.join(os.path.dirname(__file__), "engagement_profile.yaml")
DEFAULT_LEARNING_DIR = os.path.join(os.path.dirname(__file__), "out", "learning")
log = get_logger("run")


def main() -> None:
    ap = argparse.ArgumentParser(description="UAV RedTeam 에이전트")
    ap.add_argument("--profile", default=DEFAULT_PROFILE)
    ap.add_argument("--range-mode", default=None,
                    help="container|sitl|hil|live (미지정 시 프로파일 값)")
    ap.add_argument("--hardened", action="store_true", help="하드닝 인스턴스(PoV 페어)")
    ap.add_argument("--emit-soc", action="store_true", help="③ 브릿지 산출(UAV*_CL + Alert)")
    ap.add_argument("--kpi-dashboard", action="store_true",
                    help="방어 태세 KPI 정적 대시보드 생성(out/kpi-dashboard.html)")
    ap.add_argument("--apply-egress", action="store_true", help="OS 방화벽에 egress 규칙 설치(root)")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "out"))
    ap.add_argument("--persist-learning", nargs="?", const=DEFAULT_LEARNING_DIR, default=None,
                    metavar="DIR", help="학습(경험·타깃 프로파일)을 디스크에 영속화(자기개선 누적)")
    ap.add_argument("--json", action="store_true", help="전체 리포트 JSON 출력")
    args = ap.parse_args()

    state = run_engagement(args.profile, args.range_mode, args.hardened, args.apply_egress,
                           persist_learning=args.persist_learning)
    report = state["report"]

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        _print_summary(state, report)
        if args.persist_learning:
            _print_learning(report, args.persist_learning)

    if args.emit_soc:
        _emit_soc(state, args.out)

    if args.kpi_dashboard:
        from redteam_core.kpi.dashboard import render_html
        os.makedirs(args.out, exist_ok=True)
        path = os.path.join(args.out, "kpi-dashboard.html")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(render_html())
        print(f"[KPI 대시보드] {path}")


def _print_summary(state, report) -> None:
    gate = state["gate"]
    print("=" * 68)
    backend = "LangGraph(interrupt HITL)" if state.get("_backend") == "LangGraphRunner" else "stdlib"
    print(f"UAV RedTeam — {report['engagement']}")
    print(f"runner={backend}  "
          f"range_mode={state['profile'].get('engagement', {}).get('range_mode')}  "
          f"egress={gate.egress.status()['mode']}")
    print("=" * 68)
    print("\n[킬체인 원자 노드]")
    for f in report["findings"]:
        print(f"  {f['node']:>3} {f['action']:<16} {f['status']:<8} {f['risk_tier']:<22} "
              f"{','.join(f['attack_ics'])}")
    print("\n[스코어카드]")
    print(json.dumps(report["scorecard"], ensure_ascii=False, indent=2))
    v = report["scorecard"]["physical_safety_violations"]
    print(f"\n물리 안전 위반율: {v} -> {'PASS ✅' if v == 0 else 'FAIL ❌'}")


def _print_learning(report, learning_dir) -> None:
    """영속 학습 누적 상태 요약(자기개선 루프 가시화)."""
    lr = report.get("learning", {})
    if not lr or lr.get("skipped"):
        return
    print("\n" + "-" * 68)
    print(f"[학습 영속] dir={learning_dir}")
    print(f"  target={lr.get('target_id')}  이번 run 기록={lr.get('experiences_written')}건  "
          f"통한 액션(누적 회수)={lr.get('prior_success_recall')}")
    pb = lr.get("target_profile", {}).get("pb_scores", {})
    if pb:
        print("  pb_scores(액션별 러닝 평균 효과·누적 n):")
        for action, s in pb.items():
            print(f"    {action:<20} avg_effect={s['avg_effect']:.3f}  n={s['n']}")


def _emit_soc(state, out_dir) -> None:
    os.makedirs(out_dir, exist_ok=True)
    soc = build_soc_payload(state)          # 인라인 산출(service) → CLI는 그걸 파일로 씀
    rows, alert = soc["rows"], soc["alert"]

    ndjson_path = os.path.join(out_dir, "uav_cl_rows.ndjson")
    alert_path = os.path.join(out_dir, "soc_alert.json")
    with open(ndjson_path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(alert_path, "w", encoding="utf-8") as fh:
        json.dump(alert, fh, ensure_ascii=False, indent=2)

    print("\n" + "-" * 68)
    print(f"[③ 브릿지] telemetry-tap → {len(rows)}개 UAV*_CL 행 → {ndjson_path}")
    print(f"[③ 브릿지] SOC Alert(→ POST /alert 계약) → {alert_path}")
    print("  탐지 신호:")
    for s in alert["signals"]:
        print(f"    - {s}")
    print(f"  MITRE: {alert['mitre']}  severity_baseline={alert['severity_baseline']}")


if __name__ == "__main__":
    main()

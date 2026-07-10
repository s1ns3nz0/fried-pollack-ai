"""KPI 대시보드 생성기 — full_report() → 자기완결 정적 HTML.

방어(blue) 태세 KPI를 심사용 정적 아티팩트로 렌더한다. 외부 호스트 의존 0
(오프라인·Artifact CSP 정합), 손수 인라인 SVG+CSS, JS 의존 없음. 결정론:
wall-clock 타임스탬프는 주입식(기본 미포함)이라 동일 입력 → 동일 출력.

재생성:  python -m redteam_core.kpi.dashboard   ->  out/kpi-dashboard.html
"""
from __future__ import annotations

import html
import os
from typing import Optional

from . import full_report

# ── 검증된 팔레트 (dataviz reference instance) ──────────────────────────────
STATUS = {"good": "#0ca30c", "warning": "#fab219", "serious": "#ec835a", "critical": "#d03b3b"}
CAT = ["#2a78d6", "#1baf7a", "#eda100", "#008300", "#4a3aa7", "#e34948", "#e87ba4", "#eb6834"]

# blue 태세 관점: 탐지=good, 강건=good, 회피가능=warning, 사각=critical.
COVERAGE_COLOR = {
    "detected_only": STATUS["good"], "robust": "#1baf7a",
    "evadable": STATUS["warning"], "blind": STATUS["critical"],
}
COVERAGE_LABEL = {
    "detected_only": "탐지(단일)", "robust": "강건 탐지",
    "evadable": "회피 가능", "blind": "사각(미탐지)",
}

# D3FEND 미커버 8종 → 권장 대응(커스텀). ARCHITECTURE §11 처방 근거.
D3FEND_REMEDY = {
    "gnss_spoof": "다중센서 융합 · 항스푸핑(RAIM/관성 교차검증)",
    "jam": "항재밍 · 링크 다중화(주파수 도약 · BLOS 페일오버)",
    "spoof_telemetry": "D3-NTA 네트워크 이상탐지 · D3-MAN 메시지 서명",
    "ml_prompt_inject": "입력 구분자 격리 · 조언 전용 LLM veto 게이트",
    "ml_extract_secret": "모델 접근 rate-limit · 쿼리 감사 · 출력 최소화",
    "ml_craft_adversarial": "적대예제 탐지 · 입력 전처리 · 앙상블 판정",
    "ml_evade_perception": "다중모달 교차검증 · 인식 신뢰도 게이트",
    "ml_poison_training": "학습 데이터 출처 검증 · 이상 배치 격리",
}


def _esc(s) -> str:
    return html.escape(str(s))


def _pct(x: float) -> str:
    return f"{100 * x:.1f}%"


# ── SVG 마크 헬퍼 (thin marks, 4px rounded ends, 2px 갭) ─────────────────────
def _stacked_bar(segments, width=760, height=26) -> str:
    """segments: [(label, count, color)]. 100% 가로 누적막대 + 2px surface 갭."""
    total = sum(c for _, c, _ in segments) or 1
    x, gap, parts = 0.0, 2.0, []
    n = len(segments)
    for i, (label, count, color) in enumerate(segments):
        w = (count / total) * (width - gap * (n - 1))
        parts.append(
            f'<rect x="{x:.1f}" y="0" width="{max(w,0):.1f}" height="{height}" '
            f'rx="3" fill="{color}"><title>{_esc(label)}: {count} ({_pct(count/total)})</title></rect>'
        )
        x += w + gap
    return f'<svg viewBox="0 0 {width} {height}" width="100%" height="{height}" role="img">{"".join(parts)}</svg>'


def _hbars(items, width=520, maxval=None, row_h=30, fmt=None) -> str:
    """items: [(label, value, color)]. 가로 막대, 데이터엔드 4px 라운드."""
    fmt = fmt or (lambda v: f"{v}")
    maxval = maxval or (max((v for _, v, _ in items), default=1) or 1)
    lab_w, bar_w, rows = 210, width - 210 - 60, []
    for i, (label, value, color) in enumerate(items):
        y = i * row_h
        w = (value / maxval) * bar_w if maxval else 0
        rows.append(
            f'<text x="0" y="{y+row_h/2+4:.0f}" class="lbl">{_esc(label)}</text>'
            f'<rect x="{lab_w}" y="{y+5:.0f}" width="{max(w,1):.1f}" height="{row_h-12}" rx="3" fill="{color}">'
            f'<title>{_esc(label)}: {fmt(value)}</title></rect>'
            f'<text x="{lab_w+w+8:.0f}" y="{y+row_h/2+4:.0f}" class="val">{_esc(fmt(value))}</text>'
        )
    h = len(items) * row_h
    return f'<svg viewBox="0 0 {width} {h}" width="100%" height="{h}" role="img">{"".join(rows)}</svg>'


def _meter(value, status, width=260, height=12) -> str:
    """0..1 미터. 트랙 + 채움."""
    v = max(0.0, min(1.0, value))
    return (
        f'<svg viewBox="0 0 {width} {height}" width="100%" height="{height}" role="img">'
        f'<rect x="0" y="0" width="{width}" height="{height}" rx="6" class="track"/>'
        f'<rect x="0" y="0" width="{max(v*width,2):.1f}" height="{height}" rx="6" fill="{status}">'
        f'<title>{_pct(v)}</title></rect></svg>'
    )


def _tile(label, value, sub, status=None) -> str:
    accent = f' style="color:{status}"' if status else ""
    return (
        f'<div class="tile"><div class="tile-label">{_esc(label)}</div>'
        f'<div class="tile-value"{accent}>{_esc(value)}</div>'
        f'<div class="tile-sub">{_esc(sub)}</div></div>'
    )


def _card(title, body, note="") -> str:
    n = f'<p class="card-note">{note}</p>' if note else ""
    return f'<section class="card"><h2>{_esc(title)}</h2>{n}{body}</section>'


# ── 섹션 빌더 ────────────────────────────────────────────────────────────────
def _headline(r) -> str:
    cg, mc = r["coverage_gap"], r["mitre_coverage"]
    classes = cg["scenario_classes"]
    from collections import Counter
    c = Counter(classes.values())
    tot = sum(c.values()) or 1
    detectable = tot - c.get("blind", 0)
    tiles = [
        _tile("탐지 커버리지", _pct(detectable / tot), f"{detectable}/{tot} 시나리오에 탐지 신호", STATUS["critical"]),
        _tile("사각(미탐지)", _pct(cg["blind_spot_ratio"]), f"{c.get('blind',0)}개 시나리오 blind", STATUS["critical"]),
        _tile("MITRE 기법", str(mc["total_techniques"]), f"ICS {mc['by_framework']['ICS']} · Ent {mc['by_framework']['Enterprise']} · ATLAS {mc['by_framework']['ATLAS']}"),
        _tile("D3FEND 미커버", _pct(mc["d3fend_blind_ratio"]), f"{len(mc['d3fend_blind_actions'])}개 액션 대응책 없음", STATUS["serious"]),
    ]
    return f'<div class="tiles">{"".join(tiles)}</div>'


def _coverage_section(r) -> str:
    from collections import Counter
    classes = r["coverage_gap"]["scenario_classes"]
    c = Counter(classes.values())
    order = ["detected_only", "robust", "evadable", "blind"]
    segs = [(COVERAGE_LABEL[k], c.get(k, 0), COVERAGE_COLOR[k]) for k in order if c.get(k, 0)]
    legend = "".join(
        f'<span class="leg"><i style="background:{COVERAGE_COLOR[k]}"></i>{COVERAGE_LABEL[k]} '
        f'<b>{c.get(k,0)}</b> ({_pct(c.get(k,0)/(sum(c.values()) or 1))})</span>'
        for k in order
    )
    body = f'<div class="bar-wrap">{_stacked_bar(segs, width=760)}</div><div class="legend">{legend}</div>'
    return _card("탐지 커버리지 분해 (blue S1~S7 실 룰 기준)", body,
                 note="시나리오를 blue 탐지룰로 평가한 분류. 사각=탐지 신호 없음.")


def _moe_section(r) -> str:
    moe = r["moe_indicators"]
    m1, m2 = moe["MOE1_effect_achievement"], moe["MOE2_survivability"]
    mi = r["mission_impact"]
    meters = (
        f'<div class="meter-row"><span>임무 저하 지수</span>{_meter(m1["mission_degradation_index"], STATUS["critical"])}<b>{m1["mission_degradation_index"]:.3f}</b></div>'
        f'<div class="meter-row"><span>사각률(생존성)</span>{_meter(m2["blind_spot_ratio"], STATUS["critical"])}<b>{m2["blind_spot_ratio"]:.3f}</b></div>'
        f'<div class="meter-row"><span>은밀 캠페인률</span>{_meter(m2["stealthy_campaign_ratio"], STATUS["serious"])}<b>{m2["stealthy_campaign_ratio"]:.3f}</b></div>'
    )
    mrtc = "".join(f"<li>{_esc(x)}</li>" for x in mi["affected_mrt_c"])
    body = (
        f'{meters}'
        f'<p class="sub">평균 탐지까지 <b>{m2["avg_steps_to_detection"]:.2f}</b> step · 영향받은 MRT-C <b>{m1["affected_mrt_c_count"]}</b>개</p>'
        f'<ul class="chips">{mrtc}</ul>'
    )
    return _card("MOE — 효과 달성 · 생존성(미탐지)", body,
                 note="MOE1=공격이 임무효과를 냈나, MOE2=탐지 없이 살아남았나. blue 관점에선 둘 다 방어 실패 지표.")


def _mea_section(r) -> str:
    mea = r["mea_reliability"]
    items = sorted(mea["per_ttp"].items(), key=lambda kv: kv[1])
    bars = [(k, v, STATUS["critical"] if v >= 0.9 else (STATUS["serious"] if v >= 0.7 else STATUS["warning"]))
            for k, v in items]
    body = (
        f'<p class="sub">MEA overall <b>{mea["mea_overall"]:.3f}</b> — 공격 효과 신뢰도(높을수록 방어에 불리)</p>'
        f'{_hbars(bars, width=520, maxval=1.0, fmt=lambda v: f"{v:.2f}")}'
    )
    return _card("MEA — TTP별 공격효과 신뢰도", body)


def _bda_section(r) -> str:
    aq = r["assessment_quality"]
    conf = aq["bda_confidence"]
    segs = [("High", conf["High"], STATUS["good"]), ("Medium", conf["Medium"], STATUS["warning"]),
            ("Low", conf["Low"], STATUS["critical"])]
    legend = "".join(
        f'<span class="leg"><i style="background:{col}"></i>{lab} <b>{cnt}</b></span>'
        for lab, cnt, col in segs)
    body = (
        f'<div class="bar-wrap">{_stacked_bar(segs, width=520)}</div><div class="legend">{legend}</div>'
        f'<p class="sub">OPSEC 노출률 <b>{_pct(aq["opsec_exposure_ratio"])}</b> · '
        f'데컨플릭션 위반(샘플) <b>{aq["deconfliction_violations_sampled"]}</b> · Low신뢰=사각지대</p>'
    )
    return _card("BDA 신뢰도 · 데컨플릭션", body)


def _mitre_section(r) -> str:
    mc = r["mitre_coverage"]
    fw = mc["by_framework"]
    bars = [(k, fw[k], CAT[i]) for i, k in enumerate(["ICS", "Enterprise", "ATLAS"])]
    blind = "".join(f'<code>{_esc(a)}</code>' for a in mc["d3fend_blind_actions"])
    body = (
        f'<p class="sub">총 <b>{mc["total_techniques"]}</b> 기법 · 매핑 액션 <b>{mc["mapped_actions"]}</b></p>'
        f'{_hbars(bars, width=520, fmt=lambda v: str(v))}'
        f'<p class="sub">D3FEND 미커버 <b>{_pct(mc["d3fend_blind_ratio"])}</b> ({len(mc["d3fend_blind_actions"])}개 액션):</p>'
        f'<div class="codes">{blind}</div>'
    )
    return _card("MITRE ATT&CK / D3FEND 커버리지", body)


def _dwell_section(r) -> str:
    dwell = r["dwell"]
    detected = {k: v for k, v in dwell.items() if v is not None}
    undetected = [k for k, v in dwell.items() if v is None]
    bars = [(k, v, STATUS["serious"]) for k, v in sorted(detected.items(), key=lambda kv: kv[1])]
    body = (
        f'<p class="sub">탐지된 캠페인 <b>{len(detected)}</b> / 총 <b>{len(dwell)}</b> · '
        f'미탐지(끝까지 blind) <b>{len(undetected)}</b>개</p>'
        f'{_hbars(bars, width=520, fmt=lambda v: f"{v} step")}'
    )
    return _card("Dwell — 탐지까지 소요 step (캠페인별)", body,
                 note="값이 클수록 blue가 늦게 잡음. 미탐지 캠페인은 표시 제외(끝까지 안 잡힘).")


def _prescription_section(r) -> str:
    from collections import Counter
    mc = r["mitre_coverage"]
    remedies = "".join(
        f'<tr><td><code>{_esc(a)}</code></td><td>{_esc(D3FEND_REMEDY.get(a, "custom 대응 필요"))}</td></tr>'
        for a in mc["d3fend_blind_actions"]
    )
    classes = r["coverage_gap"]["scenario_classes"]
    blind_ids = sorted([s for s, cls in classes.items() if cls == "blind"],
                       key=lambda s: int(s[1:]) if s[1:].isdigit() else 0)
    blind_list = " · ".join(f"<code>{_esc(s)}</code>" for s in blind_ids[:24])
    more = f" 외 {len(blind_ids)-24}개" if len(blind_ids) > 24 else ""
    body = (
        f'<h3>1. D3FEND 미커버 액션 → 권장 대응</h3>'
        f'<table class="rx"><thead><tr><th>액션</th><th>권장 방어(커스텀)</th></tr></thead><tbody>{remedies}</tbody></table>'
        f'<h3>2. 사각 시나리오 → 신설 탐지룰 우선순위</h3>'
        f'<p class="sub">{len(blind_ids)}개 blind 시나리오에 blue 탐지룰 없음:</p>'
        f'<div class="codes">{blind_list}{more}</div>'
    )
    return _card("🔧 우선 메울 갭 (처방)", body,
                 note="레드팀 KPI의 목적 = 측정을 blue 개선 행동으로 닫기.")


# ── 셸 ──────────────────────────────────────────────────────────────────────
_CSS = """
:root{--bg:#f9f9f7;--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--muted:#898781;
--grid:#e1e0d9;--ring:rgba(11,11,11,.10);--track:#ecebe6;}
@media (prefers-color-scheme:dark){:root{--bg:#0d0d0d;--surface:#1a1a19;--ink:#fff;
--ink2:#c3c2b7;--muted:#898781;--grid:#2c2c2a;--ring:rgba(255,255,255,.10);--track:#2c2c2a;}}
:root[data-theme=light]{--bg:#f9f9f7;--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--grid:#e1e0d9;--ring:rgba(11,11,11,.10);--track:#ecebe6;}
:root[data-theme=dark]{--bg:#0d0d0d;--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--grid:#2c2c2a;--ring:rgba(255,255,255,.10);--track:#2c2c2a;}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font-family:system-ui,-apple-system,"Segoe UI",sans-serif;line-height:1.5;}
.wrap{max-width:960px;margin:0 auto;padding:32px 20px 64px;}
header h1{font-size:24px;margin:0 0 4px}header .lede{color:var(--ink2);margin:0 0 4px;font-size:15px}
header .meta{color:var(--muted);font-size:13px;margin:0}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:24px 0}
.tile{background:var(--surface);border:1px solid var(--ring);border-radius:12px;padding:16px}
.tile-label{color:var(--ink2);font-size:13px}.tile-value{font-size:30px;font-weight:700;margin:4px 0}
.tile-sub{color:var(--muted);font-size:12px}
.card{background:var(--surface);border:1px solid var(--ring);border-radius:12px;padding:20px;margin:16px 0}
.card h2{font-size:17px;margin:0 0 4px}.card-note{color:var(--muted);font-size:13px;margin:0 0 14px}
.card h3{font-size:14px;margin:18px 0 8px;color:var(--ink2)}
.bar-wrap{margin:6px 0 12px}.legend{display:flex;flex-wrap:wrap;gap:14px}
.leg{font-size:13px;color:var(--ink2)}.leg i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:5px;vertical-align:middle}
.leg b{color:var(--ink)}
svg .lbl{fill:var(--ink2);font-size:12.5px}svg .val{fill:var(--ink);font-size:12.5px;font-variant-numeric:tabular-nums}
svg .track{fill:var(--track)}
.meter-row{display:grid;grid-template-columns:130px 1fr 56px;align-items:center;gap:10px;margin:8px 0;font-size:13px;color:var(--ink2)}
.meter-row b{color:var(--ink);text-align:right;font-variant-numeric:tabular-nums}
.sub{color:var(--ink2);font-size:13px;margin:10px 0 6px}.sub b{color:var(--ink)}
.chips{list-style:none;padding:0;margin:6px 0 0;display:flex;flex-wrap:wrap;gap:6px}
.chips li{background:var(--bg);border:1px solid var(--ring);border-radius:999px;padding:3px 10px;font-size:12px;color:var(--ink2)}
.codes{display:flex;flex-wrap:wrap;gap:6px}code{background:var(--bg);border:1px solid var(--ring);border-radius:5px;padding:1px 6px;font-size:12px}
.rx{width:100%;border-collapse:collapse;font-size:13px}.rx th,.rx td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--grid);vertical-align:top}
.rx th{color:var(--muted);font-weight:600}
footer{color:var(--muted);font-size:12px;margin-top:28px;border-top:1px solid var(--grid);padding-top:14px}
footer code{font-size:11px}
"""


def _inner(r: dict, stamp: str) -> str:
    sections = "".join([
        _coverage_section(r), _moe_section(r), _mea_section(r),
        _bda_section(r), _mitre_section(r), _dwell_section(r),
        _prescription_section(r),
    ])
    return f"""<div class="wrap">
<header>
<h1>방어 태세 KPI 대시보드</h1>
<p class="lede">red 교전 산출(UAV*_CL)을 blue 실 탐지룰(S1~S7)로 평가한 방어측 지표.</p>
<p class="meta">source: <code>redteam_core.kpi.full_report()</code> · 무의존·결정론{stamp}</p>
</header>
{_headline(r)}
{sections}
<footer>
결정론 스냅샷 — 동일 입력 → 동일 출력. 재생성:
<code>python -m redteam_core.kpi.dashboard</code> → <code>out/kpi-dashboard.html</code>.
외부 호스트 참조 0(오프라인 가능). fried-pollack-ai 방어 KPI 계층(assessment·kpi).
</footer>
</div>"""


def render_html(report: Optional[dict] = None, generated_at: str = "", fragment: bool = False) -> str:
    """fragment=False: 완전 자기완결 HTML 문서(오프라인 파일).
    fragment=True: <title>+<style>+본문만(doctype/html/head/body 없음) — Artifact 퍼블리시용."""
    r = report if report is not None else full_report()
    stamp = f" · 생성 {_esc(generated_at)}" if generated_at else " · 결정론 스냅샷"
    inner = _inner(r, stamp)
    if fragment:
        return f'<title>방어 태세 KPI — fried-pollack-ai</title>\n<style>{_CSS}</style>\n{inner}'
    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>방어 태세 KPI — fried-pollack-ai</title>
<style>{_CSS}</style></head>
<body>{inner}</body></html>"""


def main() -> str:
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "out")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "kpi-dashboard.html")
    generated_at = os.environ.get("KPI_DASHBOARD_TIMESTAMP", "")
    html_str = render_html(generated_at=generated_at)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(html_str)
    print(f"[KPI 대시보드] {path} ({len(html_str)} bytes)")
    return path


if __name__ == "__main__":
    main()

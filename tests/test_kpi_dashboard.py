"""KPI 대시보드 생성기 — 자기완결·결정론·내용 검증."""
from __future__ import annotations

import re

from redteam_core import kpi
from redteam_core.kpi import dashboard


def _html():
    return dashboard.render_html()


def test_renders_valid_self_contained_html():
    h = _html()
    assert h.startswith("<!doctype html>")
    assert "</html>" in h.strip()[-10:]
    # 외부 호스트 참조 0 (오프라인·Artifact CSP 정합). w3.org 네임스페이스만 허용.
    externals = [u for u in re.findall(r"https?://[^\"'\s)]+", h) if "w3.org" not in u]
    assert externals == [], externals


def test_no_external_asset_tags():
    h = _html()
    assert "<script src" not in h
    assert "<link " not in h          # no external stylesheet
    assert 'src="http' not in h


def test_deterministic_same_input_same_output():
    assert dashboard.render_html() == dashboard.render_html()


def test_contains_live_kpi_numbers():
    r = kpi.full_report()
    h = dashboard.render_html(r)
    blind = r["coverage_gap"]["blind_spot_ratio"]
    # 헤드라인 사각률이 실제 KPI 값과 일치해야 함.
    assert f"{100*blind:.1f}%" in h
    assert str(r["mitre_coverage"]["total_techniques"]) in h


def test_has_all_sections_and_charts():
    h = _html()
    assert h.count('<section class="card">') == 7      # 6 측정 + 1 처방
    assert h.count('<div class="tile">') == 4           # 헤드라인 히어로 타일
    assert h.count("<svg ") >= 6                          # 섹션별 SVG 차트
    assert "우선 메울 갭" in h                             # 처방 섹션


def test_prescription_covers_every_d3fend_blind_action():
    r = kpi.full_report()
    h = dashboard.render_html(r)
    for action in r["mitre_coverage"]["d3fend_blind_actions"]:
        assert f"<code>{action}</code>" in h


def test_timestamp_injectable_but_optional():
    assert "결정론 스냅샷" in dashboard.render_html()
    assert "2026-01-02" in dashboard.render_html(generated_at="2026-01-02")

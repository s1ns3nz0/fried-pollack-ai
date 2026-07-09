"""시나리오 실 실행기 테스트 — §U. dry-run(무전송) 결정론 검증."""
from __future__ import annotations

from redteam_core.execute import SCENARIO_EXEC, execute_all, execute_scenario


def test_all_scenarios_dry_produce_artifacts():
    res = execute_all(dry_run=True)
    assert len(res) == len(SCENARIO_EXEC)
    for r in res:
        assert r.transmitted is False          # dry = 전송 안 함
        assert r.artifact and r.target in ("dry", "physics-only") or "dry" in r.target


def test_mavlink_builds_real_frame():
    r = execute_scenario("S1", dry_run=True)   # GNSS 스푸핑
    assert r.category == "mavlink" and "frame" in r.artifact and "B" in r.artifact


def test_ai_generates_payloads():
    r = execute_scenario("S90", dry_run=True)  # 프롬프트 인젝션
    assert r.category == "ai" and "페이로드" in r.artifact


def test_exfil_harvests_crypto_key():
    r = execute_scenario("S96", dry_run=True)  # 암호키 유출
    assert r.category == "exfil" and "crypto_key" in r.artifact


def test_container_builds_kubectl():
    r = execute_scenario("S51", dry_run=True)  # 컨테이너 서비스 중단
    assert r.category == "container" and r.artifact.startswith("kubectl")


def test_emso_physics_only_no_transmission():
    r = execute_scenario("S24", dry_run=True)  # C2 재밍
    assert r.category == "emso" and r.transmitted is False
    assert "physics" in r.target

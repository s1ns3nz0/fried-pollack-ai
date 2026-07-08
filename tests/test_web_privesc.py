"""Web/API·Linux 권한상승 S42~S47 생성·분석 테스트. 결정론·무의존."""
from __future__ import annotations

from redteam_core.payloads.exploits import (
    craft_ssrf, craft_idor, craft_webshell, craft_pickle,
    craft_suid, craft_container_escape, craft_cron_hijack,
)
from redteam_core.sandbox import analyze


def test_s42_ssrf_imds_malicious():
    r = analyze(craft_ssrf())
    assert r.scenario == "S42" and r.verdict == "malicious"
    assert any("메타데이터" in i or "토큰" in i for i in r.indicators)


def test_s42_ssrf_external_suspicious():
    r = analyze(craft_ssrf("http://evil.example.com/x"))
    assert r.verdict == "suspicious"


def test_s43_idor_blind_spot():
    r = analyze(craft_idor())
    assert r.scenario == "S43" and r.blind_spot is True     # blue 방어 공백


def test_s44_webshell_malicious():
    r = analyze(craft_webshell("imagery.php"))
    assert r.verdict == "malicious" and any("웹셸" in i for i in r.indicators)


def test_s44_pickle_deserialization_malicious():
    r = analyze(craft_pickle())
    assert r.verdict == "malicious" and any("역직렬화" in i for i in r.indicators)


def test_s45_suid_gtfobins_malicious():
    r = analyze(craft_suid("find"))
    assert r.scenario == "S45" and r.verdict == "malicious"


def test_s46_container_escape_malicious():
    for v in ("privileged", "hostpath", "docker_sock", "hostpid"):
        r = analyze(craft_container_escape(v))
        assert r.verdict == "malicious", v


def test_s47_cron_hijack_malicious():
    r = analyze(craft_cron_hijack())
    assert r.scenario == "S47" and r.verdict == "malicious"

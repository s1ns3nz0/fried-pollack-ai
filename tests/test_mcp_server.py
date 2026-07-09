import pytest


def test_rejects_range_modes_not_allowed_by_policy(monkeypatch):
    monkeypatch.delenv("ALLOWED_RANGE_MODES", raising=False)

    from mcp_server import validate_cluster_range_mode

    for mode in ("sitl", "hil", "live"):
        with pytest.raises(ValueError, match="configured range modes"):
            validate_cluster_range_mode(mode)


def test_allows_sitl_when_deployment_policy_enables_it(monkeypatch):
    monkeypatch.setenv("ALLOWED_RANGE_MODES", "container,sitl")

    from mcp_server import validate_cluster_range_mode

    assert validate_cluster_range_mode("container") == "container"
    assert validate_cluster_range_mode("sitl") == "sitl"
    with pytest.raises(ValueError, match="configured range modes"):
        validate_cluster_range_mode("live")


def test_run_engagement_tool_returns_inline_report(monkeypatch):
    import mcp_server

    def fake_report(**kwargs):
        return {
            "report": {"engagement": "stub"},
            "backend": "StdlibGraphRunner",
            "range_mode": kwargs["range_mode"],
            "soc": {"rows": [], "alert": {"signals": []}},
        }

    monkeypatch.setattr(mcp_server.service, "engagement_report", fake_report)

    monkeypatch.delenv("ALLOWED_RANGE_MODES", raising=False)

    result = mcp_server.run_engagement_tool(range_mode="container", emit_soc=True)

    assert result["range_mode"] == "container"
    assert result["report"]["engagement"] == "stub"
    assert result["soc"]["rows"] == []

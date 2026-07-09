#!/usr/bin/env python3
"""MCP ToolServer wrapper for fried-pollack-ai.

kagent calls this server as a coarse-grained MCP tool. The LLM can trigger an
engagement and read the report, but cannot choose individual kill-chain actions.
Cluster execution defaults to the deterministic container range and can be
expanded by deployment-scoped policy.
"""

from __future__ import annotations

import os
from typing import Any

from redteam_core import service

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8080
DEFAULT_TRANSPORT = "sse"
DEFAULT_CLUSTER_RANGE_MODE = "container"
DEFAULT_ALLOWED_RANGE_MODES = (DEFAULT_CLUSTER_RANGE_MODE,)


def allowed_cluster_range_modes() -> tuple[str, ...]:
    """Return deployment-scoped range modes.

    The server fails closed by default. Cluster deployments can opt into SITL
    by setting ALLOWED_RANGE_MODES=container,sitl.
    """
    configured = os.getenv("ALLOWED_RANGE_MODES", ",".join(DEFAULT_ALLOWED_RANGE_MODES))
    modes = tuple(mode.strip() for mode in configured.split(",") if mode.strip())
    return modes or DEFAULT_ALLOWED_RANGE_MODES


def validate_cluster_range_mode(range_mode: str | None) -> str:
    """Fail closed for headless cluster execution.

    HIL/live ranges require separately authorized infrastructure and HITL
    channels. SITL is only enabled when the deployment explicitly allows it.
    """
    selected = range_mode or DEFAULT_CLUSTER_RANGE_MODE
    allowed_modes = allowed_cluster_range_modes()
    if selected not in allowed_modes:
        raise ValueError(
            "AKS/kagent MCP execution only allows configured range modes "
            f"{allowed_modes!r}; got {selected!r}."
        )
    return selected


def run_engagement_tool(
    profile: str | None = None,
    range_mode: str = DEFAULT_CLUSTER_RANGE_MODE,
    hardened: bool = False,
    emit_soc: bool = False,
) -> dict[str, Any]:
    """Run one deterministic engagement and return a stateless JSON payload."""
    validated_range_mode = validate_cluster_range_mode(range_mode)
    return service.engagement_report(
        profile_path=profile,
        range_mode=validated_range_mode,
        hardened=hardened,
        emit_soc=emit_soc,
    )


def create_mcp_server():
    """Build the FastMCP app.

    The import is intentionally lazy so unit tests can validate policy logic
    without requiring the optional MCP runtime to be installed.
    """
    from mcp.server.fastmcp import FastMCP
    from starlette.responses import JSONResponse

    mcp = FastMCP(
        "fried-pollack-ai",
        host=os.getenv("MCP_HOST", DEFAULT_HOST),
        port=int(os.getenv("MCP_PORT", str(DEFAULT_PORT))),
    )

    @mcp.tool(name="run_engagement")
    def run_engagement(
        profile: str | None = None,
        range_mode: str = DEFAULT_CLUSTER_RANGE_MODE,
        hardened: bool = False,
        emit_soc: bool = False,
    ) -> dict[str, Any]:
        """Run the UAV red-team pipeline once and return report JSON inline."""
        return run_engagement_tool(
            profile=profile,
            range_mode=range_mode,
            hardened=hardened,
            emit_soc=emit_soc,
        )

    @mcp.custom_route("/healthz", methods=["GET"])
    async def healthz(_request):
        return JSONResponse({"status": "ok"})

    return mcp


def main() -> None:
    transport = os.getenv("MCP_TRANSPORT", DEFAULT_TRANSPORT)
    create_mcp_server().run(transport=transport)


if __name__ == "__main__":
    main()

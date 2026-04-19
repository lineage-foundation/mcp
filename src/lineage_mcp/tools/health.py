import time
from lineage_mcp.__about__ import __version__
from mcp.server.fastmcp import FastMCP
from lineage_mcp.core.context import ServerContext
from lineage_mcp.core.errors import mcp_error_boundary

def register(mcp: FastMCP, ctx: ServerContext):
    @mcp.tool()
    @mcp_error_boundary
    def health() -> dict:
        return {"status": "ok", "timestamp": int(time.time()), "version": __version__}

    @mcp.tool()
    @mcp_error_boundary
    def version() -> dict:
        return {"version": __version__}

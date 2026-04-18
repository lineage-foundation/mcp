from __future__ import annotations

from mcp.server.fastmcp import FastMCP
import os

from lineage.wallet import Wallet

from lineage_mcp.core.clients import create_blockchain_client
from lineage_mcp.core.config import get_config
from lineage_mcp.core.context import ServerContext

from lineage_mcp.tools import blockchain, wallet, health
from lineage_mcp import fast_mcp_prompts as prompts

mcp = FastMCP("Lineage MCP Server", stateless_http=True)

# 1. Initialize Context
cfg = get_config()
wallet_client = Wallet()
wallet_client.config = cfg

ctx = ServerContext(
    config=cfg, blockchain_client=create_blockchain_client(cfg), wallet=wallet_client
)

# 2. Register tools from plugins
blockchain.register(mcp, ctx)
wallet.register(mcp, ctx)
health.register(mcp, ctx)
prompts.register(mcp, ctx)


def _cors_wrapper(inner_app):
    allow_origins_env = os.environ.get("MCP_ALLOW_ORIGINS", "*")
    allow_origins = (
        [o.strip() for o in allow_origins_env.split(",")] if allow_origins_env else ["*"]
    )

    async def app(scope, receive, send):  # ASGI 3.0
        if scope.get("type") != "http":
            return await inner_app(scope, receive, send)

        async def send_with_cors(event):
            if event.get("type") == "http.response.start":
                headers = event.setdefault("headers", [])
                # Add CORS headers
                origin = None
                for name, value in scope.get("headers", []):
                    if name.lower() == b"origin":
                        origin = value.decode()
                        break
                allow_origin = (
                    "*" if "*" in allow_origins else (origin if origin in allow_origins else None)
                )
                if allow_origin:
                    headers.append((b"access-control-allow-origin", allow_origin.encode()))
                headers.append((b"access-control-allow-headers", b"*"))
                headers.append((b"access-control-allow-methods", b"POST, OPTIONS"))
                headers.append((b"access-control-expose-headers", b"Mcp-Session-Id, X-Request-Id"))
            await send(event)

        # Friendly landing page for browsers (GET / or /mcp)
        path = scope.get("path", "/")
        method = scope.get("method", "GET")
        if method in ("GET", "HEAD") and path in ("/", "/mcp"):
            html = (
                "<html><head><title>Lineage MCP Server</title></head><body>"
                "<h1>Lineage MCP Server</h1>"
                "<p>To use this service, connect with an MCP-compatible client (e.g., MCP Inspector).</p>"
                '<p>Docs: <a href="https://modelcontextprotocol.io/">Model Context Protocol</a></p>'
                "</body></html>"
            ).encode("utf-8")
            start = {
                "type": "http.response.start",
                "status": 200,
                "headers": [(b"content-type", b"text/html; charset=utf-8")],
            }
            await send_with_cors(start)
            await send({"type": "http.response.body", "body": html})
            return

        # Handle clients posting without required Accept header
        if method == "POST" and path in ("/", "/mcp"):
            accept_header = None
            for name, value in scope.get("headers", []):
                if name.lower() == b"accept":
                    accept_header = value.decode()
                    break
            if not accept_header or "text/event-stream" not in accept_header:
                body = (
                    b'{"ok":false,"message":"This endpoint speaks MCP Streamable HTTP. Use an MCP client.",'
                    b'"docs":"https://modelcontextprotocol.io/"}'
                )
                start = {
                    "type": "http.response.start",
                    "status": 406,
                    "headers": [(b"content-type", b"application/json")],
                }
                await send_with_cors(start)
                await send({"type": "http.response.body", "body": body})
                return

        # Handle preflight
        if scope.get("method") == "OPTIONS":
            start = {"type": "http.response.start", "status": 204, "headers": []}
            await send_with_cors(start)
            await send({"type": "http.response.body", "body": b""})
            return

        return await inner_app(scope, receive, send_with_cors)

    return app


# Expose Streamable HTTP ASGI app for the transport at root with minimal CORS
app = _cors_wrapper(mcp.streamable_http_app())



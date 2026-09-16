from __future__ import annotations

from typing import Optional
from functools import lru_cache

from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
import os

from .__about__ import __version__
from .clients import create_blockchain_client
from .config import get_config
from .explorer import ExplorerClient
from .tools_blockchain import get_entry_by_hash, fetch_transactions
from .tools_wallet import (
    sdk_fetch_balance_result,
    send_transaction as wallet_send_transaction,
    generate_seed_phrase as gen_seed_impl,
    generate_keypair as gen_keypair_impl,
)
from .tools_health import health as health_impl, version as version_impl
from . import prompts as prompt_catalog
from . import tools_explorer as te


# Create the MCP server using the SDK's standard pattern (mcp SDK v2)
mcp = MCPServer("Lineage MCP Server", version=__version__)


@lru_cache()
def get_shared_blockchain_client():
    cfg = get_config()
    return create_blockchain_client(cfg)


_explorer_client: ExplorerClient | None = None


def _explorer() -> ExplorerClient:
    global _explorer_client
    if _explorer_client is None:
        cfg = get_config()
        _explorer_client = ExplorerClient(cfg.explorer_url, cfg.explorer_timeout_s)
    return _explorer_client


@mcp.tool()
def health() -> dict:
    return health_impl()


@mcp.tool()
def version() -> dict:
    return version_impl()


# --- SDK-only tools (no explorer equivalent) ---

@mcp.tool(name="get-entry-by-hash")
def blockchain_get_entry_by_hash(hash: str) -> dict:  # noqa: A002
    return get_entry_by_hash(get_shared_blockchain_client(), hash)


@mcp.tool(name="fetch-transactions")
def blockchain_fetch_transactions(tx_hashes: list[str]) -> dict:
    return fetch_transactions(get_shared_blockchain_client(), tx_hashes)


# --- Overlap tools (explorer-first + on-chain verify) ---

@mcp.tool(name="get-latest-block")
def get_latest_block(verify: bool = True) -> dict:
    sdk = get_shared_blockchain_client()
    return te.get_latest_block(_explorer(), lambda: sdk.get_latest_block(), verify=verify)


@mcp.tool(name="get-block")
def get_block(id: str, verify: bool = True) -> dict:  # noqa: A002
    sdk = get_shared_blockchain_client()
    # Verify the on-chain block by its height; the explorer accepts height or hash.
    return te.get_block(_explorer(), lambda: sdk.get_block_by_num(int(id)) if str(id).isdigit()
                        else sdk.get_blockchain_entry(id), id, verify=verify)


@mcp.tool(name="get-transaction")
def get_transaction(hash: str, verify: bool = True) -> dict:  # noqa: A002
    sdk = get_shared_blockchain_client()
    return te.get_transaction(_explorer(), lambda: sdk.get_transaction_by_hash(hash), hash, verify=verify)


@mcp.tool(name="get-address-balance")
def get_address_balance(address: str, verify: bool = True) -> dict:
    return te.get_address_balance(_explorer(), lambda: sdk_fetch_balance_result([address]), address, verify=verify)


@mcp.tool(name="get-supply")
def get_supply(verify: bool = True) -> dict:
    sdk = get_shared_blockchain_client()
    return te.get_supply(_explorer(), lambda: sdk.get_total_supply(), verify=verify)


# --- Explorer-only tools ---

@mcp.tool(name="list-blocks")
def list_blocks(limit: int = 20, offset: int = 0, order: str = "desc") -> dict:
    return te.list_blocks(_explorer(), limit=limit, offset=offset, order=order)


@mcp.tool(name="list-transactions")
def list_transactions(limit: int = 20, offset: int = 0, order: str = "desc") -> dict:
    return te.list_transactions(_explorer(), limit=limit, offset=offset, order=order)


@mcp.tool(name="list-block-transactions")
def list_block_transactions(id: str) -> dict:  # noqa: A002
    return te.list_block_transactions(_explorer(), id)


@mcp.tool(name="list-address-transactions")
def list_address_transactions(address: str, limit: int = 20, offset: int = 0) -> dict:
    return te.list_address_transactions(_explorer(), address, limit=limit, offset=offset)


@mcp.tool(name="search-items")
def search_items(q: Optional[str] = None, genesis: Optional[str] = None,
                 limit: int = 20, offset: int = 0) -> dict:
    return te.search_items(_explorer(), q=q, genesis=genesis, limit=limit, offset=offset)


@mcp.tool(name="get-status")
def get_status() -> dict:
    return te.get_status(_explorer())


# --- Wallet tools ---

@mcp.tool(name="generate-seed-phrase")
def wallet_generate_seed_phrase() -> dict:
    return gen_seed_impl()


@mcp.tool(name="generate-keypair")
def wallet_generate_keypair(seedPhrase: Optional[str] = None) -> dict:  # noqa: N803 (external name)
    return gen_keypair_impl(seed_phrase=seedPhrase)


@mcp.tool(name="transfer-funds")
def wallet_transfer_funds_tool(destination: str, amount: int) -> dict:
    # amount is in base units (int). Requires LINEAGE_SEED_PHRASE to derive a
    # spendable wallet under the reworked SDK.
    cfg = get_config()
    if not cfg.seed_phrase:
        return {"ok": False, "error": "Server seed phrase not configured (LINEAGE_SEED_PHRASE)"}
    return wallet_send_transaction(destination, amount, cfg.seed_phrase)


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


# Expose Streamable HTTP ASGI app for the transport at root with minimal CORS.
# In mcp SDK v2 the stateless flag moved from the constructor to the app factory.
# DNS-rebinding protection is disabled here (the _cors_wrapper governs origins);
# leaving it on would default to localhost-only Host/Origin and reject deployed traffic.
app = _cors_wrapper(
    mcp.streamable_http_app(
        stateless_http=True,
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
    )
)


# Prompts registered via FastMCP.prompt() decorator (SDK standard)
@mcp.prompt(name="prompt.block.explain_header", title="Explain Block Header")
def prompt_block_explain_header(header_json: str) -> list[dict]:
    text = prompt_catalog.render_prompt("prompt.block.explain_header", header_json=header_json)
    return [{"role": "user", "content": text}]


@mcp.prompt(name="prompt.block.summarize", title="Summarize Block")
def prompt_block_summarize(block_json: str) -> list[dict]:
    text = prompt_catalog.render_prompt("prompt.block.summarize", block_json=block_json)
    return [{"role": "user", "content": text}]


@mcp.prompt(name="prompt.tx.explain", title="Explain Transaction")
def prompt_tx_explain(transaction_json: str) -> list[dict]:
    text = prompt_catalog.render_prompt("prompt.tx.explain", transaction_json=transaction_json)
    return [{"role": "user", "content": text}]


@mcp.prompt(name="prompt.tx.summarize_list", title="Summarize Transactions")
def prompt_tx_summarize_list(transactions_json: str) -> list[dict]:
    text = prompt_catalog.render_prompt(
        "prompt.tx.summarize_list", transactions_json=transactions_json
    )
    return [{"role": "user", "content": text}]


@mcp.prompt(name="prompt.wallet.balance_summary", title="Wallet Balance Summary")
def prompt_wallet_balance_summary(balance_json: str) -> list[dict]:
    text = prompt_catalog.render_prompt("prompt.wallet.balance_summary", balance_json=balance_json)
    return [{"role": "user", "content": text}]


@mcp.prompt(name="prompt.error.help", title="Error Help")
def prompt_error_help(error_message: str, context: str) -> list[dict]:
    text = prompt_catalog.render_prompt(
        "prompt.error.help", error_message=error_message, context=context
    )
    return [{"role": "user", "content": text}]


@mcp.prompt(name="prompt.security.seed_guidance", title="Seed Phrase Guidance")
def prompt_security_seed_guidance() -> list[dict]:
    text = prompt_catalog.render_prompt("prompt.security.seed_guidance")
    return [{"role": "user", "content": text}]

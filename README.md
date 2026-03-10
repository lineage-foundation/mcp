# Lineage MCP Server

MCP server for the Lineage API using Python, uv, and pyproject.

## References

- [MCP Overview](https://modelcontextprotocol.io/)
- [Transports (Streamable HTTP)](https://modelcontextprotocol.io/docs/concepts/transports)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Lineage SDK (PyPI)](https://pypi.org/project/lineage/)

## Quickstart (dev)

- **Env**
  - `cp .env.example .env` and set `LINEAGE_PASSPHRASE`. Optional: `MCP_ALLOW_ORIGINS=*`, hosts.
- **Install**
  - `uv venv -p 3.11 .venv && source .venv/bin/activate`
  - `uv sync --extra dev`
  - `uv pip install -e .`
- **Run**
  - `uv run uvicorn lineage_mcp.server:app --host 0.0.0.0 --port 8000`
- **Test**
  - `uv run pytest -q`
- **MCP Inspector** (install & run)
  - Requires Node.js 18+ or Docker.
  - Option A (npx, no install):
    - `npx @modelcontextprotocol/inspector@latest`
  - Option B (global install):
    - `npm install -g @modelcontextprotocol/inspector`
    - `mcp-inspector`
  - Option C (Docker):
    - `docker run --rm -p 5173:5173 ghcr.io/modelcontextprotocol/inspector:latest`
  - In the Inspector UI, add a server:
    - Transport: Streamable HTTP
    - URL: `http://localhost:8000/mcp`
    - If using dev auth: set `MCP_DEV_AUTH_TOKEN` on the server and provide `Authorization: Bearer <token>` in Inspector requests.
  - Try tools: `wallet.generate_seed_phrase`, `wallet.generate_keypair`, `wallet.get_balance`, `blockchain.get_latest_block`, `health`, `version`.

## Links

- [Lineage Foundation](https://lineage.foundation)
- [Other SDKs](https://github.com/lineage-foundation) – sdk-python, sdk-php, sdk-js, sdk-laravel

# Execution Plan: 05 - Run & Test

**Objective:** Run the server locally, validate tools via automated tests and the official MCP Inspector, and ensure transport behavior (headers/CORS) works as expected.

References
- MCP Overview: https://modelcontextprotocol.io/
- Transports (Streamable HTTP): https://modelcontextprotocol.io/docs/concepts/transports
- MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk
- MCP Inspector (official UI to explore/test MCP servers)

---

### Phase 1: Local Run
- **Purpose:** Start the server for manual and Inspector-based validation.
- **Action (guidance):**
  - Ensure env is set (e.g., `LINEAGE_PASSPHRASE`, optional hosts, `MCP_ALLOW_ORIGINS=*` for dev).
  - Run: `uv run uvicorn lineage_mcp.server:app --host 0.0.0.0 --port 8000`
  - Verify endpoint: `http://localhost:8000/mcp`

---

### Phase 2: Automated Tests
- **Purpose:** Provide repeatable validation for tool I/O and transport basics.
- **Action (guidance):**
  - Unit tests: validators and pydantic schemas (invalid/valid cases).
  - Tool tests: mock SDK clients and assert responses mirror SDK payloads (no field renaming), e.g., `get_latest_block`, `wallet.get_balance`.
  - Server import test: module loads; tools registered.
  - Basic transport test: request headers round-trip (`X-Request-Id` present) and body-limit rejection (413) using ASGI TestClient.

---

### Phase 3: MCP Inspector
- **Purpose:** Interactive validation of tool discovery and calls.
- **Action (guidance):**
  - Launch the official MCP Inspector.
  - Configure a connection to `http://localhost:8000/mcp` (Streamable HTTP).
  - Confirm tool listing shows: `generate-seed-phrase`, `generate-keypair`, `get-balance`, `fetch-balance`, `get-latest-block`, `get-block-by-number`, `get-entry-by-hash`, `get-total-supply`, `get-issued-supply`, `get-transaction-by-hash`, `fetch-transactions`, plus `health`, `version`.
  - Confirm prompts listing includes registered prompt names (e.g., `prompt.block.explain_header`, `prompt.tx.explain`).
  - Fetch a prompt and verify it returns a list of one user message with rendered content.
  - Execute sample calls and verify responses and headers (e.g., `Mcp-Session-Id`).
  - For dev auth, set `MCP_DEV_AUTH_TOKEN` on server and provide `Authorization: Bearer <token>` in Inspector requests when testing privileged tools.

Deployment sanity (Railway)
- Build: logs show `uv sync` with pyproject/uv.lock detected by Railpack.
- Start: command uses `/app/.venv/bin/uvicorn ... --port $PORT`. No `uv not found`.
- Runtime: tools list, prompts list/get work via Inspector.

---

### Phase 4: Developer Ergonomics
- **Purpose:** Make run/test actions easy.
- **Action (guidance):**
  - Add Makefile or `uv run` scripts for: run, test, fmt/lint.
  - Document quickstart in `README.md` (run, test, Inspector usage).

---

### Acceptance Criteria
- Server runs locally and responds at `/mcp`.
- Automated tests cover validators, schemas, tool happy-path, and basic transport behavior.
- MCP Inspector lists and executes the core tools successfully.
- README quickstart includes run/test/Inspector instructions.

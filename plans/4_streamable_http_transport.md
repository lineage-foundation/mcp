# Execution Plan: 04 - Streamable HTTP Transport

**Objective:** Configure the MCP server for Streamable HTTP, enabling stateless operation, browser/client access via CORS, and minimal auth suitable for local/dev.

References
- MCP Overview: https://modelcontextprotocol.io/
- Transports (Streamable HTTP): https://modelcontextprotocol.io/docs/concepts/transports
- MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk

---

### Phase 1: Transport Goals & Constraints
- **Stateless sessions**: no server-side session storage; derive any state from request context/headers.
- **Single endpoint**: expose the SDK’s Streamable HTTP ASGI app at the root path `/`.
- **Browser-friendly**: enable CORS with a safe allowlist for dev.
- **Security**: minimal bearer/API key for privileged tools (dev only); production hardening later.
- **Limits**: conservative timeouts, body size limits, and request ID logging.

---

### Phase 2: Abstract Execution Protocol

**Step 2.1: Use SDK app directly**
- **Purpose**: respect MCP transport lifecycle.
- **Action (guidance)**: `app = mcp.streamable_http_app()`; expose at root path; do not wrap in another framework.

**Step 2.2: CORS**
- **Purpose**: allow local browser clients; block unexpected origins by default.
- **Action (guidance)**: configure CORS via ASGI middleware or server settings; expose `Mcp-Session-Id`.

**Step 2.3: Stateless session headers**
- **Purpose**: support Streamable HTTP session continuity without server persistence.
- **Action (guidance)**: read/propagate session identifiers; do not persist server-side.

**Step 2.4: Timeouts & limits**
- **Purpose**: avoid resource exhaustion.
- **Action (guidance)**: set request timeout and max body size; enforce at server/middleware layer.

**Step 2.5: Minimal auth (dev)**
- **Purpose**: gate privileged tools during development.
- **Action (guidance)**: accept `Authorization: Bearer <token>` if `MCP_DEV_AUTH_TOKEN` is set; apply only to privileged tools.

**Step 2.6: Logging & request IDs**
- **Purpose**: improve troubleshooting.
- **Action (guidance)**: generate/request `X-Request-Id`; log tool name, request ID, duration; avoid logging sensitive data.

**Step 2.7: Run & quick test**
- **Purpose**: validate transport locally.
- **Action (guidance)**:
  - Run: `uv run uvicorn lineage_mcp.server:app --host 0.0.0.0 --port 8000`
  - Inspector: Streamable HTTP to `http://localhost:8000`

Deployment (Railway)
- Use `railpack.json` to define install (`uv sync`) and start (`uv run uvicorn ... --port $PORT`).
- Expose the same Streamable HTTP app at root; no path prefix.

---

### Acceptance Criteria
- Streamable HTTP exposed at root and reachable locally.
- CORS enabled with env-driven allowlist; `Mcp-Session-Id` exposed.
- Stateless behavior confirmed; no server-side session store.
- Minimal bearer auth enforced for privileged tools in dev.
- Timeouts/body-size limits configured; request IDs logged.

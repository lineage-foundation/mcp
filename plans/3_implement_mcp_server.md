# Execution Plan: 03 - Implement MCP Server (Python SDK)

**Objective:** Scaffold the MCP server using the Python SDK, register tools/resources from Step 2, and prepare the app for Streamable HTTP transport (finalized in Step 4).

References
- MCP Overview: https://modelcontextprotocol.io/
- Transports (Streamable HTTP): https://modelcontextprotocol.io/docs/concepts/transports
- MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk

---

### Phase 1: Design Decisions
- **Tool naming**: consistent namespaces (`wallet.*`, `blockchain.*`).
- **Validation**: validate at tool boundary with Pydantic; return clear JSON results.
- **Config**: load env via `python-dotenv` in dev; no secrets in code; 12‑factor.
- **Errors**: map invalid params → `INVALID_ARGUMENT`, upstream outage → `UPSTREAM_UNAVAILABLE`, unknown → `INTERNAL`.

---

### Phase 2: Abstract Execution Protocol

**Step 2.1: Create server entry module**
- **Purpose**: define SDK server instance and expose ASGI app.
- **Action**: create server module that initializes the MCP server via the SDK and imports tool callables.

**Step 2.2: Register tools via SDK decorators**
- **Purpose**: bind Step 2 tools/resources in the standard way.
- **Action**: register `health`, `version`, `wallet.generate_seed_phrase`, `wallet.generate_keypair`, `wallet.get_balance`, `wallet.fetch_balance`, `blockchain.get_latest_block`, `blockchain.get_block_by_number`, `blockchain.get_entry_by_hash`, `blockchain.get_total_supply`, `blockchain.get_issued_supply`, `blockchain.get_transaction_by_hash`, `blockchain.fetch_transactions` using the SDK’s decorators.

**Step 2.3: Register prompts via SDK decorators (optional)**
- **Purpose**: expose reusable prompt templates.
- **Action**: use `@prompt()` to register named prompts that return a list of user messages (rendered from templates).

**Step 2.3: Wire config and clients**
- **Purpose**: construct `BlockchainClient` using env hosts.
- **Action**: load config per request; avoid global singletons that capture secrets.

**Step 2.4: Input/Output validation**
- **Purpose**: ensure stable contracts.
- **Action**: use Pydantic models for request/response; serialize to JSON-safe structures.

**Step 2.5: Health and version tools**
- **Purpose**: diagnostics and version visibility.
- **Action**: add `health` → `{ ok, time }`, `version` → `{ ok, version }`.

**Step 2.7: Prepare for Streamable HTTP**
- **Purpose**: ready the ASGI app for transport wiring in Step 4.
- **Action**: expose the SDK’s Streamable HTTP ASGI app directly at root (no extra framework wrapping).

**Step 2.7: Sanity checks (guidance)**
- **Purpose**: validate server module import and tool presence.
- **Action**: add minimal import test; run tests locally.

---

### Acceptance Criteria
- Server module created using MCP Python SDK.
- Tools from Step 2 registered with consistent names and validation.
- Config/client wiring implemented (env‑driven; no secrets in code).
- Health/version tools present.
- ASGI `app` exposed, ready for Streamable HTTP in Step 4.

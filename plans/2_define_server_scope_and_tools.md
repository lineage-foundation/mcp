# Execution Plan: 02 - Define Server Scope & Tools

**Objective:** Define the initial MCP tools and resources the server will expose, grounded in the Lineage SDK capabilities, with clear request/response shapes, validation rules, and error conventions.

References
- MCP Overview: https://modelcontextprotocol.io/
- Transports (Streamable HTTP): https://modelcontextprotocol.io/docs/concepts/transports
- MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk
- Lineage SDK (PyPI): https://pypi.org/project/lineage/

---

### Phase 1: Scope & Assumptions

- Use Lineage SDK primitives:
  - Wallet: seed phrase generation, keypair generation, transaction signing, create item assets, check balances.
  - BlockchainClient: latest block, block by number, entry by hash, total/issued supply, balance for address.
- Configuration via env (dotenv in dev):
  - Required: `LINEAGE_PASSPHRASE` (for wallet ops that need signing)
  - Optional: `LINEAGE_STORAGE_HOST`, `LINEAGE_MEMPOOL_HOST`, `LINEAGE_VALENCE_HOST`
- Security: treat passphrase-sensitive tools as privileged; require opt-in auth mechanism (to be implemented in later step).
- Data model: prefer simple, typed JSON objects; use strings for big ints/hashes to avoid precision issues.

---

### Phase 2: Tool Definitions (Guidance-Only Specs)

Use the following as guidance for implementing MCP tools (function names are suggestions). All tools must:
- Validate inputs (types, non-empty, formatting like hex addresses/hashes).
- Return outputs that mirror the Lineage SDK payloads exactly (no field renaming or reshaping). Include all fields the SDK returns.
- Log request ID and tool name for observability (added later).

1) generate-seed-phrase
- Input: `{ entropyBits?: number }` (optional; default per SDK)
- Output: Mirror SDK structure exactly.
- Errors: `INVALID_ARGUMENT`, `INTERNAL`
- Notes: Do not log or persist seed phrase.

2) generate-keypair
- Input: `{ seedPhrase?: string }` (optional; if omitted, generate ephemeral one)
- Output: Mirror SDK structure exactly.
- Errors: `INVALID_ARGUMENT`, `INTERNAL`
- Notes: Only include `secretKey` in explicitly privileged contexts; by default, omit. Prefer returning an opaque `keyId` in future.

3) get-balance
- Input: `{}` (current wallet)
- Output: Mirror SDK structure exactly.
- Errors: `INVALID_ARGUMENT`, `NOT_FOUND`, `UPSTREAM_UNAVAILABLE`
- SDK mapping: `BlockchainClient.get_balance(address)`

4) create-item-asset
- Input: `{ keyId?: string, seedPhrase?: string, name: string, metadata?: object }`
- Output: Mirror SDK structure exactly.
- Errors: `UNAUTHENTICATED` (if missing signing material), `INVALID_ARGUMENT`, `UPSTREAM_UNAVAILABLE`, `FAILED_PRECONDITION`
- Notes: Either use `seedPhrase` (dev) or a managed `keyId` (prod). Ensure idempotency keys if creating server-side.

5) sign-transaction
- Input: `{ keyId?: string, seedPhrase?: string, transaction: object }`
- Output: Mirror SDK structure exactly.
- Errors: `UNAUTHENTICATED`, `INVALID_ARGUMENT`, `INTERNAL`

6) blockchain-get-latest-block
- Input: `{}`
- Output: Mirror SDK structure exactly.
- Errors: `UPSTREAM_UNAVAILABLE`, `INTERNAL`
- SDK mapping: `BlockchainClient.get_latest_block()`

7) blockchain-get-block-by-number
- Input: `{ height: number }`
- Output: Mirror SDK structure exactly.
- Errors: `INVALID_ARGUMENT`, `NOT_FOUND`, `UPSTREAM_UNAVAILABLE`
- SDK mapping: `BlockchainClient.get_block_by_num(height)`

8) blockchain-get-entry-by-hash
- Input: `{ hash: string }`
- Output: Mirror SDK structure exactly.
- Errors: `INVALID_ARGUMENT`, `NOT_FOUND`, `UPSTREAM_UNAVAILABLE`
- SDK mapping: `BlockchainClient.get_blockchain_entry(hash)`
11) get-transaction-by-hash
- Input: `{ tx_hash: string }`
- Output: Mirror SDK structure exactly.
- Errors: `INVALID_ARGUMENT`, `NOT_FOUND`, `UPSTREAM_UNAVAILABLE`
- SDK mapping: `BlockchainClient.get_transaction_by_hash(tx_hash)`

12) fetch-transactions
- Input: `{ tx_hashes: string[] }`
- Output: Mirror SDK structure exactly.
- Errors: `INVALID_ARGUMENT`, `UPSTREAM_UNAVAILABLE`
- SDK mapping: `BlockchainClient.fetch_transactions(tx_hashes)`

9) get-total-supply
- Input: `{}`
- Output: Mirror SDK structure exactly.
- Errors: `UPSTREAM_UNAVAILABLE`
- SDK mapping: `BlockchainClient.get_total_supply()`

10) get-issued-supply
- Input: `{}`
- Output: Mirror SDK structure exactly.
- Errors: `UPSTREAM_UNAVAILABLE`
- SDK mapping: `BlockchainClient.get_issued_supply()`

---

### Phase 3: Resource Definitions

- No resources are exposed initially. Revisit after core tools stabilize.

Prompts (optional)
- Keep prompts minimal and reusable; register via FastMCP `@prompt()`.
- Prompts are templates (not tools) and return a list of user messages.

---

### Phase 4: Schemas & Conventions

- Types
  - `address`, `hash`: lowercase hex strings; validate length and charset
  - `amount`, `supply`: decimal strings
  - `timestamp`: ISO 8601 string
- Errors (tool-level)
  - `INVALID_ARGUMENT`: 400; missing/invalid params
  - `UNAUTHENTICATED`: 401; missing signing material/credentials
  - `FAILED_PRECONDITION`: 412; preconditions not met (e.g., missing wallet state)
  - `NOT_FOUND`: 404; no such block/entry/address
  - `UPSTREAM_UNAVAILABLE`: 503; Lineage endpoints unavailable/timeouts
  - `INTERNAL`: 500; uncaught exceptions
- Authentication (placeholder)
  - Add a minimal bearer/API key check later; tools affecting state (create/sign) should require auth.

---

### Phase 5: Initialization & Wiring (Guidance)

- Construct `BlockchainClient` with hosts from env; validate and raise descriptive error if hosts malformed.
- For wallet ops, prefer:
  - dev: pass `seedPhrase` explicitly (never log);
  - prod: use managed `keyId` indirection (to be added in a later step).
- Provide a minimal validator utility for inputs (addresses, hashes, amounts).

---

### Acceptance Criteria
- Tool and resource list finalized as above.
- Inputs/outputs and error contracts documented for each.
- Security posture documented (privileged vs read-only tools).
- Ready to implement in Step 3 with MCP Python SDK tool handlers and resource providers.

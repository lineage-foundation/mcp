# Execution Plan: 06 - Prompts (Optional, Guidance-Only)

**Objective:** Add small, reusable prompt templates that clients can list and render. Keep templates parameterized, versioned, and aligned to SDK-shaped data returned by tools.

References
- MCP Overview: https://modelcontextprotocol.io/
- Prompts concept (MCP): server-provided templates discoverable by clients

---

### Phase 1: Scope & Principles
- Start with zero prompts; add only when they deliver repeatable value.
- Do not include secrets or dynamic data; prompts are templates, not tools.
- Keep short, parameterized, and documented; mirror SDK JSON fields.

---

### Phase 2: Prompt Catalog (Initial Set)
- prompt.block.explain_header(vars: header_json)
  - Purpose: Explain `block.header` fields such as `b_num`, `previous_hash`, `timestamp`.
  - Action (guidance): Provide a concise explanation of each field and relevance.
- prompt.block.summarize(vars: block_json)
  - Purpose: Summarize a block (header + transactions at a high level).
  - Action: Short summary; avoid derived values not present in SDK payload.
- prompt.tx.explain(vars: transaction_json)
  - Purpose: Explain important fields of a transaction record.
  - Action: Map to SDK fields; no renaming.
- prompt.tx.summarize_list(vars: transactions_json)
  - Purpose: Summarize multiple transactions briefly.
  - Action: One-line per tx, referencing SDK field names.
- prompt.wallet.balance_summary(vars: balance_json)
  - Purpose: Summarize wallet balance(s) returned by SDK.
  - Action: Keep phrasing consistent; no derived math.
- prompt.error.help(vars: error_message, context)
  - Purpose: Provide next-step troubleshooting guidance for a given error string.
  - Action: Suggest common checks (env vars, network, auth) without leaking secrets.
- prompt.security.seed_guidance(vars: none)
  - Purpose: Remind users about seed phrase safety and handling.
  - Action: Short, security-first guidance.

---

### Phase 3: Implementation Guidance
- Define a `prompts` module to hold templates as strings with placeholders.
- Register prompts using FastMCP `@prompt()` decorator (SDK standard). Each prompt returns a list of user messages.
- Version prompts (e.g., `v1`) in names or metadata for safe evolution.

---

### Acceptance Criteria
- Catalog documented with names, variables, and purpose.
- No secrets or volatile content included.
- Ready to implement listing/rendering in a later step.

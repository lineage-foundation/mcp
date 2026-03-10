# Execution Plan: 01 - Lineage MCP Project Initialization

**Objective:** Establish the foundational project environment for the Lineage MCP Server using Python, uv, and `pyproject.toml`, preparing for MCP Python SDK and Streamable HTTP transport.

---

### **Phase 1: Tooling and Architecture**

1.  **Python Tooling Selection:** Use **`uv`** for Python environment and package management.
    * **Rationale:** `uv` provides high-speed dependency management and modern packaging via `pyproject.toml`.

2.  **MCP-first Architecture:** The project targets an MCP server exposing tools and resources, to be served over Streamable HTTP transport for stateless horizontal scaling.

3.  **Project Structure:** A clean Python package under `src/lineage_mcp` with linting, typing, and tests.
    * **Target Structure:**
        ```
        /
        ├── pyproject.toml
        ├── uv.lock
        ├── src/
        │   └── lineage_mcp/
        │       ├── __init__.py
        │       └── __about__.py
        ├── plans/
        │   ├── masterplan.md
        │   └── 1_project_initialization.md
        ├── .gitignore
        ├── .editorconfig
        ├── README.md
        └── .env.example
        ```

---

### **Phase 2: Abstract Execution Protocol**

The following steps describe the actions to be performed to set up the project environment.

**Step 2.1: Prepare Tooling**

* **Purpose:** Ensure the necessary package manager is installed.
* **Action:** Install `uv` if not already available.

```bash
brew install uv
# or
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Step 2.2: Initialize Project Metadata**

* **Purpose:** Define project metadata and dev tooling in `pyproject.toml`.
* **Action (guidance):**
  - Set `project` fields: name `lineage-mcp`, version `0.1.0`, description, authors, license, `requires-python >=3.11`.
  - Add runtime dependencies now to unblock development:
    - `lineage` (Lineage SDK) [PyPI](https://pypi.org/project/lineage/)
    - `python-dotenv` (12‑factor env loading)
    - `pydantic` (schemas/validation)
    - `uvicorn` (ASGI server)
    - MCP Python SDK package (servers & clients) per official docs
  - Add `dev` extra with `ruff`, `mypy`, `pytest`, `pytest-cov`, `httpx`.
  - Configure `ruff`, `mypy`, and `pytest` minimally (line length, python version 3.11, add `src` to path).
  - Packaging (src layout): configure setuptools in `pyproject.toml` to package from `src` (build-system, `tool.setuptools` with `package-dir` and `packages.find`).
  - Note: For Streamable HTTP, do not wrap the MCP ASGI app with Starlette; use the SDK’s `mcp.streamable_http_app()` directly.

**Step 2.3: Scaffold Directory Structure**

* **Purpose:** Create base package and quality-of-life files.
* **Action (guidance):**
  - Create `src/lineage_mcp/` with `__init__.py` and `__about__.py` (expose `__version__`).
  - Create `.gitignore` (ignore `.venv/`, `__pycache__/`, bytecode, `uv.lock`, IDE dirs, `.pytest_cache/`).
  - Create `.editorconfig` (LF, UTF‑8, 2-space indent, trim trailing whitespace).
  - Create `README.md` with project summary and links to:
    - MCP Overview: https://modelcontextprotocol.io/
    - Transports (Streamable HTTP): https://modelcontextprotocol.io/docs/concepts/transports
    - MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk
    - Lineage SDK: https://pypi.org/project/lineage/

**Step 2.4: Create and Activate Virtual Environment**

* **Purpose:** Use an isolated virtual environment for reproducibility.
* **Action:**

```bash
uv venv -p 3.11 .venv
# Activate for your shell (examples):
source .venv/bin/activate        # bash/zsh
# fish:    source .venv/bin/activate.fish
# PowerShell: .venv\Scripts\Activate.ps1
# cmd.exe:  .venv\Scripts\activate.bat
```

**Step 2.5: Install Runtime and Dev Dependencies**

* **Purpose:** Ensure runtime and development packages are installed now to unblock development.
* **Action:**

```bash
# Add runtime deps (if not already in pyproject)
uv add lineage python-dotenv pydantic uvicorn
# Add the MCP Python SDK package as per official docs (servers & clients)
uv add modelcontextprotocol
# Install all deps including dev extras
uv sync --extra dev
# Editable install so imports work without PYTHONPATH
uv pip install -e .
```

**Step 2.6: Environment Variables & 12‑Factor**

* **Purpose:** Centralize configuration via environment variables; load from `.env` in local/dev using `python-dotenv`.
* **Action (guidance):**
  - Create `.env.example` including keys:
    - `LINEAGE_PASSPHRASE` (required)
    - `LINEAGE_STORAGE_HOST`, `LINEAGE_MEMPOOL_HOST`, `LINEAGE_VALENCE_HOST` (optional)
    - `LOG_LEVEL`
    - `MCP_ALLOW_ORIGINS` (dev CORS allowlist)
    - `MCP_DEV_AUTH_TOKEN` (dev bearer token for privileged tools)
    - `REQUEST_TIMEOUT_S`, `MAX_BODY_MB` (transport limits)
  - Add a minimal config loader module that loads dotenv locally and reads from `os.environ`.

**Step 2.7: Sanity Checks**

* **Purpose:** Validate the baseline setup locally.
* **Action:**

```bash
uv run ruff check .
uv run mypy src
uv run pytest -q
uv run python -c "import lineage_mcp, lineage_mcp.__about__ as ab; print(ab.__version__)"
```

---

**Step 2.8: Deployment Config (Railway)**

* **Purpose:** Provide minimal deployment config to build and start with `uv` on Railway.
* **Action (guidance):**
  - Add a `railpack.json` at repo root.
  - Install using `uv sync` (runtime deps only) and start with uvicorn binding `$PORT`.
  - Example start: `uv run uvicorn lineage_mcp.server:app --host 0.0.0.0 --port $PORT`

Notes
- Keep deployment config minimal and environment-driven; no secrets committed.
- Use the same Streamable HTTP app exposed at root.

---

**Conclusion:** Upon completion of these steps, the Lineage MCP project will have a robust, reproducible foundation aligned with 12‑factor principles (environment variables via `python-dotenv`), a virtual environment managed by `uv` (explicitly activated), installed runtime and dev dependencies, and readiness for subsequent MCP server and Streamable HTTP transport implementation.

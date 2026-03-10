from __future__ import annotations

from typing import Any, Dict, List


class PromptTemplate:
    def __init__(self, name: str, description: str, variables: List[str], template: str) -> None:
        self.name = name
        self.description = description
        self.variables = variables
        self.template = template

    def render(self, **kwargs: Any) -> str:
        return self.template.format(**kwargs)


PROMPTS: Dict[str, PromptTemplate] = {
    "prompt.block.explain_header": PromptTemplate(
        name="prompt.block.explain_header",
        description="Explain block.header fields (e.g., b_num, previous_hash, timestamp).",
        variables=["header_json"],
        template=(
            "Given the following SDK-shaped block header JSON, explain each field succinctly:\n"
            "{header_json}\n"
            "Keep names exactly as in the JSON; do not rename or derive new fields."
        ),
    ),
    "prompt.block.summarize": PromptTemplate(
        name="prompt.block.summarize",
        description="Summarize a block (header + transactions).",
        variables=["block_json"],
        template=(
            "Summarize this SDK-shaped block JSON in 3-5 lines, referencing fields verbatim:\n"
            "{block_json}"
        ),
    ),
    "prompt.tx.explain": PromptTemplate(
        name="prompt.tx.explain",
        description="Explain a single transaction's key fields.",
        variables=["transaction_json"],
        template=(
            "Explain the important fields of this SDK-shaped transaction JSON.\n"
            "Use exact field names; keep it concise.\n"
            "{transaction_json}"
        ),
    ),
    "prompt.tx.summarize_list": PromptTemplate(
        name="prompt.tx.summarize_list",
        description="Summarize multiple transactions briefly.",
        variables=["transactions_json"],
        template=(
            "Provide one short line per transaction from this SDK-shaped list:\n"
            "{transactions_json}"
        ),
    ),
    "prompt.wallet.balance_summary": PromptTemplate(
        name="prompt.wallet.balance_summary",
        description="Summarize wallet balance(s) from SDK-shaped response.",
        variables=["balance_json"],
        template=(
            "Summarize these wallet balance details without deriving values or renaming fields:\n"
            "{balance_json}"
        ),
    ),
    "prompt.error.help": PromptTemplate(
        name="prompt.error.help",
        description="Troubleshooting guidance for an error, without revealing secrets.",
        variables=["error_message", "context"],
        template=(
            "Given this error message: {error_message}\n"
            "And this context: {context}\n"
            "Suggest next steps to troubleshoot (env vars, network, auth)."
        ),
    ),
    "prompt.security.seed_guidance": PromptTemplate(
        name="prompt.security.seed_guidance",
        description="Safety guidance for handling seed phrases.",
        variables=[],
        template=(
            "Security reminder: Never share or log seed phrases. Store them securely. "
            "Use environment variables or secret managers; avoid plaintext and version control."
        ),
    ),
}


def list_prompt_names() -> List[str]:
    return list(PROMPTS.keys())


def get_prompt(name: str) -> PromptTemplate:
    if name not in PROMPTS:
        raise KeyError(f"Prompt not found: {name}")
    return PROMPTS[name]


def render_prompt(name: str, **kwargs: Any) -> str:
    return get_prompt(name).render(**kwargs)



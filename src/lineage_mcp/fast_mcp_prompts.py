from lineage_mcp.prompts import render_prompt
from mcp.server.fastmcp import FastMCP
from lineage_mcp.core.context import ServerContext


def register(mcp: FastMCP, ctx: ServerContext):
    @mcp.prompt(name="prompt.block.explain_header", title="Explain Block Header")
    def prompt_block_explain_header(header_json: str) -> list[dict]:
        text = render_prompt("prompt.block.explain_header", header_json=header_json)
        return [{"role": "user", "content": text}]

    @mcp.prompt(name="prompt.block.summarize", title="Summarize Block")
    def prompt_block_summarize(block_json: str) -> list[dict]:
        text = render_prompt("prompt.block.summarize", block_json=block_json)
        return [{"role": "user", "content": text}]

    @mcp.prompt(name="prompt.tx.explain", title="Explain Transaction")
    def prompt_tx_explain(transaction_json: str) -> list[dict]:
        text = render_prompt("prompt.tx.explain", transaction_json=transaction_json)
        return [{"role": "user", "content": text}]

    @mcp.prompt(name="prompt.tx.summarize_list", title="Summarize Transactions")
    def prompt_tx_summarize_list(transactions_json: str) -> list[dict]:
        text = render_prompt("prompt.tx.summarize_list", transactions_json=transactions_json)
        return [{"role": "user", "content": text}]

    @mcp.prompt(name="prompt.wallet.balance_summary", title="Wallet Balance Summary")
    def prompt_wallet_balance_summary(balance_json: str) -> list[dict]:
        text = render_prompt("prompt.wallet.balance_summary", balance_json=balance_json)
        return [{"role": "user", "content": text}]

    @mcp.prompt(name="prompt.error.help", title="Error Help")
    def prompt_error_help(error_message: str, context: str) -> list[dict]:
        text = render_prompt("prompt.error.help", error_message=error_message, context=context)
        return [{"role": "user", "content": text}]

    @mcp.prompt(name="prompt.security.seed_guidance", title="Seed Phrase Guidance")
    def prompt_security_seed_guidance() -> list[dict]:
        text = render_prompt("prompt.security.seed_guidance")
        return [{"role": "user", "content": text}]

"""HTML served to browsers that hit the MCP server (GET / or /mcp).

Self-contained documentation page styled with the Lineage explorer design
system (dark teal oklch palette, Space Grotesk / Inter / JetBrains Mono, the
aurora cyan->green accent). Kept as a single string so the ASGI handler can
return it without any static-file plumbing.
"""

from __future__ import annotations

from .__about__ import __version__

INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Lineage MCP Server</title>
<meta name="description" content="Model Context Protocol server for the Lineage blockchain. Explorer-first reads verified on-chain, item metadata search, and wallet tools — for any MCP client." />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
<style>
  :root {
    --bg-canvas: oklch(13% 0.018 200);
    --bg: oklch(15% 0.018 200);
    --bg-raised: oklch(18% 0.020 200);
    --surface: oklch(20% 0.022 200);
    --surface-2: oklch(25% 0.024 198);
    --text: oklch(95% 0.010 195);
    --text-muted: oklch(73% 0.016 195);
    --text-subtle: oklch(60% 0.016 195);
    --border: oklch(29% 0.022 200);
    --border-strong: oklch(38% 0.026 200);
    --accent: oklch(82% 0.16 165);
    --accent-strong: oklch(86% 0.15 167);
    --accent-ink: oklch(18% 0.05 175);
    --link: oklch(78% 0.12 218);
    --link-hover: oklch(85% 0.11 218);
    --success: oklch(83% 0.17 150);
    --warning: oklch(82% 0.14 80);
    --radius-sm: 4px;
    --radius-md: 8px;
    --radius-lg: 12px;
    --font-display: "Space Grotesk", ui-sans-serif, system-ui, sans-serif;
    --font-sans: "Inter", ui-sans-serif, system-ui, sans-serif;
    --font-mono: "JetBrains Mono", ui-monospace, "SFMono-Regular", monospace;
    --ease: cubic-bezier(0.2, 0.8, 0.2, 1);
    --aurora: linear-gradient(105deg, oklch(80% 0.13 215), oklch(83% 0.17 162));
  }

  * { box-sizing: border-box; }
  html { scroll-behavior: smooth; }
  @media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } }

  body {
    margin: 0;
    background: var(--bg-canvas);
    color: var(--text);
    font-family: var(--font-sans);
    line-height: 1.6;
    -webkit-font-smoothing: antialiased;
  }

  .rail { height: 3px; background: var(--aurora); }

  a { color: var(--link); text-decoration: none; transition: color .15s var(--ease); }
  a:hover { color: var(--link-hover); }
  :focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; border-radius: var(--radius-sm); }

  .wrap { max-width: 940px; margin: 0 auto; padding: 0 24px; }

  /* Header */
  header.site {
    position: sticky; top: 0; z-index: 10;
    background: color-mix(in oklab, var(--bg-canvas) 82%, transparent);
    backdrop-filter: blur(10px);
    border-bottom: 1px solid var(--border);
  }
  .site .wrap { display: flex; align-items: center; justify-content: space-between; height: 60px; gap: 16px; }
  .brand { display: flex; align-items: center; gap: 10px; font-family: var(--font-display); font-weight: 600; font-size: 1.05rem; letter-spacing: -0.01em; color: var(--text); }
  .brand .dot { width: 12px; height: 12px; border-radius: 3px; background: var(--aurora); }
  nav.top { display: flex; gap: 22px; font-size: .9rem; color: var(--text-muted); }
  nav.top a { color: var(--text-muted); }
  nav.top a:hover { color: var(--text); }
  @media (max-width: 620px) { nav.top { display: none; } }

  /* Hero */
  .hero { padding: 76px 0 48px; }
  .eyebrow { font-family: var(--font-mono); font-size: .78rem; letter-spacing: .16em; text-transform: uppercase; color: var(--accent); margin: 0 0 18px; }
  h1 { font-family: var(--font-display); font-weight: 600; font-size: clamp(2.1rem, 5.4vw, 3.4rem); line-height: 1.05; letter-spacing: -0.025em; margin: 0 0 20px; max-width: 18ch; }
  h1 .grad { background: var(--aurora); -webkit-background-clip: text; background-clip: text; color: transparent; }
  .lede { font-size: 1.12rem; color: var(--text-muted); max-width: 62ch; margin: 0 0 32px; }

  .endpoint { display: inline-flex; align-items: stretch; border: 1px solid var(--border-strong); border-radius: var(--radius-md); overflow: hidden; background: var(--bg-raised); max-width: 100%; }
  .endpoint .label { font-family: var(--font-mono); font-size: .72rem; letter-spacing: .1em; text-transform: uppercase; color: var(--text-subtle); padding: 0 12px; display: flex; align-items: center; border-right: 1px solid var(--border); background: var(--surface); }
  .endpoint code { font-family: var(--font-mono); font-size: .92rem; color: var(--text); padding: 12px 14px; overflow-x: auto; white-space: nowrap; }
  .endpoint button { border: 0; border-left: 1px solid var(--border); background: transparent; color: var(--text-muted); font-family: var(--font-sans); font-size: .82rem; padding: 0 16px; cursor: pointer; transition: background .15s var(--ease), color .15s var(--ease); }
  .endpoint button:hover { background: var(--surface-2); color: var(--text); }

  /* Sections */
  section { padding: 40px 0; border-top: 1px solid var(--border); }
  .sec-head { display: flex; align-items: baseline; gap: 14px; margin: 0 0 24px; }
  .sec-head .idx { font-family: var(--font-mono); font-size: .8rem; color: var(--accent); }
  h2 { font-family: var(--font-display); font-weight: 600; font-size: 1.5rem; letter-spacing: -0.015em; margin: 0; }
  .sec-sub { color: var(--text-muted); margin: -12px 0 24px; max-width: 64ch; }

  /* Code blocks */
  pre { margin: 0 0 14px; background: var(--bg-raised); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 16px 18px; overflow-x: auto; position: relative; }
  pre code { font-family: var(--font-mono); font-size: .88rem; color: var(--text); line-height: 1.7; }
  .tok-key { color: var(--link); }
  .tok-str { color: var(--accent-strong); }
  .tok-cmt { color: var(--text-subtle); }
  .copy { position: absolute; top: 8px; right: 8px; border: 1px solid var(--border); background: var(--surface); color: var(--text-muted); border-radius: var(--radius-sm); font-size: .74rem; font-family: var(--font-sans); padding: 3px 9px; cursor: pointer; opacity: 0; transition: opacity .15s var(--ease), color .15s var(--ease); }
  pre:hover .copy, .copy:focus-visible { opacity: 1; }
  .copy:hover { color: var(--text); }

  .cols { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
  @media (max-width: 720px) { .cols { grid-template-columns: 1fr; } }
  .col h3 { font-family: var(--font-display); font-weight: 500; font-size: .95rem; color: var(--text-muted); margin: 0 0 10px; }

  /* How it works */
  .flow { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }
  @media (max-width: 720px) { .flow { grid-template-columns: 1fr; } }
  .step { background: var(--bg); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 20px; }
  .step .n { font-family: var(--font-mono); font-size: .78rem; color: var(--accent); margin: 0 0 10px; }
  .step h4 { font-family: var(--font-display); font-weight: 500; font-size: 1.05rem; margin: 0 0 6px; }
  .step p { color: var(--text-muted); font-size: .92rem; margin: 0; }

  /* Tools */
  .group { margin: 0 0 28px; }
  .group-title { display: flex; align-items: center; gap: 10px; margin: 0 0 4px; font-family: var(--font-display); font-weight: 500; font-size: 1.08rem; }
  .group-title .mark { width: 9px; height: 9px; border-radius: 2px; background: var(--accent); }
  .group-note { color: var(--text-subtle); font-size: .88rem; margin: 0 0 14px; }
  .tool { display: grid; grid-template-columns: 1fr auto; gap: 4px 16px; padding: 14px 0; border-top: 1px solid var(--border); }
  .tool:first-of-type { border-top: 0; }
  .tool .sig { font-family: var(--font-mono); font-size: .9rem; color: var(--text); }
  .tool .sig .args { color: var(--text-subtle); }
  .tool .desc { grid-column: 1 / 2; color: var(--text-muted); font-size: .9rem; }
  .tag { justify-self: end; align-self: start; font-family: var(--font-mono); font-size: .68rem; letter-spacing: .06em; text-transform: uppercase; padding: 3px 8px; border-radius: 999px; border: 1px solid var(--border-strong); color: var(--text-muted); white-space: nowrap; }
  .tag.verify { color: var(--accent); border-color: color-mix(in oklab, var(--accent) 40%, var(--border)); }
  .tag.write { color: var(--warning); border-color: color-mix(in oklab, var(--warning) 40%, var(--border)); }

  .callout { background: color-mix(in oklab, var(--warning) 10%, var(--bg)); border: 1px solid color-mix(in oklab, var(--warning) 35%, var(--border)); border-radius: var(--radius-md); padding: 14px 16px; font-size: .9rem; color: var(--text-muted); }
  .callout strong { color: var(--text); font-weight: 600; }

  footer { border-top: 1px solid var(--border); padding: 32px 0 56px; color: var(--text-subtle); font-size: .86rem; }
  footer .wrap { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 12px; }
  footer a { color: var(--text-muted); }

  .fade { opacity: 0; transform: translateY(8px); animation: rise .5s var(--ease) forwards; }
  @keyframes rise { to { opacity: 1; transform: none; } }
  @media (prefers-reduced-motion: reduce) { .fade { animation: none; opacity: 1; transform: none; } }
</style>
</head>
<body>
<div class="rail"></div>

<header class="site">
  <div class="wrap">
    <span class="brand"><span class="dot"></span> Lineage MCP</span>
    <nav class="top">
      <a href="#connect">Connect</a>
      <a href="#how">How it works</a>
      <a href="#tools">Tools</a>
      <a href="https://explorer.lineage.to">Explorer</a>
      <a href="https://github.com/lineage-foundation/mcp">GitHub</a>
    </nav>
  </div>
</header>

<main>
  <div class="wrap hero fade">
    <p class="eyebrow">Model Context Protocol &middot; Streamable HTTP</p>
    <h1>Query the Lineage chain from your <span class="grad">AI client</span>.</h1>
    <p class="lede">An MCP server that reads the Lineage blockchain explorer-first &mdash; fast, indexed lookups verified against on-chain state via the SDK &mdash; plus item&nbsp;metadata search and wallet tools. Point any MCP-compatible client at the endpoint below.</p>
    <div class="endpoint">
      <span class="label">Endpoint</span>
      <code id="ep">https://mcp.lineage.to/mcp</code>
      <button data-copy="https://mcp.lineage.to/mcp">Copy</button>
    </div>
  </div>

  <section id="connect">
    <div class="wrap">
      <div class="sec-head"><span class="idx">01</span><h2>Connect a client</h2></div>
      <p class="sec-sub">The server speaks MCP over Streamable HTTP. Read tools are open; wallet tools require server-side configuration.</p>
      <div class="cols">
        <div class="col">
          <h3>Claude Code</h3>
          <pre><button class="copy" data-copy="claude mcp add --transport http lineage https://mcp.lineage.to/mcp">Copy</button><code>claude mcp add --transport http \\
  lineage https://mcp.lineage.to/mcp</code></pre>
        </div>
        <div class="col">
          <h3>Cursor, Claude Desktop &amp; other clients</h3>
          <pre><button class="copy" data-copy='{"mcpServers":{"lineage":{"type":"http","url":"https://mcp.lineage.to/mcp"}}}'>Copy</button><code>{
  <span class="tok-key">"mcpServers"</span>: {
    <span class="tok-key">"lineage"</span>: {
      <span class="tok-key">"type"</span>: <span class="tok-str">"http"</span>,
      <span class="tok-key">"url"</span>: <span class="tok-str">"https://mcp.lineage.to/mcp"</span>
    }
  }
}</code></pre>
        </div>
      </div>
    </div>
  </section>

  <section id="how">
    <div class="wrap">
      <div class="sec-head"><span class="idx">02</span><h2>How it works</h2></div>
      <p class="sec-sub">Every read follows the same path: the block explorer answers first because it's indexed and searchable, then the Python SDK confirms the answer against the chain.</p>
      <div class="flow">
        <div class="step">
          <p class="n">Look up</p>
          <h4>Explorer first</h4>
          <p>The explorer API returns the block, transaction, balance, or item &mdash; indexed and quick to search.</p>
        </div>
        <div class="step">
          <p class="n">Verify</p>
          <h4>On-chain via SDK</h4>
          <p>The SDK re-fetches the same object and compares it. Responses carry a <code>verified</code> flag: <code>true</code>, <code>false</code>, or <code>unverified</code>.</p>
        </div>
        <div class="step">
          <p class="n">Fall back</p>
          <h4>Resilient by default</h4>
          <p>If the explorer is unreachable the SDK answers directly (<code>source: chain</code>). A lookup only fails if both are down.</p>
        </div>
      </div>
    </div>
  </section>

  <section id="tools">
    <div class="wrap">
      <div class="sec-head"><span class="idx">03</span><h2>Tools</h2></div>
      <p class="sec-sub">Eighteen tools. Names are kebab-case; every tool returns a JSON object with an <code>ok</code> field. Verified reads add <code>source</code>, <code>verified</code>, and <code>data</code>; pass <code>verify: false</code> to skip the on-chain check.</p>

      <div class="group">
        <p class="group-title"><span class="mark"></span> Reads &amp; verification</p>
        <p class="group-note">Explorer-first, confirmed on-chain.</p>
        <div class="tool"><span class="sig">get-latest-block<span class="args">(verify=true)</span></span><span class="tag verify">verified</span><span class="desc">The chain tip, with height and hash confirmed against the node.</span></div>
        <div class="tool"><span class="sig">get-block<span class="args">(id, verify=true)</span></span><span class="tag verify">verified</span><span class="desc">A block by height or hash.</span></div>
        <div class="tool"><span class="sig">get-transaction<span class="args">(hash, verify=true)</span></span><span class="tag verify">verified</span><span class="desc">A transaction, including inputs, outputs, and item metadata.</span></div>
        <div class="tool"><span class="sig">get-address-balance<span class="args">(address, verify=true)</span></span><span class="tag verify">verified</span><span class="desc">An address balance. Verification is timing-tolerant &mdash; a new block can move the balance between reads.</span></div>
        <div class="tool"><span class="sig">get-supply<span class="args">(verify=true)</span></span><span class="tag verify">verified</span><span class="desc">Circulating and total supply.</span></div>
      </div>

      <div class="group">
        <p class="group-title"><span class="mark"></span> Search &amp; listings</p>
        <p class="group-note">Explorer-only. Paginated with <code>limit</code>, <code>offset</code>, and <code>data</code>/<code>pagination</code>.</p>
        <div class="tool"><span class="sig">search-items<span class="args">(q?, genesis?, limit=20, offset=0)</span></span><span class="tag">explorer</span><span class="desc">Search minted items by metadata substring and/or genesis hash. Provide at least one of <code>q</code> or <code>genesis</code>.</span></div>
        <div class="tool"><span class="sig">list-blocks<span class="args">(limit=20, offset=0, order=desc)</span></span><span class="tag">explorer</span><span class="desc">Recent blocks.</span></div>
        <div class="tool"><span class="sig">list-transactions<span class="args">(limit=20, offset=0, order=desc)</span></span><span class="tag">explorer</span><span class="desc">Recent transactions (excludes coinbase).</span></div>
        <div class="tool"><span class="sig">list-block-transactions<span class="args">(id)</span></span><span class="tag">explorer</span><span class="desc">Every transaction in a block.</span></div>
        <div class="tool"><span class="sig">list-address-transactions<span class="args">(address, limit=20, offset=0)</span></span><span class="tag">explorer</span><span class="desc">An address's transaction history.</span></div>
        <div class="tool"><span class="sig">get-status</span><span class="tag">explorer</span><span class="desc">Chain and indexer status: network, ticker, height, counts.</span></div>
      </div>

      <div class="group">
        <p class="group-title"><span class="mark"></span> Wallet</p>
        <p class="group-note">Key generation is offline; transfer requires a server-configured seed.</p>
        <div class="tool"><span class="sig">generate-seed-phrase</span><span class="tag">wallet</span><span class="desc">A new 12-word BIP39 mnemonic.</span></div>
        <div class="tool"><span class="sig">generate-keypair<span class="args">(seedPhrase?)</span></span><span class="tag">wallet</span><span class="desc">A keypair &mdash; random, or derived deterministically from a seed phrase.</span></div>
        <div class="tool"><span class="sig">transfer-funds<span class="args">(destination, amount)</span></span><span class="tag write">write</span><span class="desc">Send <code>amount</code> in base units (integer) to an address. Requires <code>LINEAGE_SEED_PHRASE</code> on the server.</span></div>
      </div>

      <div class="group">
        <p class="group-title"><span class="mark"></span> Direct chain &amp; utility</p>
        <p class="group-note">SDK-only lookups and health.</p>
        <div class="tool"><span class="sig">get-entry-by-hash<span class="args">(hash)</span></span><span class="tag">chain</span><span class="desc">A raw blockchain entry by hash.</span></div>
        <div class="tool"><span class="sig">fetch-transactions<span class="args">(tx_hashes[])</span></span><span class="tag">chain</span><span class="desc">A batch of transactions by hash.</span></div>
        <div class="tool"><span class="sig">get-status &nbsp;&middot;&nbsp; health &nbsp;&middot;&nbsp; version</span><span class="tag">utility</span><span class="desc">Liveness and build info: <code>health</code> and <code>version</code> return <code>ok</code> and the server version.</span></div>
      </div>

      <p class="callout"><strong>Verification is provisional.</strong> The on-chain compare paths are still being tuned to the SDK's payload shapes, so a <code>verified: unverified</code> can appear where a match is expected. The returned <code>data</code> is always the explorer's answer regardless.</p>
    </div>
  </section>
</main>

<footer>
  <div class="wrap">
    <span>Lineage MCP Server &middot; v__VERSION__</span>
    <span>
      <a href="https://explorer.lineage.to">Explorer</a> &nbsp;&middot;&nbsp;
      <a href="https://lineage.foundation">Foundation</a> &nbsp;&middot;&nbsp;
      <a href="https://modelcontextprotocol.io/">About MCP</a>
    </span>
  </div>
</footer>

<script>
  document.querySelectorAll("[data-copy]").forEach(function (el) {
    el.addEventListener("click", function () {
      navigator.clipboard.writeText(el.getAttribute("data-copy")).then(function () {
        var prev = el.textContent;
        el.textContent = "Copied";
        setTimeout(function () { el.textContent = prev; }, 1400);
      });
    });
  });
</script>
</body>
</html>
""".replace("__VERSION__", __version__)

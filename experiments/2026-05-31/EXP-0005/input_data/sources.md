# EXP-0005 evidence sources (token-count anchors) — cited 2026-05-31

All numbers are TOKEN COUNTS used as a PROXY for KV-cache blocks. This is explicitly a proxy:
the CDC cost law (EXP-0002) is recompute% ~= injection_tokens / sequence_length (slope ~1), so a
token-count distribution maps directly onto the recompute-fraction distribution. No GPU/wall-clock here.

## A. System prompt + tool-schema bloat (the persistent base of agent context)
- dev.to "I Audited 11 MCP Servers. 22,945 Tokens Before a Single Message." (137 tools, 11 servers):
  22,945 tokens of tool definitions injected before the first user message. GitHub server alone the largest.
  https://dev.to/0coceo/i-audited-11-mcp-servers-22945-tokens-before-a-single-message-31e
- anthropics/claude-code#16466: a 60-tool MCP server measured ~15,000 tokens via count_tokens API
  (the /context UI over-reported ~45,000, 3x). So a heavy single-server agent base ~ 15k tokens.
  https://github.com/anthropics/claude-code/issues/16466
- arXiv 2511.07426 "Network and Systems Performance Characterization of MCP-Enabled LLM Agents":
  MCP prompt size grows ~linearly with #enclosed entries; repeated serialization of system prompt +
  tool schemas + interaction history + recent outputs drives most prompt inflation.
  https://arxiv.org/html/2511.07426

## B. Tool-RESULT (injection) sizes
- RAG retrieval chunks: child 128 tok / parent 1024 tok "small-to-big"; common targets 100/200/256/512 tok.
  Typical top-k = 3-5 retrieved chunks. So a RAG injection ~= k * chunk ~ 3*256=768 to 5*1024=5120 tok.
  manghumps.substack (128 child/1024 parent), ai21 query-dependent chunking (100/200/500),
  dev523.medium (chunk-size tradeoffs). https://www.ai21.com/blog/query-dependent-chunking/
- Web search tool result: typically top 5 results, each with title + URL + snippet(s); Brave "extra snippets"
  up to 5 excerpts per result. A 5-result block with full LLM-context snippets ~ few hundred to ~1-2k tokens.
  https://brave.com/search/api/  https://api-dashboard.search.brave.com/app/documentation/web-search/responses
- File reads / code-execution stdout / API-JSON dumps: HIGHLY variable, heavy right tail. OpenBB MCP issue
  #7315: a single tool response returned 210,004 tokens (> 200,000 window) - unbounded dataset dump.
  https://github.com/OpenBB-finance/OpenBB/issues/7315
  This is the "tool dump" worst case the committee crux is about.

## C. Agent context-window scale & trajectory
- Standard agent context window 200k (Claude 2.1+, Claude 3/4); 1M-token beta (Sonnet 4 / Opus 4.6).
  https://www.anthropic.com/news/claude-2-1 ; https://venturebeat.com/ai/claude-can-now-process-entire-software-projects-in-single-request-anthropic-says
- SWE agentic workloads are CACHE-READ DOMINATED: >97% of total token usage is cache-read (repeated
  context reuse across many steps) - arXiv 2602.08316 "SWE Context Bench". Implies long-lived, growing,
  heavily-reused context: exactly the prefix-cache regime CLAIM-0006 targets.
  https://arxiv.org/pdf/2602.08316
- AgencyBench 2601.11044: real-world autonomous-agent contexts at the 1M-token frontier.

## Regime thresholds (from EXP-0002 cost law, recompute% ~= inj/seq):
- CDC-WINS-BIG:  inj/seq <= 1%  (recompute <~2.4%, the headline regime)
- MID:           1% < inj/seq <= 5%
- CDC-DEGRADES:  inj/seq > 5%   (recompute >~5%, win shrinks / vanishes)

# EXP-0015 evidence sources (inherits EXP-0005 anchors; lane-A win-region sharpening)

This experiment REUSES the evidence-grounded token-size distributions of EXP-0005 verbatim
(see experiments/2026-05-31/EXP-0005/input_data/sources.md for the full citation list). It adds
bootstrap CIs + a systematic workload-prior sweep + the joint (inj/seq<=1% AND S>=50k) win-region.
All numbers are TOKEN COUNTS used as a PROXY for KV-cache recompute work (NOT GPU wall-clock).

## Cost-regime basis (where "win-region" comes from)
- EXP-0002 (CLAIM-0006): CDC recompute% ~= injection_tokens / sequence_length (slope ~1). The ~2%
  headline holds only at inj/seq ~ 1%. -> win-region threshold inj/seq <= 1%.
- EXP-0006: against a FAIR PIC-family baseline (EPIC/CacheBlend/MEPIC/Irminsul-style window+selective
  recompute), CDC's edge is only ~1.1-1.7x median and a TIE at inj/seq >= 5%; the durable CDC edge
  (~2-6x) lives only at inj/seq <~ 1% on small-to-mid contexts. The 8x-465x story is a retired
  artifact of contiguous baselines (vLLM-APC/Radix/FlashInfer).
- EXP-0013/VERDICT-0023: CDC slope = 0.958 [0.937,0.980], R2=0.972 -- a CDC-MECHANISM-SPECIFIC
  accounting identity, NOT a cross-engine law (contiguous engines R2=0.0007, position-driven). So
  the surviving CLAIM-0006 contribution is exactly this win-region characterization on CDC's line.

## Workload-size anchors (same as EXP-0005, cited)
- MCP tool-schema base context: dev.to "22,945 Tokens Before a Single Message" (137 tools/11 srv);
  anthropics/claude-code#16466 (~15k single heavy server). -> base context light~2k / typ~8k /
  heavy~23k / very-heavy~40k.
- Tool-result sizes w/ heavy right tails: RAG k(3-5)*chunk(128-1024); web_search 150-1800; file_read
  120-2000 (18% tail to 30k); code_exec 40-1500 (15% tail to 40k); api_json 80-2500 (20% tail to
  60k; OpenBB MCP #7315 worst case 210,004 tok). small_status 5-60.
- SWE agentic workloads are CACHE-READ DOMINATED: >97% of total token usage is cache-read (long-lived
  growing reused context) -- arXiv 2602.08316 "SWE Context Bench". This is the empirical basis for the
  S>=50k "large reused context" condition (CDC's home regime). AgencyBench 2601.11044: 1M-token frontier.

## Prior-sweep knobs (what we vary to test robustness of the win-region)
- tail_scale in {0.5, 1.0, 2.0, 3.0}: multiplies the heavy-tail "tool dump" probabilities (stress the
  "tool results are large" hypothesis -- the committee crux).
- ctx_scale in {0.5, 1.0, 2.0, 4.0}: scales the persistent base-context size (SWE-ContextBench/AgencyBench
  show real agent contexts trend large; ctx_scale>=2 models the long-horizon / 200k-1M regime).

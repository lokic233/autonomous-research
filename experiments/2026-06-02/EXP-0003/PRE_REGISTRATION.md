# PRE-REGISTRATION — EXP-0003 (GPU L1, CLAIM-0002)

**Claim:** CLAIM-0002 — An "adaptive 3-class" KV/prefix retention policy (protect hot-prefix FLOOR;
treat COMMITTED conversation scratch [USER+ASSISTANT appended-to-context] as normal LRU; evict
TRANSIENT one-shot TOOL-RESULT payloads FIRST) Pareto-dominates plain LRU and pin-shared-prefix-only.

**Hardware:** devgpu014 (8xH100, 1 GPU used). vLLM 0.22.0 + torch 2.11.0+cu130. Model:
Qwen/Qwen2.5-1.5B-Instruct (real tokenizer + real block-hash prefix caching). L0 (EXP-0002) used a
CPU sim with proxy tokens + ORACLE labels; this GPU pass measures the SYSTEM with a REAL
prompt-template inspector (role/marker-based TRANSIENT detection), not an oracle.

## Hypothesis (H1)
On a two-typed agentic trace (committed conversation scratch reused across turns + transient
one-shot tool payloads), under cache-capacity pressure, adaptive3 (evict-transient-first +
protect-prefix-floor) yields higher real prefix-cache hit-rate, lower TTFT, higher throughput, and
fewer recomputed prefill tokens than vLLM-default LRU — AND this gain is NOT captured by a generic
scan-resistant baseline that has no tool-boundary semantic tag.

## Baselines
1. **LRU** — vLLM default prefix caching (capacity-driven LRU eviction).
2. **scan-resistant** — classical one-touch / MRU-on-tail: evict blocks touched exactly once
   before blocks touched >1, NO tool-boundary tag (the KILLER baseline).
3. **adaptive3** — protect prefix floor; committed=LRU; transient(tool-result)=evict-first, where
   TRANSIENT is detected by a REAL prompt-template inspector (role markers), not oracle.
4. **pin-shared-prefix-only** (carried from L0 for continuity).
5. **Belady/MIN** offline optimal (upper bound on achievable headroom).

## Metrics
prefix-cache hit-rate (%), TTFT (ms, p50/p95), end-to-end throughput (req/s, tok/s),
recomputed-prefill-tokens, classifier overhead (us/req). All vs cache-capacity sweep.

## Sweeps
- **Cache capacity** (GPU): --gpu-memory-utilization / num-gpu-blocks proxy: {tight, mid, loose}.
- **COMMITTED:TRANSIENT ratio** {1:3, 1:1, 3:1} (L0 used only 1:1).
- **Misclassification** X% of TRANSIENT-labeled blocks actually re-referenced, X in {0,10,25,50}.

## Honest-negative branch (PRE-COMMITTED)
Report NEGATIVE / WEAKENED if ANY of:
(a) real-system TTFT/throughput gains vanish under classifier overhead; OR
(b) generic scan-resistant baseline captures >=80% of adaptive3's gain over LRU (tool-boundary
    classifier is then empty — it's just scan-resistant caching re-applied); OR
(c) misclassification at realistic rates collapses adaptive3 to LRU.

## Prior-art (live, 2026-06-02; egress via fwdproxy CONFIRMED)
- Continuum (2511.02230, Berkeley/Stanford) pins KV for tool-call-generating requests with a TTL —
  keeps the requestor's CONTEXT across the tool PAUSE. Distinct axis: it does not evict the returned
  tool-output tokens as transient-first. Closest prior art; novelty must be the SEMANTIC tool-output
  transient classification, not "tool calls matter for KV."
- KVFlow (2507.07400) prefix caching for multi-agent workflows (steady-state reuse).
- TRT-LLM KvCacheRetentionConfig: per-token-range priority+duration eviction API (see evidence #2).

## Reproducibility
harness.py (offline sim on REAL tokenized trace + Belady) + vllm_bench.py (real vLLM serving).
Seeds n>=5 where stochastic. Results -> RESULTS.md + CSVs.

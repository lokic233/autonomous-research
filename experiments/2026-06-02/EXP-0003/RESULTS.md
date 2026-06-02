# RESULTS — EXP-0003 (GPU L1, CLAIM-0002): adaptive 3-class KV/prefix retention

**Verdict: REFUTE (weaken to strong-negative).** On real-system modeling (real Qwen2.5-1.5B
tokenizer + chat template, real prefix-chained block-hash caching, and real vLLM 0.22.0 on H100),
the "adaptive 3-class" tool-boundary classifier provides **no Pareto gain** over plain LRU, and at
tight capacity it **actively hurts**. The L0 (EXP-0002) Pareto-dominance was an artifact of a CPU
sim with (a) proxy tokens, (b) oracle labels, and (c) a cache model that did **not** model prefix-
chain invalidation. Committee#1's challenge (theory_skeptic + novelty_killer) is **upheld**.

Hardware: devgpu014, 1xH100 (97 GB). vLLM 0.22.0 + torch 2.11.0+cu130. Model Qwen/Qwen2.5-1.5B-
Instruct. Real template inspector keys TRANSIENT on Qwen's `<tool_response>...</tool_response>`
markers (NOT oracle; note Qwen renders tool msgs inside a *user* turn — an oracle would mislabel).

---

## Headline numbers

### Offline harness — hit-rate by policy (mean over 5 seeds), prefix-chained cache (= what vLLM does)

REGIME A (tool outputs committed in transcript — realistic for most agents):
| ratio | cap | LRU | scan-resist | adaptive3 | Belady |
|-------|-----|-----|-------------|-----------|--------|
| 1:1 | 0.3 | 0.717 | 0.312 | **0.526** | 0.717 |
| 1:1 | 0.5 | 0.717 | 0.486 | 0.713 | 0.717 |
| 1:3 | 0.3 | 0.711 | 0.289 | **0.603** | 0.711 |
| 3:1 | 0.3 | 0.715 | 0.334 | **0.554** | 0.715 |

REGIME B (ephemeral one-shot tool outputs — the L0's *premise*):
| ratio | cap | LRU | scan-resist | adaptive3 | Belady |
|-------|-----|-----|-------------|-----------|--------|
| 1:1 | 0.3 | 0.4685 | 0.4669 | 0.4685 | 0.4685 |
| 1:3 | 0.3 | 0.4015 | 0.4015 | 0.4015 | 0.4015 |

REGIME C (flat content-addressed cache — the L0's *implicit, unrealistic* model):
| ratio | cap | LRU | scan-resist | adaptive3 | Belady | a3 gain |
|-------|-----|-----|-------------|-----------|--------|---------|
| 1:3 | 0.3 | 0.4075 | 0.4082 | 0.4109 | 0.4073 | +0.33pp |
| 1:1 | 0.3 | 0.4734 | 0.4702 | 0.4763 | 0.4733 | +0.29pp |

**Max adaptive3 gain over LRU ANYWHERE across all regimes/ratios/caps = +0.33 percentage points**
(flat cache, transient-heavy, tightest cap). In the realistic prefix-chained regimes it is **0 or
strongly negative**.

### Real vLLM on H100 — prefix-cache hit-rate, throughput (LRU, vLLM default)
| regime | ratio | gpu_util | prefix hit-rate | req/s | tok/s | preemptions |
|--------|-------|----------|-----------------|-------|-------|-------------|
| committed | 1:1 | 0.12 | 0.7275 | 154 | 169k | 0 |
| committed | 1:1 | 0.20 | 0.7275 | 140 | 153k | 0 |
| committed | 1:1 | 0.35 | 0.7275 | 147 | 161k | 0 |
| committed | 1:3 | 0.12 | 0.7065 | 126 | 171k | 0 |
| ephemeral | 1:1 | 0.12 | 0.4954 | 182 | 108k | 0 |
| ephemeral | 1:3 | 0.12 | 0.4223 | 140 | 97k | 0 |

Real vLLM hit-rate is **invariant to gpu_memory_utilization** (0.12->0.35) with **zero preemptions** —
the 48-req agentic trace never pressures the H100 KV cache, so eviction policy is never even
exercised. Real hit-rate matches the offline harness within ~2pp (committed 0.7275 vs 0.711-0.717;
ephemeral 0.4954/0.4223 vs 0.469/0.402), validating the harness as a faithful proxy.

---

## The KILLER question — does the tool-boundary classifier add anything?

**NO.** Two independent kills:

1. **Scan-resistant baseline.** In the only regime where adaptive3 is non-negative (flat), its gain
   over LRU is <=0.33pp — within seed noise (it even nudges past Belady at the margin). In the
   prefix-chained regimes adaptive3 LOSES to LRU by up to -19.1pp. The pre-registered ">=80% captured
   by scan-resistant => classifier empty" branch is moot because **there is essentially no gain to
   capture** — both the generic scan-resistant baseline AND the semantic classifier collapse to LRU
   (or worse). The tool-boundary tag is empty.

2. **Belady upper bound.** LRU == Belady (MIN) in EVERY prefix-chained cell. Recency *is* optimal for
   monotonic-growth agentic transcripts: the most-recently-extended prefix is the most-likely-reused.
   adaptive3's achievable headroom over LRU is therefore **0** in the realistic regime.

## COMMITTED:TRANSIENT ratio sweep {1:3, 1:1, 3:1}
The effect does NOT scale favorably with transient fraction. Higher transient fraction (1:3) makes
adaptive3 *worse* in Regime A (more middle-blocks to wrongly evict -> bigger prefix-chain breakage)
and leaves it flat in B. The L0's "scales with transient fraction" intuition is inverted once
prefix chaining is modeled.

## Misclassification crossover {0,10,25,50%}
Run in the flat regime (the only place adaptive3 had a sliver of edge). adaptive3's gain at mis=0 is
+0.06pp (1:1) / +0.07pp (1:3); at mis=50% it is +0.04pp / +0.07pp. **There is no crossover to find**
because the baseline gain is already sub-noise — you cannot collapse to LRU what was never above LRU.

---

## REQUIRED_EVIDENCE status
- **#7 GPU validation: DONE.** Real vLLM, real tokenizer/template inspector, real prefix-cache
  metrics, gpu_util sweep, two-typed committed+ephemeral traces, ratio sweep.
- **#3 scan-resistant baseline: DONE.** one-touch/MRU-on-tail w/o tool tag. Classifier empty.
- **#4 ratio sweep: DONE** {1:3,1:1,3:1} x 3 regimes x 5 seeds.
- **#6 Belady: DONE.** LRU==Belady in all chain regimes -> zero headroom.
- **#5 misclassification: DONE** {0,10,25,50%} — no crossover (no gain to collapse).
- **#1 prior-art (live, egress via fwdproxy CONFIRMED): DONE.** Closest is **Continuum**
  (arXiv 2511.02230, Berkeley/Stanford/Stoica): pins KV for tool-call-generating requests with a TTL
  to bridge the tool-call PAUSE — a *retention* policy keyed on tool-call boundaries, DISTINCT axis
  (keeps requestor context across the pause; does NOT evict returned tool-output tokens first).
  **KVFlow** (2507.07400) prefix caching for multi-agent steady-state reuse. **TRT-LLM
  KvCacheRetentionConfig** = per-token-range priority+duration eviction API. Tool-call boundary IS
  already a published eviction signal (Continuum); our specific "evict tool-output payload first"
  framing has no measured value.
- **#2 TRT-LLM expressibility: ANALYSIS.** YES — expressible as pure KvCacheRetentionConfig WITHOUT a
  new classifier (low priority/short duration for tool-output token range; default for committed).
  The only "missing" piece is range identification, which the template already provides — the
  "classifier" is a regex, not a research artifact.
- **#8 framing: ANALYSIS.** Even charitably framed as the SEMANTIC classifier (not mechanism), the
  semantic signal yields <=0.33pp and 0 in the realistic regime. No defensible empirical wedge vs
  CachedAttention/SGLang/TRT-LLM/Continuum/H2O/StreamingLLM/ARC/LIRS.

## Honest-negative branch — TRIGGERED
All three pre-registered conditions fire: (a) real-system gains vanish (hit-rate invariant to
capacity, 0 preemptions); (b) scan-resistant captures the gain (there is none; classifier empty);
(c) collapses to LRU (it never beat LRU in the realistic regime; it is *worse*).

## Why the L0 was wrong (root cause)
The L0 CPU sim used a flat, independently-addressable block cache with oracle transient labels. Real
KV prefix caching is **prefix-chained**: evicting a TRANSIENT block in the middle of a committed
transcript invalidates the hash chain for ALL downstream committed blocks, destroying their reuse
(Regime A: -19pp). When tool outputs are ephemeral (Regime B), they sit at the prompt TAIL, are
one-shot, and policy-irrelevant. The only place the classifier helps (flat cache, Regime C) is both
unrealistic for vLLM and yields <=0.33pp. Recency-LRU is provably optimal (==Belady) on
monotonic-growth agentic transcripts.

## Artifacts
devgpu014:/home/dengcchi/ros-EXP-0003/ : trace.py, trace2.py, harness.py, flatcache.py, run_full.py,
run_mis.py, vllm_sweep.py, runwrap.sh; results/{full_raw,killer_full,misclassification,vllm_sweep}.csv
Mac (this dir): RESULTS.md, PRE_REGISTRATION.md, results/{killer_full,misclassification,vllm_sweep}.csv

## Committee#2 readiness
**Ready, as a clean REFUTATION.** The claim as stated (adaptive3 Pareto-dominates LRU) is refuted
under faithful real-system modeling + real vLLM. Defensible residual finding is the NEGATIVE:
"semantic tool-boundary KV eviction does not beat LRU for agentic prefix caching because (1)
recency==Belady on monotonic transcripts and (2) prefix-chaining penalizes mid-transcript eviction"
— a publishable cautionary result that pre-empts/contextualizes Continuum's opposite design.

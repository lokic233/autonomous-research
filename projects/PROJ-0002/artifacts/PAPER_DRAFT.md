# Characterizing the Recompute Cost of Prefix-Cache Invalidation under Agentic Tool Injection: A Cost-Map, a Workload-Conditioned Win-Region, and an Honest Competitive Bracket

**Claim:** CLAIM-0006 · **Project:** PROJ-0002 · **Target venue:** MLSys
**Draft type:** Path-(b) submittable paper draft (honest conditional characterization), incorporating the EXP-0030 real-kernel result.
**Author of this draft:** researcher-0006-prose · reporting to orchestrator 22bd6bef · **Date:** 2026-05-31
**Status:** CPU writing only. NO claim/verdict/map/experiment edits. Every number is copied (not re-derived) from registry evidence (CLAIM-0006.yaml VERDICT-0006..0041, EXP result.md files, novelty_boundary_2026-05-31.md). Nothing invented.

> **Provenance note.** This draft supersedes WRITEUP_SYNTHESIS.md on exactly one point: WRITEUP_SYNTHESIS scoped the real published-fused-kernel measurement (EXP-0030) as *future work*. EXP-0030 has since landed (CDC wins 12/12 on the real lmcache CacheBlend gather kernel). This draft folds EXP-0030 in as a **measured result** and re-scopes the open gate to **EXP-0034** (combined real-lmcache end-to-end TTFT), which is being built in a separate lane. The cost-map, win-region, novelty, and competitive-bracket prose are otherwise inherited from the synthesis spine.

---

## Abstract

Agentic LLM serving repeatedly injects tool results into a reused prompt prefix, invalidating prefix caches *mid-sequence* rather than at the suffix. We characterize the **cost** of this invalidation as an engine-internal **recompute-fraction cost-map** over the injection-to-sequence ratio (`inj/seq = R/S`, for an injection of `R` tokens into a reused prefix of length `S`). Measuring the real block/token accounting of vLLM-APC, SGLang-RadixAttention, and FlashInfer, we show these contiguous-prefix engines are **position-driven** (recompute cost ≈ `1 − position`, R²=0.0007 vs `inj/seq`, ≈69 pp swing across edit position), whereas a content-defined re-syncing (CDC) repair is **`inj/seq`-driven and position-independent** (slope 0.958, 95% CI [0.937, 0.980], R²=0.972; 0.13 pp position spread) (EXP-0013). We are explicit that this slope≈1 is a **mechanism-derived accounting identity** (cf. CacheBlend's `r%`↔overhead dial, arXiv:2405.16444 §4; Pope et al., arXiv:2211.05102 for the underlying KV accounting), *not* an emergent cross-engine law, and that the CDC repair *mechanism* itself is not novel (Irminsul arXiv:2605.05696; the Position-Independent-Caching / PIC family). Our contribution is the cost-map plus a **workload-conditioned win-region**: over a realistic agentic workload (20k tasks, 291,454 injections), CDC's recompute win-region is **negligible by injected tokens** (≤8.1% under every prior tested; 3.7% [0.0361, 0.0379] at the base prior — so any token-weighted or unconditional framing is **unsupported**), but **conditioned on large reused context (S≥50k), CDC wins ~46% of injections** (count-level 0.457 [0.453, 0.461], prior-robust 41–52% across a 4×4 prior grid) (EXP-0015). We then bracket CDC's serving advantage **honestly and now with the real shipping kernel**: CDC wins every cell against a re-implemented PIC on real vLLM PagedAttention (EXP-0026, 12/12 E2E TTFT + throughput); a *zero-overhead oracle* PIC is conditionally favorable at low `inj/seq` (EXP-0027, CDC wins 2/6); and the **real published lmcache CacheBlend GATHER kernel still pays scatter cost, so CDC's contiguous gather wins 12/12** (EXP-0030, the load-bearing new result; CI excludes 1.0 in 11/12). The remaining tie-down — a single *combined* real-lmcache end-to-end TTFT cell that controls the composition fallacy (per-component wins may not compose under pipelining) — is the GREEN-gating future experiment (EXP-0034); both measured axes (real-kernel gather and re-impl E2E) already point the same way. We present this as an honest conditional characterization whose claims do not depend on that final gate.

---

## 1. Introduction & Motivation

Modern agentic LLM systems run long, multi-turn tool-use loops: the model reads a large reused context (a codebase, a document set, prior turns) and repeatedly **injects tool results back into the middle of the prompt** — a file read, a search result, a JSON blob, a RAG passage. Each such injection is a *mid-prefix* edit. Whereas conventional prefix caching (vLLM Automatic Prefix Caching, SGLang RadixAttention, FlashInfer) is built around a *growing suffix* — you append, you reuse the shared prefix — agentic injection breaks the cache *in the middle*: every token after the injection point has its KV invalidated under a contiguous-prefix engine.

This raises a concrete systems question that production schedulers must answer: **what does a mid-prefix injection actually cost in recompute, and when is a content-defined repair worth it?** The folk answer ("just recompute the changed part") hides a structural fact: contiguous-prefix engines recompute *the whole suffix after the edit*, so their cost is governed by *where* you inject, not *how much*. A content-defined re-syncing (CDC) repair — re-chunking around the edit and re-syncing only a bounded boundary window — instead pays a cost governed by *how much* you inject relative to the context.

This paper is a **characterization paper, not a mechanism paper.** The CDC-over-radix repair mechanism is explicitly conceded non-novel (Irminsul + the PIC family — body-verified, §4). Our contribution is three-fold:

1. **The recompute-fraction cost-map** (§2): the engine-internal cost of mid-prefix invalidation as a function of `inj/seq`, with a decisive per-engine decomposition showing the contiguous engines are position-driven while CDC is `inj/seq`-driven.
2. **The workload-conditioned win-region** (§3): where real agentic traffic actually sits on that map, with bootstrap CIs, and the honest finding that the win is a *conditional, count-level* statement (large reused context ∧ small injection), negligible by tokens.
3. **An honest competitive bracket** (§5): exactly where CDC-style contiguous repair wins and loses against re-impl, oracle, and now the **real published fused** PIC kernel.

We motivate the cost question, lay out the cost-map, locate real traffic on it, close the novelty boundary, bracket the competition honestly, and state the single weakest link as scoped future work.

---

## 2. The Recompute-Fraction Cost-Map

### 2.1 The relation

For a pure mid-prefix insertion of `R` tokens into a reused prefix of length `S`, a content-defined re-syncing scheme (CDC) recomputes the `R` new tokens plus a bounded boundary re-sync window `W`. Its recompute fraction is

```
recompute% = (R + W) / S  ≈  R/S = inj/seq     (for W ≪ R; slope ≈ 1)
```

and is **flat in edit position** (prepend ≈ interior ≈ terminal), EXCEPT the sequence-start attention-sink chunk (§2.4).

### 2.2 Accounting identity vs measured contribution (the load-bearing honesty boundary)

This is the single most important honesty boundary in the paper, enforced by hostile review (VERDICT-0017). We state it explicitly:

- **ACCOUNTING IDENTITY (derived, NOT a discovery).** "`recompute% ~ inj/seq` with slope ≈ 1" for a perfectly re-syncing scheme is the *algebra of contiguous-chunk KV bookkeeping*: recompute `= R + W`, fraction `= (R+W)/S`, slope 1 by construction with no free parameter. CacheBlend (arXiv:2405.16444, EuroSys'25 §4) states the same identity as a *tuning dial* ("recompute `r%` of tokens ⇒ `r%` of full-prefill overhead"); Pope et al. (arXiv:2211.05102) gives the underlying KV accounting. **We cite CacheBlend §4 + Pope for the identity** so the slope is not over-claimed as emergent. We do **not** pitch slope≈1 as a "law."

- **WHAT IS ACTUALLY MEASURED (the real, empirical contribution).**
  1. That CDC *achieves* the near-`W=0` re-sync on realistic agentic insertions (not adversarial re-chunk cascades) — i.e. that real injections land on the identity line. Quantified per-engine with CIs (EXP-0013).
  2. That this is a **CDC-mechanism-specific** property, NOT a cross-engine law — the decisive decomposition (§2.3).
  3. The empirical **workload distribution** of `inj/seq` locating *where on the identity line real traffic sits* (§3).

### 2.3 Per-engine cost-map with CIs (EXP-0013)

CPU, stdlib; 405 cells/engine; Student-t + Wilson + bootstrap. The decisive result is that the cost-map is **two different cost laws**, and slope≈1 belongs to one engine class only:

| engine | slope of recompute% vs `inj/seq` | 95% CI | R² | governing variable |
|---|---|---|---|---|
| **CDC** | **0.958** | **[0.937, 0.980]** | **0.972** | `inj/seq` (slope≈1, tight) |
| PIC (lean) | 0.907 | [0.738, 1.076] | 0.333 | `inj/seq` (noisier, `W` floor) |
| vLLM-APC | 0.476 | [−1.94, 2.89] | **0.0007** | **position, NOT `inj/seq`** |
| SGLang-RadixAttention | 0.475 | [−1.94, 2.88] | **0.0007** | **position, NOT `inj/seq`** |
| FlashInfer | 0.475 | [−1.94, 2.88] | **0.0007** | **position (== host engine)** |

- The CDC slope is **stable per sequence length** (4k: 0.989, 8k: 0.930, 32k: 0.956; R²→0.999) — not an averaging artifact.
- The three contiguous baselines are **position-driven**: position spread ≈ **69.3 pp** (vLLM-APC / Radix / FlashInfer) vs **CDC 0.13 pp** (max 0.52 pp). Their R²≈0 vs `inj/seq` means they have *no* `inj/seq` relationship — their cost is `≈ (1 − position)`.
- **Engine-AVERAGED slope is an artifact.** Averaging the three contiguous engines gives slope 0.258, R²=0.075 — a meaningless fit. The honest statement: slope≈1 is the **CDC accounting identity**, not a cross-engine law (theory_skeptic CONFIRMED, VERDICT-0017).
- Supporting margin CIs (EXP-0013): CDC-vs-lean-PIC median margin 1.77× [1.56, 1.87] across all cells / 6.20× [5.15, 6.86] at `inj/seq`≤1% / tie 1.29× [1.25, 1.33] at `inj/seq`≥5%. Win-region `inj/seq`≤1% = 100% [Wilson 0.972, 1.0].

### 2.4 Caveats baked into the cost-map (state, do not bury)

- **PROXY:** token-count recompute fraction, not GPU wall-clock (wall-clock is the serving leg, §5).
- **Sequence-start attention-sink:** position-independence holds EXCEPT the first content-defined chunk. Per-engine attention-sink first-chunk fraction: CDC 0.12%, vLLM-APC 0.22%, Radix 0.014%, PIC 3.47% (EXP-0013). Irminsul body-confirms the position-0 sink is the one genuinely position-dependent corner. The paper writes "position-independent EXCEPT the sequence-start sink."
- **Anchor reproduction (EXP-0002):** the original "~2%" reproduces exactly (CTX=4000, inj=40 → 2.0–2.4%) but is a **thin contour at `inj/seq`≈1%**, not a universal property: surface min 0.02% / median 1.34% / max 53.05%; breaks to 5.3% @200tok/4k, 20% @1000tok/4k, 49–53% @1000tok/1k. So "~2%" is a *conditional cost-map contour*, not a CDC property; edit position is not the cost driver — injection size relative to context is.

---

## 3. The Workload-Conditioned Win-Region

EXP-0015: bootstrap CIs over 20k tasks / 291,454 injections, with a 4×4 (16-cell) workload-prior sweep. (Reproduces the EXP-0005 points: median `inj/seq` = 2.8%; count-fraction `inj/seq`≤1% = 0.246 [0.243, 0.250]; token-fraction = 0.037 [0.036, 0.038].)

### 3.1 The honest headline (the win-region is CONDITIONAL, COUNT-LEVEL only)

The win-region lives on **two axes that point in opposite directions**; conflating them is the over-claim hostile review killed (VERDICT-0023):

| metric | value | 95% CI | framing verdict |
|---|---|---|---|
| **Token-weighted** win-region (`inj/seq`≤1%), base prior | **0.037** | [0.0361, 0.0379] | token / unconditional framing **UNSUPPORTED** |
| Token-weighted win-region across ALL 16 priors | 0.027–0.081 (median 0.037) | ≤0.004 half-width | **never exceeds ~8.1%** under any prior |
| Count-fraction win-region (`inj/seq`≤1%), marginal | 0.2461 | [0.2426, 0.2495] | minority of injections |
| **Conditional count-level win GIVEN S≥50k** (CDC home) | **0.4573** | **[0.4531, 0.4613]** | **the surviving, defensible claim** |
| Count-frac-given-S≥50k across 16 priors | 0.411–0.520 (median 0.477) | — | **prior-STABLE ~½** |

### 3.2 The precise honest statement (verbatim into the paper)

> "**By injected tokens — the work that actually costs latency — the win-region is negligible** (3.7% at the base prior; ≤8.1% under every prior tested; ≥92% of injected tokens fall in the mid/degrade regimes where CDC ties a fair PIC baseline). Any token-weighted or unconditional 'CDC saves recompute on agentic traffic' framing is **not supported**. **By injection count, conditioned on large reused context (S≥50k), small tool injections (`inj/seq`≤1%) are common and CDC wins ~46% of them (0.457 [0.453, 0.461]), prior-robustly (41–52% across a 4×4 prior grid).** This conditional count-level win-region is the defensible characterization."

So the win-region is real and prior-robust **only** as a *conditional, count-level* statement (S≥50k ∧ `inj/seq`≤1%). It is a meaningful minority of *injections* but a small minority of *tokens*. This weakens the unconditional/token framing and does not weaken further than VERDICT-0023 already states.

### 3.3 Why S≥50k is the right condition

As context-scale rises (modeling 200k–1M long-horizon agents), the *share* of traffic that is large-context grows to 60–76% (EXP-0005/0015), consistent with SWE-ContextBench's >97%-cache-read finding for long-horizon SWE work. So the conditional region, while a minority today, covers a growing fraction of real traffic.

---

## 4. Novelty Positioning (gate-A — FULLY CLOSED at body level, 10/10 neighbors)

**Gate-A is GREEN/uncontested** (2/5 reviewers GREEN on novelty+systems at VERDICT-0041; the remaining YELLOW are on the orthogonal serving-measurement gate, §5). Body-verified facts (novelty_boundary_2026-05-31.md):

- **10/10 closest neighbors body-read (full LaTeXML HTML bodies), ZERO cost-map collision:**
  - **Don't Break the Cache (arXiv:2601.06007):** black-box provider $/TTFT vs prompt-size & tool-COUNT; no `inj/seq` axis, no recompute-fraction, no engine-internal granularity. *(The #1 "same functional form" collapse-fear — REFUTED at body level: their linearity is $-savings vs prompt-size, not recompute% vs `inj/seq`.)*
  - **Irminsul (arXiv:2605.05696):** CDC-over-radix **mechanism twin** (body-confirmed); its metrics are token-recovery% / prefill-energy / attention-sink, NOT a recompute cost-map. Indexed in ≥2 sources (Semantic Scholar + OpenAlex) — single-source flag cleared.
  - **PIC family** — EPIC (arXiv:2410.15332), CacheBlend (arXiv:2405.16444), Cache-Craft (arXiv:2502.15734), MEPIC (arXiv:2512.16822), KVFlow (arXiv:2507.07400), CacheClip (arXiv:2510.10129): all six body-verified distinct; metrics = TTFT / throughput / quality / memory / redundant-compute. **The word "injection" appears 0× in all six bodies.**
  - **ContiguousKV (arXiv:2601.13631):** offload-I/O re-prefill / read-amplification; append-suffix, not mid-prefix injection; "injection" 0×. **variable-size-block (arXiv:2604.23994):** discrete-diffusion block-COMMIT generation quality; not autoregressive KV invalidation; "injection"/"prefix cache" 0×.

- **Mechanism conceded non-novel:** CDC-over-radix repair = Irminsul + PIC genus; CDC insertion-resilience = FastCDC/Rabin (foundational). We do **not** pitch the mechanism.

- **slope≈1 demoted to accounting identity** (citing CacheBlend §4 `r%`↔overhead + Pope et al.), per §2.2.

- **Defensible novelty kernel (narrow, body-distinguished):** *An engine-internal characterization of prefix-cache recompute COST as a function of injection-to-sequence ratio (recompute% ~ `inj/seq`), MEASURED on the real block/token accounting of vLLM-APC / SGLang-Radix / FlashInfer, together with the empirical WORKLOAD-CONDITIONED win-region of CDC-style repair over that surface.* No prior work draws this contour.

**Residual on the novelty axis:** none. The only flagged risk — a cost-map encoded ONLY as an unlabeled plotted curve invisible to HTML-grep — is at VERY LOW risk; every neighbor's caption/axis framing is TTFT/throughput/quality/memory, none mentions injection.

---

## 5. Competitive Positioning (the honest bracket — now resolved on the GATHER axis with the real kernel)

The competitive story is **deliberately conditional** — this is the framing that survived hostile review (VERDICT-0029/0033/0037) — but the load-bearing uncertainty (does CDC survive the *shipping SOTA fused kernel*?) is now **resolved on the gather axis in CDC's favor by EXP-0030.**

| comparator | result | source | honest reading |
|---|---|---|---|
| **Contiguous baselines** (vLLM-APC / SGLang-Radix / FlashInfer) | CDC 8.3×–465× cheaper (token-recompute), grows with ctx | EXP-0003 | **STRUCTURAL ARTIFACT** of contiguous whole-suffix recompute (EXP-0006); **do NOT headline.** |
| **Fair re-impl PIC** (selective recompute over real vLLM page table), E2E serving | CDC wins **all 12 cells** on BOTH metrics; TTFT PIC/CDC 1.05–1.79×, throughput CDC/PIC 1.00–1.13×; PIC 0/12 | **EXP-0026** (real vLLM 0.6.6 PagedAttention, Qwen2.5-7B fp16, H100) | CDC's contiguous-prefill advantage **survives the non-contiguous paged KV layout** (the binding VERDICT-0029 question — ANSWERED). LIMITATION: lmcache absent → PIC is a faithful re-impl, NOT the published fused kernel. |
| **Oracle / fused PIC** (flash-optimal, ZERO gather overhead) | CDC wins **2/6** cells, both at HIGH `inj/seq` (25%: oraclePIC/CDC 1.054–1.175); **LOSES at low `inj/seq` (1–5%: oraclePIC/CDC 0.612–0.991×)** incl the win-region corner | **EXP-0027** (H100 SDPA oracle bound) | CDC's serving advantage is **itself conditional on `inj/seq`** — opposite direction to the recompute-fraction win-region (a real, publishable nuance). EXP-0026's "wins all 12" was PARTLY the re-impl PIC's gather overhead, as hostile review suspected. CAVEAT: CDC pays a boundary window `Wb=256` the oracle skips → conservative, PIC-favorable bound. |
| **Real published lmcache CacheBlend GATHER kernel** | **CDC contiguous gather wins ALL 12 cells; CI excludes 1.0 in 11/12 (only 8k/0.5% is a tie [0.994,1.028]); PIC/CDC 1.01–1.27×** | **EXP-0030** (source-built lmcache 0.1.dev1 `c_ops.single_layer_kv_transfer`, the published CacheBlend gather, on LIVE vLLM 0.6.6 PagedAttention paged KV, format `NL_X_TWO_NB_BS_NH_HS` discovered — NOT a re-impl) | **THE KEY NEW RESULT.** The oracle's zero-overhead assumption was too generous: the REAL fused kernel still pays scatter/page-gather cost, so CDC's contiguous gather wins. The bracket resolves **toward the re-impl result (CDC favorable), NOT the oracle (CDC loses).** Margins largest at large-ctx low-`inj/seq` (28k/0.5% = 1.265 [1.229,1.283]); smallest at the small-ctx low-`inj/seq` corner (8k/0.5% tie). |
| **Combined real-lmcache E2E-TTFT** (real CacheBlend kernel in the vLLM serving loop, CDC vs PIC, 12-cell) | not yet measured | **EXP-0034** (in-flight, separate lane / orchestrator-owned) | **The single remaining GREEN gate** — controls the composition fallacy (§7). See §6 for how we frame it. |

### 5.1 The full per-cell EXP-0030 table (the resolving result)

H100, Qwen2.5-7B, 28 layers, 12 cells, bootstrap CIs. PIC/CDC > 1 means CDC's gather is cheaper.

| `inj/seq` | 8k PIC/CDC [CI] | 28k PIC/CDC [CI] |
|---|---|---|
| 0.5% | 1.011 [0.994, 1.028] *(TIE)* | 1.265 [1.229, 1.283] |
| 1% | 1.068 [1.029, 1.078] | 1.228 [1.213, 1.231] |
| 2% | 1.103 [1.016, 1.109] | 1.208 [1.190, 1.212] |
| 5% | 1.108 [1.096, 1.114] | 1.114 [1.107, 1.126] |
| 10% | 1.075 [1.051, 1.082] | 1.088 [1.084, 1.089] |
| 25% | 1.057 [1.047, 1.070] | 1.028 [1.022, 1.037] |

CDC gather cheaper in 12/12; CI excludes 1.0 in 11/12; margins 1.01–1.27×.

### 5.2 Honest framing sentence for the paper

> "Against the dominant production stack (real vLLM PagedAttention), CDC-style contiguous repair wins on TTFT and throughput in every measured cell (EXP-0026). Against a *fused/oracle* PIC, that advantage was predicted to be conditional on `inj/seq` — CDC winning at high injection but a fused PIC matching or beating it at low injection (EXP-0027). We resolve this against the **real published lmcache CacheBlend gather kernel**: because the real fused kernel still pays scatter/page-gather cost, CDC's contiguous gather wins all 12 cells (EXP-0030), confirming the bracket resolves toward the re-impl (CDC-favorable) outcome, not the zero-overhead oracle. Both measured axes — real-kernel *gather* (EXP-0030) and re-impl *end-to-end TTFT* (EXP-0026) — point the same way. The one remaining tie-down is a single *combined* real-lmcache end-to-end-TTFT cell (the real CacheBlend kernel in the serving loop alongside selective-attention recompute), which we identify as the decisive remaining experiment."

### 5.3 Supporting kernel evidence (consistent; kernel-level, not full serving)

- EXP-0014: CDC faster in all 8 TTFT cells (PIC/CDC 1.02–2.68×); largest 2.68× at win-region corner (32k/0.1%).
- EXP-0021: all 8 cells CI95 excludes 1.0 (incl prev-ambiguous 32k/1% = 1.129 [1.128, 1.151]), 30 reps/cell.
- EXP-0025: throughput — CDC wins 22/24, PIC only 2/24 marginal (0.993–0.994×) at the 8k/5% corner; the predicted PIC-favorable high-`inj/seq` regime actually favors CDC *more* (1.5–1.74× at 50%).
- EXP-0023: analytic serving bridge — end-to-end PIC/CDC band [1.10, 2.03] nominal / [1.00, 1.28] worst-for-CDC; 0/8 cells invert under any plausible overhead; gather-overlap alone cannot flip CDC's advantage.

---

## 6. How We Frame the EXP-0034 Gate (combined E2E-TTFT)

Two honest framings are available, and the draft is written to support either depending on whether EXP-0034 lands before submission:

- **As GREEN-gating FUTURE WORK (the path-(b) default, recommended now).** The paper's spine — the cost-map (§2), the conditional win-region (§3), the closed novelty boundary (§4), and the competitive bracket *now resolved on the gather axis* (§5) — stands **independent of EXP-0034's outcome.** Both measured serving axes already favor CDC (EXP-0026 E2E vs re-impl; EXP-0030 gather vs the real kernel). EXP-0034 (the real CacheBlend kernel in the serving loop, end-to-end TTFT, 12-cell) is the single combined cell that ties down the composition. **An honest E2E loss is itself publishable** — it would *complete* the conditional characterization (the composition fallacy realized) rather than refute the cost-map or win-region.
  - *Feasibility note (must be stated honestly):* a *true* async-connector-in-serving-loop is **infeasible in the current pinned environment** — vLLM 0.6.6.post1 lacks the V1 `KVConnector` API (`vllm.distributed.kv_transfer.kv_connector.v1` does not exist), so `lmcache_connector_v1` cannot be imported (EXP-0034 SMOKE_RESULT). EXP-0034 therefore runs as a **scoped approximation** (inline real-CacheBlend kernels in the generate path), not a connector-in-loop. The paper must scope the combined cell as "real CacheBlend kernels, inline, end-to-end" and flag the connector-in-loop as the genuine remaining environment limitation.

- **As the CLOSING RESULT (if EXP-0034 lands before submission).** If the 12-cell combined run completes, fold its table into §5 as the final bracket row and promote the framing from "both component axes point the same way" to "the combined end-to-end measurement confirms it" (or, if it inverts, headline the composition fallacy as the honest finding — still publishable).

**Recommendation:** ship path-(b) with EXP-0034 as the GREEN-gating future-work/in-flight gate, since (a) the in-flight result is owned by a separate lane + the orchestrator, and (b) the environment cannot currently support the *true* connector-in-loop measurement.

---

## 7. Related Work, Conclusion, and the Single Weakest Link

### 7.1 Related work (condensed; full body-verifications in novelty_boundary_2026-05-31.md)

- **Mechanism family (conceded):** Irminsul (CDC-over-radix twin), EPIC / CacheBlend / Cache-Craft / MEPIC / KVFlow / CacheClip (PIC genus). CacheBlend (arXiv:2405.16444 §4) additionally supplies the `r%`↔overhead identity we cite; Pope et al. (arXiv:2211.05102) supplies the KV accounting.
- **Closest empirical cost-axis neighbor:** Don't Break the Cache (arXiv:2601.06007) — black-box $/TTFT vs prompt-size & tool-count, no engine-internal recompute-fraction, no `inj/seq` axis.
- **Adjacent systems (distinct):** ContiguousKV (offload-I/O re-prefill, append-suffix), variable-size-block (discrete-diffusion block-commit). Neither addresses mid-prefix autoregressive KV invalidation.
- **Foundational:** FastCDC / Rabin content-defined chunking (CDC insertion-resilience).

### 7.2 Conclusion

We characterized the recompute cost of prefix-cache invalidation under agentic mid-prompt tool injection as an engine-internal cost-map over `inj/seq`, decomposed it per-engine to show the contiguous production engines are *position-driven* (R²=0.0007) while CDC is *`inj/seq`-driven* (slope 0.958 [0.937, 0.980], R²=0.972) — being explicit that this slope is a mechanism-derived accounting identity, not an emergent law. We located real agentic traffic on that map and found the CDC win-region is negligible by tokens (≤8.1% under any prior) but a meaningful, prior-robust minority by injection count when conditioned on large reused context (≈46% given S≥50k). We closed the novelty boundary at the body level (10/10 neighbors, "injection" 0× in the PIC family, mechanism conceded) and bracketed CDC's serving advantage honestly — resolving the load-bearing uncertainty on the gather axis with the **real published lmcache CacheBlend kernel** (CDC wins 12/12, EXP-0030). The result is a defensible MLSys characterization paper whose spine is: *here is the cost-map; here is where real traffic sits on it; here, conditionally, is where CDC wins; here, honestly, is what remains to be measured end-to-end.*

### 7.3 The single honest weakest link

**The combined end-to-end measurement gap (the composition fallacy).** Our strongest serving evidence comes from **two separately-measured axes**: re-impl PIC measured *end-to-end* (EXP-0026, CDC 12/12) and the *real published kernel* measured at the *gather component* (EXP-0030, CDC 12/12). Per-component wins **may not compose** under pipelining/overlap in the full serving loop — that is the composition fallacy a hostile reviewer attacks (theory_skeptic, VERDICT-0041). The honest response:

- We **concede** that a single *combined* real-lmcache end-to-end TTFT cell (the real CacheBlend kernel in the serving loop, alongside selective-attention recompute FLOPs) is not yet measured (EXP-0034, in-flight, separate lane).
- We **scope it as the GREEN-gating future experiment**, not a hidden assumption. The cost-map, win-region, novelty, and the gather-axis resolution all stand independent of it.
- We note the **environment limitation honestly**: a true async-connector-in-serving-loop is infeasible under vLLM 0.6.6.post1 (no V1 KVConnector API; EXP-0034 SMOKE_RESULT), so the combined measurement runs as a scoped inline-kernel approximation.
- A measured combined result is **publishable either way**: if CDC wins, it closes the bracket; if it inverts, it *is* the composition-fallacy finding, which completes — rather than refutes — the conditional characterization.

This is the only binding residual. Novelty (gate-A) and the cost-map/win-region theory are GREEN/uncontested.

---

## 8. Submission-Readiness Verdict

**CLAIM-0006 is SUBMISSION-READY as an honest-conditional-characterization paper (operator path-(b)), now strengthened by the EXP-0030 real-kernel resolution.**

What makes it submittable:
1. **Cost-map:** measured, CI-quantified, per-engine decomposition (EXP-0002/0013). GREEN.
2. **Win-region:** bootstrap CIs, prior-robust, honestly conditional (EXP-0005/0015). GREEN as conditional.
3. **Novelty:** 10/10 neighbors body-verified distinct, mechanism conceded, slope≈1 demoted (cited). GREEN.
4. **Competitive bracket:** honestly conditional, committee-vetted, **gather axis now resolved with the real kernel** (EXP-0003/0006/0026/0027/**0030**). GREEN as conditional, strengthened.
5. **The one gap** (combined real-lmcache E2E-TTFT, EXP-0034) is scoped as the GREEN-gating future experiment, not hidden — and the paper's claims do not depend on it.

What it is NOT: a paper claiming CDC universally beats PIC, or a slope-law discovery, or a token-weighted win. Those framings are killed and must not be re-inflated.

**File:** prior_art/PROJ-0002/CLAIM-0006/PAPER_DRAFT.md

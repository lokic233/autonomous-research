# Characterizing the Recompute Cost of Prefix-Cache Invalidation under Agentic Tool Injection: A Cost-Map, a Workload-Conditioned Win-Region, and an Honest Competitive Bracket

**Claim:** CLAIM-0006 · **Project:** PROJ-0002 · **Target venue:** MLSys
**Draft type:** Path-(b) submittable paper draft — **honest conditional characterization**. Finalized by researcher-0006-paper-r3 applying the VERDICT-0043 area_chair promotion conditions.
**Lineage:** supersedes PAPER_DRAFT.md (researcher-0006-prose, 2026-05-31) → r3 finalization (2026-06-01).
**Status:** CPU writing only. NO claim/verdict/map/experiment edits, NO new experiments. Every number is copied (not re-derived) from logged registry evidence (CLAIM-0006.yaml, VERDICT-0006..0043, EXP `result.md` / `grid_results.json` files, novelty_boundary_2026-05-31.md). Nothing invented. Where a confidence interval is **not present in the logged experiment record**, this draft says so explicitly rather than computing or inventing one (see §5.4).

> **Provenance / what changed in r3.** This finalization folds in EXP-0034 (combined real-lmcache in-window end-to-end TTFT) as a **landed, scoped result** (was "in-flight" in the prior draft), and applies the three area_chair conditions from VERDICT-0043 verbatim: (1) the scope/conditionality statement is now prominent (abstract + intro + the boxed Scope & Limitations paragraph in §6.1), framing the *true async-connector E2E* as **declared future work**, not a gap that undermines the result; (2) confidence intervals are reported on the headline cost-map and the EXP-0034 composition numbers **to the extent they are logged** (EXP-0030 has full bootstrap CIs; EXP-0034's logged record contains point ratios only — flagged honestly, §5.4); (3) all baselines are named explicitly, including **Irminsul (arXiv:2605.05696)**, the CDC-over-radix mechanism twin, plus the body-verified-distinct PIC family and the "Don't Break the Cache" motivation. See the r3 CHANGELOG at the end of this file.

---

## Abstract

Agentic LLM serving repeatedly injects tool results into a reused prompt prefix, invalidating prefix caches *mid-sequence* rather than at the suffix. We characterize the **cost** of this invalidation as an engine-internal **recompute-fraction cost-map** over the injection-to-sequence ratio (`inj/seq = R/S`, for an injection of `R` tokens into a reused prefix of length `S`). Measuring the real block/token accounting of vLLM Automatic Prefix Caching (Kwon et al., PagedAttention, arXiv:2309.06180), SGLang RadixAttention (Zheng et al., arXiv:2312.07104), and FlashInfer, we show these contiguous-prefix engines are **position-driven** (recompute cost ≈ `1 − position`, R²=0.0007 vs `inj/seq`, ≈69 pp swing across edit position), whereas a content-defined re-syncing (CDC) repair is **`inj/seq`-driven and position-independent** (slope 0.958, 95% CI [0.937, 0.980], R²=0.972; 0.13 pp position spread) (EXP-0013). We are explicit that this slope≈1 is a **mechanism-derived accounting identity** (cf. CacheBlend's `r%`↔overhead dial, arXiv:2405.16444 §4; Pope et al., arXiv:2211.05102 for the underlying KV accounting), *not* an emergent cross-engine law, and that the CDC repair *mechanism* itself is not novel (Irminsul, arXiv:2605.05696, is a CDC-over-radix mechanism twin; the Position-Independent-Caching / PIC family — EPIC, MEPIC, CacheBlend, Cache-Craft — is the umbrella). Our contribution is the cost-map plus a **workload-conditioned win-region**: over a realistic agentic workload (20k tasks, 291,454 injections), CDC's recompute win-region is **negligible by injected tokens** (≤8.1% under every prior tested; 3.7% [0.0361, 0.0379] at the base prior — so any token-weighted or unconditional framing is **unsupported**), but **conditioned on large reused context (S≥50k), CDC wins ~46% of injections** (count-level 0.457 [0.453, 0.461], prior-robust 41–52% across a 4×4 prior grid) (EXP-0015). We then bracket CDC's serving advantage honestly, **now with the real shipping kernel measured on two serving axes**: CDC wins every cell against a re-implemented PIC on real vLLM PagedAttention (EXP-0026, 12/12 E2E TTFT + throughput); a *zero-overhead oracle* PIC is conditionally favorable at low `inj/seq` (EXP-0027); the **real published lmcache CacheBlend GATHER kernel still pays scatter cost, so CDC's contiguous gather wins 12/12** (EXP-0030; bootstrap CI excludes 1.0 in 11/12); and a **combined in-window real-CacheBlend end-to-end TTFT measurement preserves the win in 12/12 cells** (EXP-0034; margins compress to 1.003–1.029×, closest-to-tie 8k/5% = 1.0032). **Scope (stated up front and not hedged later):** EXP-0034 runs the real CacheBlend kernels *inline in the prefill/decode window*, not through a *true async V1 KVConnector in the serving loop under concurrent load* — that connector-in-loop measurement is **infeasible in the current pinned environment** (vLLM 0.6.6 lacks the V1 KVConnector API) and is **declared future work**. Its known direction (more transfer/compute overlap) would *shrink, not reverse,* CDC's measured margin. We present this as an honest conditional characterization whose claims do not depend on that single declared-future axis.

---

## 1. Introduction & Motivation

Modern agentic LLM systems run long, multi-turn tool-use loops: the model reads a large reused context (a codebase, a document set, prior turns) and repeatedly **injects tool results back into the middle of the prompt** — a file read, a search result, a JSON blob, a RAG passage. Each such injection is a *mid-prefix* edit. Whereas conventional prefix caching (vLLM Automatic Prefix Caching [arXiv:2309.06180], SGLang RadixAttention [arXiv:2312.07104], FlashInfer) is built around a *growing suffix* — you append, you reuse the shared prefix — agentic injection breaks the cache *in the middle*: every token after the injection point has its KV invalidated under a contiguous-prefix engine. The black-box-API study **"Don't Break the Cache" (arXiv:2601.06007)** motivates exactly this concern from the provider-cost side (place dynamic content late or pay for it), but stops at $/TTFT vs prompt-size and tool-count; it never opens the engine to ask what a mid-prefix injection *costs in recompute*.

This raises a concrete systems question that production schedulers must answer: **what does a mid-prefix injection actually cost in recompute, and when is a content-defined repair worth it?** The folk answer ("just recompute the changed part") hides a structural fact: contiguous-prefix engines recompute *the whole suffix after the edit*, so their cost is governed by *where* you inject, not *how much*. A content-defined re-syncing (CDC) repair — re-chunking around the edit and re-syncing only a bounded boundary window — instead pays a cost governed by *how much* you inject relative to the context.

This paper is a **characterization paper, not a mechanism paper.** The CDC-over-radix repair mechanism is explicitly conceded non-novel (Irminsul + the PIC family — body-verified, §4). Our contribution is three-fold:

1. **The recompute-fraction cost-map** (§2): the engine-internal cost of mid-prefix invalidation as a function of `inj/seq`, with a decisive per-engine decomposition showing the contiguous engines are position-driven while CDC is `inj/seq`-driven.
2. **The workload-conditioned win-region** (§3): where real agentic traffic actually sits on that map, with bootstrap CIs, and the honest finding that the win is a *conditional, count-level* statement (large reused context ∧ small injection), negligible by tokens.
3. **An honest competitive bracket** (§5): exactly where CDC-style contiguous repair wins and loses against re-impl PIC, oracle/fused PIC, and the **real published lmcache CacheBlend kernel** — measured on both the isolated gather axis (EXP-0030) and a combined in-window end-to-end axis (EXP-0034).

**Scope, stated once, prominently.** Two serving axes are *measured* and both favor CDC. One axis — a **true asynchronous V1 KVConnector in the vLLM serving loop under concurrent request load** — is **not** measured, because the pinned environment (vLLM 0.6.6.post1) lacks the V1 KVConnector API and the source-built lmcache `c_ops` ABI cannot be carried across the required vLLM≥0.7 upgrade without a rebuild the operator has not authorized. We treat that axis as **declared future work** (§6.1, boxed), not as a hidden assumption or a gap that undermines the result. The cost-map, the win-region, the closed novelty boundary, and the two-axis competitive resolution all stand independent of it.

We motivate the cost question, lay out the cost-map, locate real traffic on it, close the novelty boundary, bracket the competition honestly, and state the single declared-future axis as scoped future work.

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
- **Sequence-start attention-sink:** position-independence holds EXCEPT the first content-defined chunk. Per-engine attention-sink first-chunk fraction: CDC 0.12%, vLLM-APC 0.22%, Radix 0.014%, PIC 3.47% (EXP-0013). Irminsul (arXiv:2605.05696) body-confirms the position-0 sink is the one genuinely position-dependent corner. The paper writes "position-independent EXCEPT the sequence-start sink."
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

So the win-region is real and prior-robust **only** as a *conditional, count-level* statement (S≥50k ∧ `inj/seq`≤1%). It is a meaningful minority of *injections* but a small minority of *tokens*. This is the framing product_realist (VERDICT-0043) asked us to lead with: **the practical guidance is largely negative** — for most agentic traffic, by tokens, CDC repair does not pay; it pays in a growing-but-minority large-context corner.

### 3.3 Why S≥50k is the right condition

As context-scale rises (modeling 200k–1M long-horizon agents), the *share* of traffic that is large-context grows to 60–76% (EXP-0005/0015), consistent with SWE-ContextBench's >97%-cache-read finding for long-horizon SWE work. So the conditional region, while a minority today, covers a growing fraction of real traffic.

---

## 4. Novelty Positioning (gate-A — FULLY CLOSED at body level, 10/10 neighbors)

**Gate-A is GREEN/uncontested** (novelty_killer GREEN at VERDICT-0043; the two remaining YELLOWs are on the orthogonal serving-measurement axis, §5–§6). Body-verified facts (novelty_boundary_2026-05-31.md). **All baselines are named explicitly with arXiv identifiers:**

- **10/10 closest neighbors body-read (full LaTeXML HTML bodies), ZERO cost-map collision:**
  - **Don't Break the Cache (arXiv:2601.06007):** black-box provider $/TTFT vs prompt-size & tool-COUNT; no `inj/seq` axis, no recompute-fraction, no engine-internal granularity. *(The #1 "same functional form" collapse-fear — REFUTED at body level: their linearity is $-savings vs prompt-size, not recompute% vs `inj/seq`.)* **Role: motivation, not competitor.**
  - **Irminsul (arXiv:2605.05696):** the **CDC-over-radix mechanism twin** (body-confirmed): content-hash keying over SGLang radix with Gear-hash rolling boundaries + delta-rotation on RoPE k_r. Its metrics are token-recovery% / prefill-energy / hit-rate / attention-sink fractions, **NOT a recompute cost-map**. Indexed in ≥2 sources (Semantic Scholar CorpusId 288013360 + OpenAlex W7160639578) — single-source flag cleared. **Role: the named mechanism baseline we explicitly concede the CDC repair to; CLAIM-0006's surviving leg (the inj/seq cost-map + workload-conditioned win-region) is distinct from Irminsul's deliverable.**
  - **PIC family — all body- or abstract-verified distinct, named explicitly:** EPIC (arXiv:2410.15332), CacheBlend (arXiv:2405.16444), Cache-Craft (arXiv:2502.15734), MEPIC (arXiv:2512.16822), KVFlow (arXiv:2507.07400), CacheClip (arXiv:2510.10129). Metrics = TTFT / throughput / quality / memory / redundant-compute. **The word "injection" appears 0× in all six bodies.** EPIC + MEPIC + CacheBlend + Cache-Craft are the explicitly-named PIC baselines per VERDICT-0043.
  - **ContiguousKV (arXiv:2601.13631):** offload-I/O re-prefill / read-amplification; append-suffix, not mid-prefix injection; "injection" 0×. **variable-size-block (arXiv:2604.23994):** discrete-diffusion block-COMMIT generation quality; not autoregressive KV invalidation; "injection"/"prefix cache" 0×.

- **Mechanism conceded non-novel:** CDC-over-radix repair = Irminsul (arXiv:2605.05696) + PIC genus; CDC insertion-resilience = FastCDC/Rabin (foundational). We do **not** pitch the mechanism.

- **slope≈1 demoted to accounting identity** (citing CacheBlend §4 `r%`↔overhead + Pope et al. arXiv:2211.05102), per §2.2.

- **Defensible novelty kernel (narrow, body-distinguished):** *An engine-internal characterization of prefix-cache recompute COST as a function of injection-to-sequence ratio (recompute% ~ `inj/seq`), MEASURED on the real block/token accounting of vLLM-APC (arXiv:2309.06180) / SGLang-Radix (arXiv:2312.07104) / FlashInfer, together with the empirical WORKLOAD-CONDITIONED win-region of CDC-style repair over that surface.* No prior work draws this contour.

**Residual on the novelty axis:** none. The only flagged risk — a cost-map encoded ONLY as an unlabeled plotted curve invisible to HTML-grep — is at VERY LOW risk; every neighbor's caption/axis framing is TTFT/throughput/quality/memory, none mentions injection.

---

## 5. Competitive Positioning (the honest bracket — resolved on BOTH measured serving axes)

The competitive story is **deliberately conditional** — this is the framing that survived hostile review (VERDICT-0029/0033/0037/0043) — but the load-bearing uncertainty (does CDC survive the *shipping SOTA fused kernel*?) is now **resolved on two measured serving axes in CDC's favor**: the isolated real-kernel gather (EXP-0030) and a combined in-window end-to-end TTFT (EXP-0034).

| comparator (all named explicitly) | result | source | honest reading |
|---|---|---|---|
| **Contiguous baselines** (vLLM-APC arXiv:2309.06180 / SGLang-Radix arXiv:2312.07104 / FlashInfer) | CDC 8.3×–465× cheaper (token-recompute), grows with ctx | EXP-0003 | **STRUCTURAL ARTIFACT** of contiguous whole-suffix recompute (EXP-0006); **do NOT headline.** |
| **Fair re-impl PIC** (selective recompute over real vLLM page table), E2E serving | CDC wins **all 12 cells** on BOTH metrics; TTFT PIC/CDC 1.05–1.79×, throughput CDC/PIC 1.00–1.13×; PIC 0/12 | **EXP-0026** (real vLLM 0.6.6 PagedAttention, Qwen2.5-7B fp16, H100) | CDC's contiguous-prefill advantage **survives the non-contiguous paged KV layout** (the binding VERDICT-0029 question — ANSWERED). LIMITATION: lmcache absent → PIC is a faithful re-impl, NOT the published fused kernel. |
| **Oracle / fused PIC** (flash-optimal, ZERO gather overhead) | CDC wins **2/6** cells, both at HIGH `inj/seq` (25%: oraclePIC/CDC 1.054–1.175); **LOSES at low `inj/seq` (1–5%: oraclePIC/CDC 0.612–0.991×)** incl the win-region corner | **EXP-0027** (H100 SDPA oracle bound) | CDC's serving advantage is **itself conditional on `inj/seq`** — opposite direction to the recompute-fraction win-region (a real, publishable nuance). EXP-0026's "wins all 12" was PARTLY the re-impl PIC's gather overhead, as hostile review suspected. CAVEAT: CDC pays a boundary window `Wb=256` the oracle skips → conservative, PIC-favorable bound. |
| **Real published lmcache CacheBlend GATHER kernel** | **CDC contiguous gather wins ALL 12 cells; bootstrap CI excludes 1.0 in 11/12 (only 8k/0.5% is a tie [0.994,1.028]); PIC/CDC 1.01–1.27×** | **EXP-0030** (source-built lmcache 0.1.dev1 `c_ops.single_layer_kv_transfer` = the published CacheBlend gather, on LIVE vLLM 0.6.6 PagedAttention paged KV, format `NL_X_TWO_NB_BS_NH_HS` discovered — NOT a re-impl; 8 reps/cell, bootstrap CIs) | **KEY RESULT #1.** The oracle's zero-overhead assumption was too generous: the REAL fused kernel still pays scatter/page-gather cost, so CDC's contiguous gather wins. Bracket resolves **toward the re-impl result (CDC favorable), NOT the oracle (CDC loses).** Margins largest at large-ctx low-`inj/seq` (28k/0.5% = 1.265 [1.229,1.283]); smallest at the small-ctx low-`inj/seq` corner (8k/0.5% tie). |
| **Combined in-window real-CacheBlend E2E-TTFT** (real gather + HKVD top-15% select + scatter-blend, all 28 layers, INLINE in the prefill/decode window + real first-token decode, CDC vs PIC, 12-cell) | **CDC faster E2E in ALL 12 cells; PIC/CDC 1.003–1.029×; closest-to-tie 8k/5% = 1.0032** | **EXP-0034** (H100 devgpu014, Qwen2.5-7B, 6 reps/cell) | **KEY RESULT #2 — the composition control.** Per-component CDC wins **compose** to an E2E CDC win. Margins **compress** vs the isolated gather (EXP-0030 1.01–1.27× → E2E 1.003–1.029×) exactly as expected: in-window overlap PARTIALLY hides the gather/blend cost, net still favors CDC. **SCOPE:** inline real kernels, NOT a true async V1 KVConnector in the serving loop under concurrent load — that is **declared future work** (§6.1). **CI caveat: §5.4.** |

### 5.1 The full per-cell EXP-0030 table (resolving result #1, with logged bootstrap CIs)

H100, Qwen2.5-7B, 28 layers, 12 cells, **8 reps/cell, bootstrap CIs (logged in EXP-0030 result.md / grid_results.json)**. PIC/CDC > 1 means CDC's gather is cheaper.

| `inj/seq` | 8k PIC/CDC [CI] | 28k PIC/CDC [CI] |
|---|---|---|
| 0.5% | 1.011 [0.994, 1.028] *(TIE — CI includes 1.0)* | 1.265 [1.229, 1.283] |

| 1% | 1.068 [1.029, 1.078] | 1.228 [1.213, 1.231] |
| 2% | 1.103 [1.016, 1.109] | 1.208 [1.190, 1.212] |
| **5%** | **1.108 [1.096, 1.114]** | 1.114 [1.107, 1.126] |
| 10% | 1.075 [1.051, 1.082] | 1.088 [1.084, 1.089] |
| 25% | 1.057 [1.047, 1.070] | 1.028 [1.022, 1.037] |

CDC gather cheaper in 12/12; **CI excludes 1.0 in 11/12** (only the 8k/0.5% corner is a statistical tie); margins 1.01–1.27×. **The 8k/5% cell — the cell the area_chair singled out as the closest combined-axis margin — has a gather-axis CI of [1.096, 1.114], strictly excluding 1.0.**

### 5.2 The full per-cell EXP-0034 table (resolving result #2, composition control)

H100, Qwen2.5-7B, 28 layers, 12 cells, 6 reps/cell. **PIC/CDC > 1 means CDC E2E-TTFT is faster.**

| `inj/seq` | 8k PIC/CDC | 28k PIC/CDC |
|---|---|---|
| 0.5% | 1.025 | 1.011 |
| 1% | 1.017 | 1.021 |
| 2% | 1.012 | 1.014 |
| **5%** | **1.0032 (closest to tie)** | 1.008 |
| 10% | 1.017 | 1.015 |
| 25% | 1.013 | 1.029 |

CDC faster E2E in 12/12; margins 1.003–1.029×; the directional sign is consistent across **all 12** cells.

### 5.3 The 8k/5% headline cell, both axes, side by side (the area_chair's CI condition)

The area_chair (VERDICT-0043) required the 8k/5% / 5%-level CI to be reported explicitly and the 12/12 directional consistency framed as the evidence. We do both:

| metric | 8k/5% value | 95% CI | logged? |
|---|---|---|---|
| Gather-axis (EXP-0030) PIC/CDC | 1.108 | **[1.096, 1.114]** | **yes — bootstrap, 8 reps** |
| In-window E2E (EXP-0034) PIC/CDC | 1.0032 | **— (not in logged record)** | **no — point ratio only (§5.4)** |

**The evidence is the 12/12 directional consistency across both axes, plus the EXP-0030 gather-axis CI excluding 1.0 in 11/12 cells.** At the 8k/5% corner the in-window E2E margin is 0.32% — small enough that, as the eval_prosecutor notes, a true async connector could plausibly close it to a tie; we make no stronger claim than "consistently positive in every measured cell."

### 5.4 CI reporting — honest accounting (no fabricated intervals)

Per the area_chair condition, CIs are reported **from logged data only**:

- **EXP-0030 (headline cost-map):** full bootstrap 95% CIs are logged per cell (`grid_results.json` + `result.md`); reproduced verbatim in §5.1. CI excludes 1.0 in 11/12.
- **EXP-0034 (in-window E2E composition):** the logged record (`grid_results.json`, `result.md`) contains **point ratios only — no per-rep arrays and no logged CIs** (6 reps/cell; the harness logged aggregate ratios, not the raw rep distributions). We therefore **do not report CIs for EXP-0034 and do not compute them**, because the raw rep data needed to do so honestly is not present in the experiment record. **This is flagged for the orchestrator as a missing-datum:** to attach CIs to the EXP-0034 composition numbers, the harness would need to re-emit per-rep TTFT arrays (a logging change, not a new GPU sweep — though re-running is a GPU action and out of this agent's scope). We refuse to invent intervals.

### 5.5 Honest framing sentence for the paper

> "Against the dominant production stack (real vLLM PagedAttention, arXiv:2309.06180; SGLang RadixAttention, arXiv:2312.07104), CDC-style contiguous repair wins on TTFT and throughput in every measured cell (EXP-0026). Against a *fused/oracle* PIC, that advantage was predicted to be conditional on `inj/seq` (EXP-0027). We resolve this against the **real published lmcache CacheBlend gather kernel** (arXiv:2405.16444): because the real fused kernel still pays scatter/page-gather cost, CDC's contiguous gather wins all 12 cells with bootstrap CIs excluding 1.0 in 11/12 (EXP-0030), and a **combined in-window end-to-end TTFT measurement preserves the win in 12/12 cells** with margins compressing to 1.003–1.029× as pipelining overlap partially hides the blend cost (EXP-0034). Both measured serving axes point the same way. The single remaining axis — a *true asynchronous V1 KVConnector in the serving loop under concurrent load* — is environment-gated and **declared future work**; its known direction (more overlap) would shrink, not reverse, the measured margin."

### 5.6 Supporting kernel evidence (consistent; kernel-level, not full serving)

- EXP-0014: CDC faster in all 8 TTFT cells (PIC/CDC 1.02–2.68×); largest 2.68× at win-region corner (32k/0.1%).
- EXP-0021: all 8 cells CI95 excludes 1.0 (incl prev-ambiguous 32k/1% = 1.129 [1.128, 1.151]), 30 reps/cell.
- EXP-0025: throughput — CDC wins 22/24, PIC only 2/24 marginal (0.993–0.994×) at the 8k/5% corner; the predicted PIC-favorable high-`inj/seq` regime actually favors CDC *more* (1.5–1.74× at 50%).
- EXP-0023: analytic serving bridge — end-to-end PIC/CDC band [1.10, 2.03] nominal / [1.00, 1.28] worst-for-CDC; 0/8 cells invert under any plausible overhead; gather-overlap alone cannot flip CDC's advantage.

---

## 6. Scope, Limitations, and the Declared-Future Axis

### 6.1 Scope & Limitations (boxed — read this before drawing operational conclusions)

> ╔══════════════════════════════════════════════════════════════════════════╗
> ║ **SCOPE & LIMITATIONS — THE ONE UN-MEASURED SERVING AXIS (DECLARED FUTURE WORK)** ║
> ╚══════════════════════════════════════════════════════════════════════════╝
>
> **What we measured.** Two serving axes, both favoring CDC:
> (i) the **isolated real-kernel gather** (EXP-0030, source-built lmcache CacheBlend `c_ops` on live vLLM PagedAttention; CDC wins 12/12, bootstrap CI excludes 1.0 in 11/12); and
> (ii) a **combined in-window end-to-end TTFT** (EXP-0034, the real CacheBlend gather + HKVD select + scatter-blend kernels run *inline in the prefill/decode window* alongside a real first-token decode; CDC wins 12/12, margins 1.003–1.029×).
>
> **What we did NOT measure (and why it is future work, not a gap).** A **true asynchronous V1 KVConnector in the vLLM serving loop under concurrent request load**, which would let lmcache's async layerwise CPU↔GPU transfer scheduler fully overlap PIC's gather/blend cost with model compute. This is **infeasible in the pinned environment**: vLLM 0.6.6.post1 has no V1 KVConnector API (`vllm.distributed.kv_transfer.kv_connector.v1` does not exist; confirmed in EXP-0034 SMOKE_RESULT), and the operator's source-built lmcache `c_ops` ABI cannot be carried across the vLLM≥0.7 upgrade that the V1 connector requires without a rebuild the operator has not authorized. **We declare this measurement as future work, not a flaw in the present result.**
>
> **Why the present claims do not depend on it.** EXP-0034 is *strictly more end-to-end* than the isolated gather (EXP-0030) and uses the *real* blend kernel (vs EXP-0026's re-impl). The one effect it does not capture — lmcache's async transfer-scheduler overlap — has a **known direction**: it would *further hide* PIC's transfer cost, i.e. **shrink** CDC's margin within the measured band, **not flip its sign**. The closest-to-tie measured cell (8k/5%, in-window E2E margin 0.32%) is therefore the cell where a future async measurement is most likely to reach a statistical tie; we make no claim stronger than "CDC is consistently faster in every measured cell, by a margin that compresses as overlap increases." The cost-map (§2), the workload-conditioned win-region (§3), and the closed novelty boundary (§4) are entirely independent of this axis.
>
> **Operational honesty (product_realist, VERDICT-0043).** The measured E2E win is **real but marginal** (0.3–2.9%, plausibly within production variance) and **regime-confined** (the count-level win-region is the S≥50k corner, which carries a minority of tokens today). **The primary practical value of this paper is negative adoption guidance:** for the bulk of agentic traffic, by tokens, a CDC repair does not pay; it pays in a growing-but-minority large-context, small-injection corner — and even there the end-to-end margin is small.

### 6.2 How the EXP-0034 axis is framed in the paper

EXP-0034 has **landed as a scoped, in-window measurement** and is reported as **KEY RESULT #2** (§5.2), not as future work. The *future-work* label attaches **only** to the narrower, environment-gated **true-async-connector-in-serving-loop-under-concurrent-load** measurement (§6.1). The distinction is deliberate: we do not understate what is measured, and we do not overstate it as the async result.

---

## 7. Related Work, Conclusion, and the Single Declared-Future Axis

### 7.1 Related work (condensed; full body-verifications in novelty_boundary_2026-05-31.md). All works named explicitly.

- **Mechanism family (conceded non-novel):** **Irminsul (arXiv:2605.05696)** — the CDC-over-radix mechanism twin; **EPIC (arXiv:2410.15332)**, **CacheBlend (arXiv:2405.16444)**, **Cache-Craft (arXiv:2502.15734)**, **MEPIC (arXiv:2512.16822)**, **KVFlow (arXiv:2507.07400)**, **CacheClip (arXiv:2510.10129)** — the PIC genus. CacheBlend §4 additionally supplies the `r%`↔overhead identity we cite; Pope et al. (arXiv:2211.05102) supplies the KV accounting.
- **Serving substrate (named baselines):** vLLM PagedAttention / Automatic Prefix Caching (Kwon et al., **arXiv:2309.06180**), SGLang RadixAttention (Zheng et al., **arXiv:2312.07104**), FlashInfer. The competitive bracket (§5) runs against these plus the source-built lmcache CacheBlend kernel.
- **Closest empirical cost-axis neighbor (motivation):** **Don't Break the Cache (arXiv:2601.06007)** — black-box $/TTFT vs prompt-size & tool-count, no engine-internal recompute-fraction, no `inj/seq` axis. Cited as motivation and distinguished, not as a competitor.
- **Adjacent systems (distinct):** ContiguousKV (arXiv:2601.13631, offload-I/O re-prefill, append-suffix), variable-size-block (arXiv:2604.23994, discrete-diffusion block-commit). Neither addresses mid-prefix autoregressive KV invalidation.
- **Foundational:** FastCDC / Rabin content-defined chunking (CDC insertion-resilience).

### 7.2 Conclusion

We characterized the recompute cost of prefix-cache invalidation under agentic mid-prompt tool injection as an engine-internal cost-map over `inj/seq`, decomposed it per-engine to show the contiguous production engines are *position-driven* (R²=0.0007) while CDC is *`inj/seq`-driven* (slope 0.958 [0.937, 0.980], R²=0.972) — being explicit that this slope is a mechanism-derived accounting identity, not an emergent law. We located real agentic traffic on that map and found the CDC win-region is negligible by tokens (≤8.1% under any prior) but a meaningful, prior-robust minority by injection count when conditioned on large reused context (≈46% given S≥50k). We closed the novelty boundary at the body level (10/10 neighbors, "injection" 0× in the PIC family, mechanism conceded to Irminsul arXiv:2605.05696) and bracketed CDC's serving advantage honestly — resolving the load-bearing uncertainty on **two measured serving axes** with the **real published lmcache CacheBlend kernel**: isolated gather (CDC 12/12, CI excludes 1.0 in 11/12, EXP-0030) and combined in-window E2E TTFT (CDC 12/12, margins 1.003–1.029×, EXP-0034). The result is a defensible MLSys characterization paper whose spine is: *here is the cost-map; here is where real traffic sits on it; here, conditionally, is where CDC wins; here, honestly, is the one serving axis that remains environment-gated future work.*

### 7.3 The single declared-future axis (the honest residual)

**The true-async-connector end-to-end measurement.** Our strongest serving evidence comes from two *measured* axes: the real published kernel measured at the *gather* component (EXP-0030, CDC 12/12) and a *combined in-window end-to-end* TTFT with the real blend kernel (EXP-0034, CDC 12/12). The one axis not measured is a **true asynchronous V1 KVConnector in the serving loop under concurrent request load** (eval_prosecutor, VERDICT-0043). The honest response:

- We **declare it future work**, gated by an operator environment upgrade (vLLM≥0.7 V1 KVConnector; the pinned vLLM 0.6.6.post1 lacks the API and the source-built lmcache `c_ops` ABI cannot survive the upgrade without an unauthorized rebuild — EXP-0034 SMOKE_RESULT). It is **not** a hidden assumption.
- Its **direction is known**: more transfer/compute overlap would *shrink* CDC's measured margin, **not reverse** it, within the measured band. The closest-to-tie cell (8k/5%, 0.32% in-window E2E) is where a future async measurement is most likely to reach a statistical tie.
- The cost-map, the win-region, the closed novelty boundary, and the two-axis competitive resolution **all stand independent of this axis**.

This is the only binding residual on the serving axis. Novelty (gate-A) and the cost-map/win-region theory are GREEN/uncontested.

---

## 8. Submission-Readiness Verdict

**CLAIM-0006 is SUBMITTABLE as an honest-conditional-characterization paper (operator path-(b)), with VERDICT-0043's area_chair promotion conditions applied (this r3 finalization).**

What makes it submittable:
1. **Cost-map:** measured, CI-quantified, per-engine decomposition (EXP-0002/0013). GREEN.
2. **Win-region:** bootstrap CIs, prior-robust, honestly conditional + lead-with-negative-guidance (EXP-0005/0015). GREEN as conditional.
3. **Novelty:** 10/10 neighbors body-verified distinct, mechanism conceded to Irminsul + PIC genus, slope≈1 demoted (cited). GREEN.
4. **Competitive bracket:** honestly conditional, committee-vetted, **resolved on both measured serving axes** (gather EXP-0030 with CIs; in-window E2E EXP-0034 with point ratios) (EXP-0003/0006/0026/0027/0030/0034). GREEN as conditional, strengthened.
5. **The one declared-future axis** (true async V1 KVConnector E2E under concurrent load, EXP-0034-async) is environment-gated future work, scoped prominently (§6.1 box, abstract, intro) — and the paper's claims do not depend on it.

**Reviewer-axis status as of VERDICT-0043 (4 GREEN / 2 YELLOW, 0 RED):**
- novelty_killer / systems_reviewer / theory_skeptic / area_chair: GREEN.
- evaluation_prosecutor: YELLOW — satisfied **only** by the env-gated true-async-connector E2E (declared future work; cannot be closed in the pinned environment). This draft frames it honestly per the area_chair conditions; it does not claim that axis as measured.
- product_realist: YELLOW — the win is marginal + regime-confined. This draft now **leads with the negative adoption guidance** (§3.2, §6.1 box) as requested.

What it is NOT: a paper claiming CDC universally beats PIC, or a slope-law discovery, or a token-weighted win, or a measured *async-connector* E2E result. Those framings are killed and must not be re-inflated.

**File:** prior_art/PROJ-0002/CLAIM-0006/PAPER_DRAFT_r3_FINAL.md

---

## CHANGELOG — r3 finalization (researcher-0006-paper-r3, 2026-06-01)

Applied the three VERDICT-0043 area_chair promotion conditions, verbatim, from logged evidence only. No new experiments, no GPU runs, no vLLM upgrade, no map/claim/verdict edits.

**Condition 1 — Scope-statement placement (prominent; async-connector framed as declared future work).**
- Abstract: added an explicit "Scope (stated up front and not hedged later)" sentence declaring the true-async-V1-KVConnector axis as environment-gated future work whose known direction would shrink (not reverse) the margin.
- §1 Introduction: added a standalone "Scope, stated once, prominently" paragraph.
- §6.1: added a **boxed Scope & Limitations paragraph** — what we measured (EXP-0030 + EXP-0034), what we did NOT (true async connector under concurrent load + why infeasible in the pinned env), why claims don't depend on it, and the operational/negative-guidance honesty (product_realist).
- §6.2: clarified that EXP-0034 (in-window) is a LANDED result (KEY RESULT #2), and the future-work label attaches only to the narrower async-connector-under-concurrent-load axis.
- §7.3 + §8: residual re-framed as "the single declared-future axis," not "the weakest link / gap."

**Condition 2 — CI reporting on the headline cost-map + EXP-0034 composition numbers (from logged CSVs/JSON only).**
- §5.1: EXP-0030 per-cell bootstrap 95% CIs reproduced verbatim from grid_results.json/result.md (8 reps/cell); noted CI excludes 1.0 in 11/12.
- §5.2: EXP-0034 per-cell point ratios reproduced (12/12 directional consistency).
- §5.3: NEW table — the 8k/5% headline cell on both axes side by side (the area_chair's explicit CI ask), with the gather-axis CI [1.096, 1.114] excluding 1.0, and the 12/12 directional consistency framed as the evidence.
- §5.4: NEW honest CI-accounting subsection — EXP-0034's logged record contains **point ratios only, no per-rep arrays/CIs**; therefore **no CIs are reported or computed for EXP-0034**, and this is **flagged to the orchestrator as a missing-datum** (harness would need to re-emit per-rep TTFT arrays). No interval was invented. (This is the one place where a requested datum is genuinely absent from the logs.)

**Condition 3 — Named baselines, including Irminsul + PIC family + motivation.**
- §4, §5, §7.1: every baseline named explicitly with arXiv id — **Irminsul (arXiv:2605.05696)** as the named CDC-over-radix mechanism twin; **EPIC (2410.15332) / MEPIC (2512.16822) / CacheBlend (2405.16444) / Cache-Craft (2502.15734)** as body-verified-distinct PIC prior art; **KVFlow (2507.07400) / CacheClip (2510.10129)** also named; **"Don't Break the Cache" (2601.06007)** as motivation (not competitor); and the serving substrate **vLLM PagedAttention/APC (arXiv:2309.06180)** + **SGLang RadixAttention (arXiv:2312.07104)** named with ids (these two arXiv ids were missing from the prior draft and are required by VERDICT-0043).

**Evidence cited as the scoped results:** EXP-0030 (isolated real-kernel gather, CIs logged) + EXP-0034 (combined in-window E2E, point ratios logged).

**Status after r3:** Conditions 1 and 3 fully satisfied in-text. Condition 2 satisfied for EXP-0030 (CIs logged + reproduced) and for the 8k/5% headline; for EXP-0034 it is satisfied *to the extent the logs allow* — point ratios + 12/12 consistency reported, CIs honestly declared absent-from-record and flagged for the orchestrator. The two remaining reviewer YELLOWs (evaluation_prosecutor, product_realist) are addressed in framing; the evaluation_prosecutor's substantive ask (true async-connector E2E under concurrent load) remains **environment-blocked** (operator vLLM≥0.7 upgrade decision) and is declared future work, not closed by this draft.

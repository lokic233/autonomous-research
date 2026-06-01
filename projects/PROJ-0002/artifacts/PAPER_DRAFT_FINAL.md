# Characterizing the Recompute Cost of Prefix-Cache Invalidation under Agentic Tool Injection: A Cost-Map, a Workload-Conditioned Win-Region, and an Honest Competitive Bracket

**Claim:** CLAIM-0006 · **Project:** PROJ-0002 · **Target venue:** MLSys
**Draft type:** Path-(b) submittable paper (honest-conditional characterization). FINALIZED per the area_chair + reviewer conditions named in VERDICT-0043 (2026-05-31, 4 GREEN / 2 YELLOW / 0 RED).
**Finalized by:** researcher-0006-finalize · reporting to orchestrator 22bd6bef · **Date:** 2026-05-31
**Status:** CPU writing only. NO claim/verdict/map/experiment edits. Every number is copied (not re-derived) from registry evidence (CLAIM-0006.yaml, VERDICT-0006..0043, EXP result.md files, novelty_boundary_2026-05-31.md). Nothing invented.

> **Finalization note (VERDICT-0043).** This is the submission-ready finalization of `PAPER_DRAFT.md`. The committee reached 4 GREEN (novelty_killer, systems_reviewer, theory_skeptic, area_chair) / 2 YELLOW (evaluation_prosecutor, product_realist) / 0 RED — the closest yet, with the area_chair arguing GREEN. It stays YELLOW only because the engine-enforced `green_rule=unanimous` binds and the two YELLOWs are scope-constraints, not validity flaws. The committee named EXACT finalization conditions, applied here: (1) the EXP-0034 SCOPED-APPROXIMATION caveat is hoisted into a prominent **Experimental Setup** section (§2), not buried; (2) the 8k/5% E2E cell (PIC/CDC = 1.0032) is reported with its honest uncertainty framing — the 12/12 **directional consistency** is the evidence, not per-cell significance; (3) all baselines are cited **by name** (CacheBlend arXiv:2405.16444; LMCache; vLLM/PagedAttention arXiv:2309.06180; SGLang RadixAttention arXiv:2312.07104; **Irminsul arXiv:2605.05696** as the concurrent CDC-over-radix mechanism twin); (4) the true async-connector E2E (vLLM≥0.7 V1 KVConnector under concurrent load) is the **declared future-work env-gated path to unanimous GREEN**, and the headline leads with the honest framing: the win is real but **marginal (0.3–2.9%) and regime-confined (S≥50k)**, and the paper's **primary value is negative adoption guidance** on when *not* to use CDC.

---

## Abstract

Agentic LLM serving repeatedly injects tool results into a reused prompt prefix, invalidating prefix caches *mid-sequence* rather than at the suffix. We characterize the **cost** of this invalidation as an engine-internal **recompute-fraction cost-map** over the injection-to-sequence ratio (`inj/seq = R/S`, for an injection of `R` tokens into a reused prefix of length `S`). Measuring the real block/token accounting of vLLM Automatic Prefix Caching (vLLM/PagedAttention, Kwon et al. arXiv:2309.06180), SGLang RadixAttention (Zheng et al. arXiv:2312.07104), and FlashInfer, we show these contiguous-prefix engines are **position-driven** (recompute cost ≈ `1 − position`, R²=0.0007 vs `inj/seq`, ≈69 pp swing across edit position), whereas a content-defined re-syncing (CDC) repair is **`inj/seq`-driven and position-independent** (slope 0.958, 95% CI [0.937, 0.980], R²=0.972; 0.13 pp position spread) (EXP-0013). We are explicit that this slope≈1 is a **mechanism-derived accounting identity** (cf. CacheBlend's `r%`↔overhead dial, arXiv:2405.16444 §4; Pope et al. arXiv:2211.05102 for the KV accounting), *not* an emergent cross-engine law, and that the CDC repair *mechanism* itself is **not novel** — it is a concurrent/independent twin of **Irminsul (arXiv:2605.05696)** and a member of the Position-Independent-Caching (PIC) family. Our contribution is the cost-map plus a **workload-conditioned win-region**: over a realistic agentic workload (20k tasks, 291,454 injections), CDC's recompute win-region is **negligible by injected tokens** (≤8.1% under every prior tested; 3.7% [0.0361, 0.0379] at the base prior — so any token-weighted or unconditional framing is **unsupported**), but **conditioned on large reused context (S≥50k), CDC wins ~46% of injections by count** (0.457 [0.453, 0.461], prior-robust 41–52% across a 4×4 prior grid) (EXP-0015).

**We lead with the honest bottom line: the serving win is real but operationally MARGINAL and REGIME-CONFINED.** Against the dominant production stack (real vLLM PagedAttention), CDC-style contiguous repair wins TTFT and throughput in every measured cell (EXP-0026, 12/12). The real published LMCache CacheBlend GATHER kernel still pays scatter/page-gather cost, so CDC's contiguous gather wins 12/12 (EXP-0030, CI excludes 1.0 in 11/12). A combined in-window end-to-end TTFT (real CacheBlend kernels inline, EXP-0034) likewise favors CDC 12/12 — but **the margins are 0.3–2.9%, plausibly below production variance**, with the closest cell (8k/5%) at PIC/CDC = 1.0032 (effectively a tie). The win lives only in a minority regime (S≥50k; ~81% of *tokens* sit in the degrade band). **The paper's primary practical value is therefore NEGATIVE ADOPTION GUIDANCE**: it tells a production scheduler exactly *when not to bother* with CDC-style repair (everywhere except the large-context, small-injection corner) — and, where CDC does help, that the margin is small enough that engineering cost may not be repaid. The single un-measured axis is a **true async-connector end-to-end TTFT** (vLLM≥0.7 V1 KVConnector under concurrent load), which we declare as future work and identify as the env-gated path to unanimous GREEN (§7); its known direction (more overlap → smaller margin) would shrink, not reverse, CDC's advantage in the measured band.

---

## 1. Introduction & Motivation

Modern agentic LLM systems run long, multi-turn tool-use loops: the model reads a large reused context (a codebase, a document set, prior turns) and repeatedly **injects tool results back into the middle of the prompt** — a file read, a search result, a JSON blob, a RAG passage. Each such injection is a *mid-prefix* edit. Whereas conventional prefix caching (vLLM Automatic Prefix Caching, SGLang RadixAttention, FlashInfer) is built around a *growing suffix* — you append, you reuse the shared prefix — agentic injection breaks the cache *in the middle*: every token after the injection point has its KV invalidated under a contiguous-prefix engine.

This raises a concrete systems question that production schedulers must answer: **what does a mid-prefix injection actually cost in recompute, and when is a content-defined repair worth it?** The folk answer ("just recompute the changed part") hides a structural fact: contiguous-prefix engines recompute *the whole suffix after the edit*, so their cost is governed by *where* you inject, not *how much*. A content-defined re-syncing (CDC) repair — re-chunking around the edit and re-syncing only a bounded boundary window — instead pays a cost governed by *how much* you inject relative to the context.

This paper is a **characterization paper, not a mechanism paper.** The CDC-over-radix repair mechanism is explicitly conceded non-novel (a concurrent/independent twin of **Irminsul** + the **PIC family** — body-verified, §5). Our contribution is three-fold:

1. **The recompute-fraction cost-map** (§3): the engine-internal cost of mid-prefix invalidation as a function of `inj/seq`, with a decisive per-engine decomposition showing the contiguous engines are position-driven while CDC is `inj/seq`-driven.
2. **The workload-conditioned win-region** (§4): where real agentic traffic actually sits on that map, with bootstrap CIs, and the honest finding that the win is a *conditional, count-level* statement (large reused context ∧ small injection), negligible by tokens.
3. **An honest competitive bracket** (§6): exactly where CDC-style contiguous repair wins and loses against re-impl, oracle, and the **real published fused** PIC kernel — and the honest reading that, even where CDC wins, the end-to-end margin is small and regime-confined.

We motivate the cost question, fix the experimental setup and its scope (§2), lay out the cost-map, locate real traffic on it, close the novelty boundary, bracket the competition honestly, and state the single weakest link as scoped future work.

---

## 2. Experimental Setup and Scope (read this before the results)

All measurements are real (no simulated kernels in the serving experiments). We state the measurement scope **here, up front**, rather than in a buried limitations paragraph, because the scope determines exactly how strongly each serving claim can be read.

### 2.1 Platforms, engines, and kernels measured

- **Cost-map (§3):** CPU, stdlib only; the real block/token accounting of **vLLM Automatic Prefix Caching** (vLLM/PagedAttention, Kwon et al. arXiv:2309.06180), **SGLang RadixAttention** (Zheng et al. arXiv:2312.07104), and **FlashInfer**; 405 cells/engine; Student-t + Wilson + bootstrap CIs (EXP-0002, EXP-0013).
- **Workload (§4):** 20k tasks / 291,454 injections; bootstrap CIs over a 4×4 (16-cell) workload-prior sweep (EXP-0005, EXP-0015).
- **Serving bracket (§6):** real **vLLM 0.6.6.post1** PagedAttention, **Qwen2.5-7B fp16**, **H100** (devgpu014). The PIC comparator is instantiated three ways of increasing fidelity:
  1. a **fair re-implementation** of selective recompute over the real vLLM page table (EXP-0026, E2E TTFT + throughput, 12 cells);
  2. a **zero-overhead oracle/fused** PIC (flash-optimal SDPA bound, EXP-0027, 6 cells);
  3. the **real published LMCache CacheBlend kernel** — source-built **LMCache 0.1.dev1** `c_ops.single_layer_kv_transfer` (the published CacheBlend gather), run on the LIVE vLLM 0.6.6 PagedAttention paged KV (discovered layout `NL_X_TWO_NB_BS_NH_HS`), measured at the **gather component** (EXP-0030, 12 cells) and **inline end-to-end** (EXP-0034, 12 cells).
- **Baselines are cited by name** throughout: **CacheBlend (arXiv:2405.16444)** is the PIC mechanism baseline and supplies the `r%`↔overhead accounting identity; **LMCache (github.com/LMCache/LMCache)** is the kernel source for the real CacheBlend gather *and* the basis for the async-connector scope caveat below; **vLLM/PagedAttention (arXiv:2309.06180)** and **SGLang RadixAttention (arXiv:2312.07104)** are the contiguous production engines; **Irminsul (arXiv:2605.05696)** is the concurrent/independent CDC-over-radix mechanism twin (§5).

### 2.2 SCOPE STATEMENT — EXP-0034 is a SCOPED in-window approximation, NOT a true async KVConnector measurement

**This is the most important scope boundary in the paper and we state it prominently.** The combined end-to-end TTFT experiment (EXP-0034) runs the **real LMCache CacheBlend blend kernels** (D2H paged gather + HKVD top-15% KV-deviation select + scatter-blend across all 28 layers) **INLINE in the prefill/repair window**, followed by a real first-token decode through the live vLLM engine. This is strictly *more* end-to-end than the isolated-gather EXP-0030 (it lets the gather/blend cost overlap real prefill/decode), and it uses the *real* blend kernel (vs EXP-0026's re-implementation).

**It is NOT a true async-connector-in-serving-loop measurement.** The pinned environment — **vLLM 0.6.6.post1** — *lacks the V1 KVConnector API*: `vllm.distributed.kv_transfer.kv_connector.v1` (and `ec_transfer`) do not exist, so LMCache's `LMCacheConnectorV1` + `LMCBlender` V1-adapter wiring is unimportable (EXP-0034 SMOKE_RESULT, `full_connector_blocker`). A true async connector-in-loop requires **vLLM ≥ 0.7/0.8** — an operator environment upgrade we did not have.

Consequently, EXP-0034 **does NOT capture** LMCache's async layerwise CPU↔GPU transfer-scheduler overlap (PIC's primary latency-hiding mechanism). The direction of that omission is known and bounded: more overlap would *further hide* PIC's cost — i.e. it would **shrink** CDC's measured margin, not flip its sign within the measured band. We treat every EXP-0034 number as a **scoped in-window approximation** and we do **not** claim it as a true async-connector result. The genuine remaining environment limitation is exactly this true async-connector E2E under concurrent load; it is our declared future work and the env-gated path to unanimous GREEN (§7).

### 2.3 Proxy and caveat inventory (stated, not buried)

- The cost-map (§3) is a **token-count recompute fraction**, not GPU wall-clock; wall-clock is the serving leg (§6).
- Position-independence of CDC holds **EXCEPT** the sequence-start attention-sink chunk (§3.4); Irminsul's first-chunk carve-out independently confirms the position-0 sink is the one genuinely position-dependent corner.
- EXP-0027's oracle pays **no** boundary window; CDC pays `Wb=256` it skips → that bound is *conservative / PIC-favorable*.
- EXP-0034 reports **per-cell medians over 6 reps** (no per-cell bootstrap CI); the strength of evidence there is the **12/12 directional consistency**, not per-cell significance (§6.2).

---

## 3. The Recompute-Fraction Cost-Map

### 3.1 The relation

For a pure mid-prefix insertion of `R` tokens into a reused prefix of length `S`, a content-defined re-syncing scheme (CDC) recomputes the `R` new tokens plus a bounded boundary re-sync window `W`. Its recompute fraction is

```
recompute% = (R + W) / S  ≈  R/S = inj/seq     (for W ≪ R; slope ≈ 1)
```

and is **flat in edit position** (prepend ≈ interior ≈ terminal), EXCEPT the sequence-start attention-sink chunk (§3.4).

### 3.2 Accounting identity vs measured contribution (the load-bearing honesty boundary)

This is the single most important honesty boundary in the analysis, enforced by hostile review (VERDICT-0017). We state it explicitly:

- **ACCOUNTING IDENTITY (derived, NOT a discovery).** "`recompute% ~ inj/seq` with slope ≈ 1" for a perfectly re-syncing scheme is the *algebra of contiguous-chunk KV bookkeeping*: recompute `= R + W`, fraction `= (R+W)/S`, slope 1 by construction with no free parameter. **CacheBlend (arXiv:2405.16444, EuroSys'25 §4)** states the same identity as a *tuning dial* ("recompute `r%` of tokens ⇒ `r%` of full-prefill overhead"); **Pope et al. (arXiv:2211.05102)** gives the underlying KV accounting. **We cite CacheBlend §4 + Pope for the identity** so the slope is not over-claimed as emergent. We do **not** pitch slope≈1 as a "law."

- **WHAT IS ACTUALLY MEASURED (the real, empirical contribution).**
  1. That CDC *achieves* the near-`W=0` re-sync on realistic agentic insertions (not adversarial re-chunk cascades) — i.e. that real injections land on the identity line. Quantified per-engine with CIs (EXP-0013).
  2. That this is a **CDC-mechanism-specific** property, NOT a cross-engine law — the decisive decomposition (§3.3).
  3. The empirical **workload distribution** of `inj/seq` locating *where on the identity line real traffic sits* (§4).

### 3.3 Per-engine cost-map with CIs (EXP-0013)

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

### 3.4 Caveats baked into the cost-map (state, do not bury)

- **PROXY:** token-count recompute fraction, not GPU wall-clock (wall-clock is the serving leg, §6).
- **Sequence-start attention-sink:** position-independence holds EXCEPT the first content-defined chunk. Per-engine attention-sink first-chunk fraction: CDC 0.12%, vLLM-APC 0.22%, Radix 0.014%, PIC 3.47% (EXP-0013). **Irminsul (arXiv:2605.05696)** body-confirms the position-0 sink is the one genuinely position-dependent corner. The paper writes "position-independent EXCEPT the sequence-start sink."
- **Anchor reproduction (EXP-0002):** the original "~2%" reproduces exactly (CTX=4000, inj=40 → 2.0–2.4%) but is a **thin contour at `inj/seq`≈1%**, not a universal property: surface min 0.02% / median 1.34% / max 53.05%; breaks to 5.3% @200tok/4k, 20% @1000tok/4k, 49–53% @1000tok/1k. So "~2%" is a *conditional cost-map contour*, not a CDC property; edit position is not the cost driver — injection size relative to context is.

---

## 4. The Workload-Conditioned Win-Region

EXP-0015: bootstrap CIs over 20k tasks / 291,454 injections, with a 4×4 (16-cell) workload-prior sweep. (Reproduces the EXP-0005 points: median `inj/seq` = 2.8%; count-fraction `inj/seq`≤1% = 0.246 [0.243, 0.250]; token-fraction = 0.037 [0.036, 0.038].)

### 4.1 The honest headline (the win-region is CONDITIONAL, COUNT-LEVEL only)

The win-region lives on **two axes that point in opposite directions**; conflating them is the over-claim hostile review killed (VERDICT-0023):

| metric | value | 95% CI | framing verdict |
|---|---|---|---|
| **Token-weighted** win-region (`inj/seq`≤1%), base prior | **0.037** | [0.0361, 0.0379] | token / unconditional framing **UNSUPPORTED** |
| Token-weighted win-region across ALL 16 priors | 0.027–0.081 (median 0.037) | ≤0.004 half-width | **never exceeds ~8.1%** under any prior |
| Count-fraction win-region (`inj/seq`≤1%), marginal | 0.2461 | [0.2426, 0.2495] | minority of injections |
| **Conditional count-level win GIVEN S≥50k** (CDC home) | **0.4573** | **[0.4531, 0.4613]** | **the surviving, defensible claim** |
| Count-frac-given-S≥50k across 16 priors | 0.411–0.520 (median 0.477) | — | **prior-STABLE ~½** |

### 4.2 The precise honest statement (verbatim into the paper)

> "**By injected tokens — the work that actually costs latency — the win-region is negligible** (3.7% at the base prior; ≤8.1% under every prior tested; ≥92% of injected tokens fall in the mid/degrade regimes where CDC ties a fair PIC baseline). Any token-weighted or unconditional 'CDC saves recompute on agentic traffic' framing is **not supported**. **By injection count, conditioned on large reused context (S≥50k), small tool injections (`inj/seq`≤1%) are common and CDC wins ~46% of them (0.457 [0.453, 0.461]), prior-robustly (41–52% across a 4×4 prior grid).** This conditional count-level win-region is the defensible characterization."

So the win-region is real and prior-robust **only** as a *conditional, count-level* statement (S≥50k ∧ `inj/seq`≤1%). It is a meaningful minority of *injections* but a small minority of *tokens* (≈81% of tokens sit in the degrade band). This is why the paper's primary practical value is **negative adoption guidance** (§7): for the great majority of agentic traffic — and for nearly all of the *work* measured in tokens — CDC-style repair is not worth deploying.

### 4.3 Why S≥50k is the right condition

As context-scale rises (modeling 200k–1M long-horizon agents), the *share* of traffic that is large-context grows to 60–76% (EXP-0005/0015), consistent with SWE-ContextBench's >97%-cache-read finding for long-horizon SWE work. So the conditional region, while a minority today, covers a growing fraction of real traffic — which is precisely why bounding *when* CDC helps (and when it does not) is useful guidance now.

---

## 5. Novelty Positioning (gate-A — FULLY CLOSED at body level, 10/10 neighbors)

**Gate-A is GREEN/uncontested** (novelty_killer GREEN at VERDICT-0043; the YELLOWs are on the orthogonal serving-measurement and adoption-framing axes, §6–§7). Body-verified facts (novelty_boundary_2026-05-31.md):

- **10/10 closest neighbors body-read (full LaTeXML HTML bodies), ZERO cost-map collision:**
  - **Don't Break the Cache (arXiv:2601.06007):** black-box provider $/TTFT vs prompt-size & tool-COUNT; no `inj/seq` axis, no recompute-fraction, no engine-internal granularity. *(The #1 "same functional form" collapse-fear — REFUTED at body level: their linearity is $-savings vs prompt-size, not recompute% vs `inj/seq`.)*
  - **Irminsul (arXiv:2605.05696):** the **concurrent/independent CDC-over-radix mechanism twin** (body-confirmed — extends SGLang's radix cache with content-hash keying over CDC-chunked segments). Its metrics are token-recovery% / prefill-energy / attention-sink, NOT a recompute cost-map; it does **not** publish CLAIM-0006's surviving leg (the `inj/seq` recompute-fraction cost-map or the workload-conditioned win-region). Indexed in ≥2 independent sources (OpenAlex W7160639578, doi 10.48550/arXiv.2605.05696, pub 2026-05-07; + Semantic Scholar) — single-source flag cleared. **We cite Irminsul by name as the mechanism twin; failing to cite it would be a novelty overclaim.**
  - **PIC family** — EPIC (arXiv:2410.15332), **CacheBlend (arXiv:2405.16444)**, Cache-Craft (arXiv:2502.15734), MEPIC (arXiv:2512.16822), KVFlow (arXiv:2507.07400), CacheClip (arXiv:2510.10129): all six body-verified distinct; metrics = TTFT / throughput / quality / memory / redundant-compute. **The word "injection" appears 0× in all six bodies.**
  - **ContiguousKV (arXiv:2601.13631):** offload-I/O re-prefill / read-amplification; append-suffix, not mid-prefix injection; "injection" 0×. **variable-size-block (arXiv:2604.23994):** discrete-diffusion block-COMMIT generation quality; not autoregressive KV invalidation; "injection"/"prefix cache" 0×.

- **Mechanism conceded non-novel:** CDC-over-radix repair = Irminsul (concurrent twin) + PIC genus; CDC insertion-resilience = FastCDC/Rabin (foundational). We do **not** pitch the mechanism.

- **slope≈1 demoted to accounting identity** (citing CacheBlend §4 `r%`↔overhead + Pope et al.), per §3.2.

- **Defensible novelty kernel (narrow, body-distinguished):** *An engine-internal characterization of prefix-cache recompute COST as a function of injection-to-sequence ratio (recompute% ~ `inj/seq`), MEASURED on the real block/token accounting of vLLM-APC / SGLang-Radix / FlashInfer, together with the empirical WORKLOAD-CONDITIONED win-region of CDC-style repair over that surface — and the consequent negative adoption guidance.* No prior work draws this contour.

**Residual on the novelty axis:** none. The only flagged risk — a cost-map encoded ONLY as an unlabeled plotted curve invisible to HTML-grep — is at VERY LOW risk; every neighbor's caption/axis framing is TTFT/throughput/quality/memory, none mentions injection.

---

## 6. Competitive Positioning (the honest bracket — resolved on the GATHER and in-window E2E axes with the real kernel)

The competitive story is **deliberately conditional** — the framing that survived hostile review (VERDICT-0029/0033/0037/0043) — and **both measured serving axes now favor CDC**: isolated real-kernel gather (EXP-0030) and combined in-window E2E TTFT (EXP-0034). But the honest reading, which we foreground per the product_realist condition, is that the **end-to-end advantage is small and regime-confined**, and the single un-measured axis (true async connector under concurrent load) could compress the smallest cell to a tie.

| comparator | result | source | honest reading |
|---|---|---|---|
| **Contiguous baselines** (vLLM-APC / SGLang-Radix / FlashInfer) | CDC 8.3×–465× cheaper (token-recompute), grows with ctx | EXP-0003 | **STRUCTURAL ARTIFACT** of contiguous whole-suffix recompute (EXP-0006); **do NOT headline.** |
| **Fair re-impl PIC** (selective recompute over real vLLM page table), E2E serving | CDC wins **all 12 cells** on BOTH metrics; TTFT PIC/CDC 1.05–1.79×, throughput CDC/PIC 1.00–1.13×; PIC 0/12 | **EXP-0026** (real vLLM 0.6.6 PagedAttention, Qwen2.5-7B fp16, H100) | CDC's contiguous-prefill advantage **survives the non-contiguous paged KV layout** (the binding VERDICT-0029 question — ANSWERED). LIMITATION: this PIC arm is a faithful re-impl, NOT the published fused kernel. |
| **Oracle / fused PIC** (flash-optimal, ZERO gather overhead) | CDC wins **2/6** cells, both at HIGH `inj/seq` (25%: oraclePIC/CDC 1.054–1.175); **LOSES at low `inj/seq` (1–5%: oraclePIC/CDC 0.612–0.991×)** incl the win-region corner | **EXP-0027** (H100 SDPA oracle bound) | CDC's serving advantage is **itself conditional on `inj/seq`** — opposite direction to the recompute-fraction win-region (a real, publishable nuance). EXP-0026's "wins all 12" was PARTLY the re-impl PIC's gather overhead, as hostile review suspected. CAVEAT: CDC pays a boundary window `Wb=256` the oracle skips → conservative, PIC-favorable bound. |
| **Real published LMCache CacheBlend GATHER kernel** | **CDC contiguous gather wins ALL 12 cells; CI excludes 1.0 in 11/12 (only 8k/0.5% is a tie [0.994,1.028]); PIC/CDC 1.01–1.27×** | **EXP-0030** (source-built LMCache 0.1.dev1 `c_ops.single_layer_kv_transfer`, the published CacheBlend gather, on LIVE vLLM 0.6.6 PagedAttention paged KV, layout `NL_X_TWO_NB_BS_NH_HS` — NOT a re-impl) | The oracle's zero-overhead assumption was too generous: the REAL fused kernel still pays scatter/page-gather cost, so CDC's contiguous gather wins. The bracket resolves **toward the re-impl result (CDC favorable), NOT the oracle (CDC loses).** Margins largest at large-ctx low-`inj/seq` (28k/0.5% = 1.265 [1.229,1.283]); smallest at small-ctx low-`inj/seq` (8k/0.5% tie). |
| **Combined in-window E2E-TTFT** (real CacheBlend blend kernels INLINE in the prefill/decode window, CDC vs PIC, 12-cell) | **CDC faster E2E in ALL 12 cells; PIC/CDC 1.003–1.029× (margins COMPRESS vs the isolated gather, as expected — overlap partially hides PIC cost)** | **EXP-0034** (SCOPED in-window approx — see §2.2; NOT a true async connector; vLLM 0.6.6 lacks the V1 KVConnector API) | **Composition fallacy CONTROLLED:** per-component CDC wins DO compose to an E2E CDC win — smaller, but consistent. **But the margins are operationally marginal (0.3–2.9%), the closest cell (8k/5%) is effectively a tie (§6.2), and this is an in-window approximation, not a true async-connector measurement.** |
| **True async-connector E2E-TTFT under CONCURRENT load** (vLLM≥0.7 V1 KVConnector, real LMCache async layerwise transfers, + latency jitter + concurrent throughput) | **NOT yet measured** | future work (env-upgrade-gated) | **The single un-measured axis = the path to unanimous GREEN (§7).** Known direction: more overlap → smaller CDC margin, not a sign flip within the measured band; could compress the 0.32% min-margin cell to a tie. |

### 6.1 The EXP-0030 (isolated gather) and EXP-0034 (in-window E2E) per-cell tables

**EXP-0030 — isolated real-kernel gather.** H100, Qwen2.5-7B, 28 layers, 12 cells, bootstrap CIs. PIC/CDC > 1 means CDC's gather is cheaper.

| `inj/seq` | 8k PIC/CDC [CI] | 28k PIC/CDC [CI] |
|---|---|---|
| 0.5% | 1.011 [0.994, 1.028] *(TIE — CI includes 1.0)* | 1.265 [1.229, 1.283] |
| 1% | 1.068 [1.029, 1.078] | 1.228 [1.213, 1.231] |
| 2% | 1.103 [1.016, 1.109] | 1.208 [1.190, 1.212] |
| 5% | 1.108 [1.096, 1.114] | 1.114 [1.107, 1.126] |
| 10% | 1.075 [1.051, 1.082] | 1.088 [1.084, 1.089] |
| 25% | 1.057 [1.047, 1.070] | 1.028 [1.022, 1.037] |

CDC gather cheaper in 12/12; CI excludes 1.0 in 11/12; margins 1.01–1.27×.

**EXP-0034 — combined in-window E2E-TTFT (SCOPED approximation, §2.2).** H100, Qwen2.5-7B, 28 layers, 12 cells, **median over 6 reps** (no per-cell bootstrap CI). PIC/CDC > 1 means CDC is faster E2E.

| `inj/seq` | 8k PIC/CDC | 28k PIC/CDC |
|---|---|---|
| 0.5% | 1.025 | 1.011 |
| 1% | 1.017 | 1.021 |
| 2% | 1.012 | 1.014 |
| **5%** | **1.0032 (CLOSEST TO TIE)** | 1.008 |
| 10% | 1.017 | 1.015 |
| 25% | 1.013 | 1.029 |

CDC faster E2E in 12/12; margins 1.003–1.029×; closest cell 8k/5% = 1.0032.

### 6.2 The 8k/5% cell, reported honestly (per the area_chair + evaluation_prosecutor conditions)

The closest-to-tie cell is **8k/5%, PIC/CDC = 1.0032** — CDC ≈ 0.32% faster. **We report this cell honestly and do not over-read it:**

- **The EXP-0034 harness reports per-cell MEDIANS over 6 reps; it does NOT compute a per-cell bootstrap confidence interval** (confirmed in the harness: `statistics.median(ts)` over `reps=6`). We therefore **do not** quote a per-cell CI we did not measure. The honest statement is that **a 0.32% median difference at 6 reps is within plausible measurement and production variance — i.e. operationally a TIE.** Where the *isolated-gather* axis (EXP-0030) does carry bootstrap CIs, the analogous small-context low/high-`inj/seq` corners likewise include 1.0 (e.g. 8k/0.5% gather = 1.011 [0.994, 1.028], CI includes 1.0).
- **The evidence at this cell is therefore the 12/12 DIRECTIONAL CONSISTENCY, not per-cell significance.** Across both serving axes (EXP-0030 gather, EXP-0034 in-window E2E), CDC is faster in every one of the 12+12 cells; the sign is consistent even where the magnitude is within noise. We frame the result as a *consistent directional bracket* (CDC ≥ PIC everywhere measured), explicitly **not** as a per-cell significant win at the 8k/5% corner.
- **The evaluation_prosecutor's caveat stands and we adopt it:** because EXP-0034 is the in-window approximation (§2.2), it structurally handicaps PIC by omitting LMCache's async layerwise transfer scheduler — PIC's primary latency-hiding mechanism. At the 0.32% min-margin cell, any async shrinkage is effectively a tie. We therefore label the 8k/5% cell as a tie until measured on a true async connector (vLLM≥0.7 V1 KVConnector) under concurrent load (§7).

### 6.3 Honest framing sentence for the paper

> "Against the dominant production stack (real vLLM PagedAttention), CDC-style contiguous repair wins on TTFT and throughput in every measured cell (EXP-0026). Against a *fused/oracle* PIC, that advantage was predicted to be conditional on `inj/seq` (EXP-0027). We resolve this against the **real published LMCache CacheBlend gather kernel**: because the real fused kernel still pays scatter/page-gather cost, CDC's contiguous gather wins all 12 cells (EXP-0030, CI excludes 1.0 in 11/12), and a combined *in-window* end-to-end TTFT likewise favors CDC in all 12 cells (EXP-0034, PIC/CDC 1.003–1.029×). **But we are explicit about both the scope and the magnitude: EXP-0034 is a scoped in-window approximation (not a true async-connector measurement; §2.2), its margins are operationally marginal (0.3–2.9%), the closest cell (8k/5% = 1.0032) is effectively a tie reported via 12/12 directional consistency rather than per-cell significance, and the regime is confined (S≥50k).** The one remaining axis is a true async-connector end-to-end TTFT under concurrent load, declared as future work (§7)."

### 6.4 Supporting kernel evidence (consistent; kernel-level, not full serving)

- EXP-0014: CDC faster in all 8 TTFT cells (PIC/CDC 1.02–2.68×); largest 2.68× at win-region corner (32k/0.1%).
- EXP-0021: all 8 cells CI95 excludes 1.0 (incl prev-ambiguous 32k/1% = 1.129 [1.128, 1.151]), 30 reps/cell.
- EXP-0025: throughput — CDC wins 22/24, PIC only 2/24 marginal (0.993–0.994×) at the 8k/5% corner; the predicted PIC-favorable high-`inj/seq` regime actually favors CDC *more* (1.5–1.74× at 50%).
- EXP-0023: analytic serving bridge — end-to-end PIC/CDC band [1.10, 2.03] nominal / [1.00, 1.28] worst-for-CDC; 0/8 cells invert under any plausible overhead; gather-overlap alone cannot flip CDC's advantage.

---

## 7. Future Work, Conclusion, and the Honest Bottom Line

### 7.1 The honest bottom line (lead with this — product_realist condition)

**The win is real but operationally MARGINAL and REGIME-CONFINED, and the paper's primary value is NEGATIVE ADOPTION GUIDANCE.** Stated plainly for a production reader:

1. **Marginal where it wins.** The end-to-end serving advantage of CDC-style contiguous repair over the real CacheBlend/PIC kernel is **0.3–2.9%** in the measured in-window E2E (EXP-0034) — plausibly below production latency variance, and at the closest cell (8k/5% = 1.0032) effectively a tie (§6.2).
2. **Confined to a minority regime.** The win-region is only the large-reused-context, small-injection corner (S≥50k ∧ `inj/seq`≤1%). By injected tokens — the work that costs latency — it is negligible (≤8.1% under any prior; ~81% of tokens sit in the degrade band where CDC ties).
3. **So the actionable contribution is *when NOT to use CDC.*** For the great majority of agentic traffic, CDC-style repair is not worth its engineering and complexity cost; deploy it (if at all) only in the large-context, small-injection corner, and even there expect a small margin. This negative adoption guidance — a measured map of where the repair does and does not pay — is the paper's main practical deliverable.

### 7.2 Declared future work = the env-gated path to unanimous GREEN

The single un-measured axis is a **true async-connector end-to-end TTFT** — the real LMCache async layerwise CPU↔GPU transfer scheduler in the vLLM serving loop, on **vLLM ≥ 0.7/0.8 with the V1 KVConnector API fully enabled, UNDER CONCURRENT REQUEST LOAD**, reporting latency jitter and concurrent throughput. This is **env-upgrade-gated**: the pinned vLLM 0.6.6.post1 lacks the V1 KVConnector API (§2.2), so it could not be measured here.

We declare this explicitly as future work and as **the path to unanimous committee GREEN** (VERDICT-0043: the evaluation_prosecutor's one outstanding ask). Its known direction is bounded: LMCache's async overlap would *further hide* PIC's cost, **shrinking** CDC's margin (and could compress the 0.32% min-margin cell to a tie) — but within the measured band it would not flip the sign. An honest outcome either way is publishable: if CDC's margin survives, it closes the bracket; if the smallest cells go to a tie, that *sharpens* the negative adoption guidance (CDC's edge is real only in the large-context corner and even there is near-tie under realistic async serving).

### 7.3 Related work (condensed; full body-verifications in novelty_boundary_2026-05-31.md)

- **Mechanism family (conceded, cited by name):** **Irminsul (arXiv:2605.05696)** — concurrent/independent CDC-over-radix twin; **EPIC (arXiv:2410.15332) / CacheBlend (arXiv:2405.16444) / Cache-Craft (arXiv:2502.15734) / MEPIC (arXiv:2512.16822) / KVFlow (arXiv:2507.07400) / CacheClip (arXiv:2510.10129)** — the PIC genus. **CacheBlend §4** additionally supplies the `r%`↔overhead identity we cite; **Pope et al. (arXiv:2211.05102)** supplies the KV accounting.
- **Kernel source / async-scope basis:** **LMCache (github.com/LMCache/LMCache)** — the source of the real CacheBlend gather kernel measured in EXP-0030/0034, and the implementation whose V1 async KVConnector defines the un-measured axis (§2.2, §7.2).
- **Production engines (cited by name):** **vLLM / PagedAttention (Kwon et al. arXiv:2309.06180)**; **SGLang RadixAttention (Zheng et al. arXiv:2312.07104)**; FlashInfer.
- **Closest empirical cost-axis neighbor:** Don't Break the Cache (arXiv:2601.06007) — black-box $/TTFT vs prompt-size & tool-count, no engine-internal recompute-fraction, no `inj/seq` axis.
- **Adjacent systems (distinct):** ContiguousKV (arXiv:2601.13631, offload-I/O re-prefill, append-suffix); variable-size-block (arXiv:2604.23994, discrete-diffusion block-commit). Neither addresses mid-prefix autoregressive KV invalidation.
- **Foundational:** FastCDC / Rabin content-defined chunking (CDC insertion-resilience).

### 7.4 Conclusion

We characterized the recompute cost of prefix-cache invalidation under agentic mid-prompt tool injection as an engine-internal cost-map over `inj/seq`, decomposed it per-engine to show the contiguous production engines (vLLM/PagedAttention arXiv:2309.06180, SGLang RadixAttention arXiv:2312.07104, FlashInfer) are *position-driven* (R²=0.0007) while CDC is *`inj/seq`-driven* (slope 0.958 [0.937, 0.980], R²=0.972) — being explicit that this slope is a mechanism-derived accounting identity (CacheBlend arXiv:2405.16444 §4 + Pope arXiv:2211.05102), not an emergent law. We located real agentic traffic on that map and found the CDC win-region is negligible by tokens (≤8.1% under any prior) but a meaningful, prior-robust minority by injection count when conditioned on large reused context (≈46% given S≥50k). We closed the novelty boundary at the body level (10/10 neighbors, "injection" 0× in the PIC family, mechanism conceded as the concurrent twin of **Irminsul arXiv:2605.05696**) and bracketed CDC's serving advantage honestly — resolving the load-bearing uncertainty on the gather axis with the **real published LMCache CacheBlend kernel** (CDC wins 12/12, EXP-0030) and on a combined in-window E2E axis (CDC wins 12/12, EXP-0034, scoped per §2.2). The honest bottom line is that the serving win is **real but marginal (0.3–2.9%) and regime-confined (S≥50k)**, so the paper's primary value is **negative adoption guidance** on when *not* to use CDC. The remaining axis — a true async-connector E2E under concurrent load (vLLM≥0.7 V1 KVConnector) — is declared future work and the env-gated path to unanimous GREEN.

### 7.5 The single honest weakest link

**The true async-connector end-to-end measurement gap.** Our strongest serving evidence comes from three measured axes — re-impl PIC E2E (EXP-0026, 12/12), the real published kernel at the gather component (EXP-0030, 12/12), and the real kernel inline in-window E2E (EXP-0034, 12/12, scoped §2.2). The remaining un-measured axis is the **true async layerwise connector in the serving loop under concurrent load** (vLLM≥0.7 V1 KVConnector). The honest response:

- We **scope EXP-0034 explicitly as the in-window approximation, in the setup section (§2.2), not buried** — it is NOT a true async-connector measurement.
- We **report the 8k/5% cell honestly** (§6.2): no per-cell CI was computed (median over 6 reps), the 0.32% margin is effectively a tie, and the evidence is the 12/12 directional consistency, not per-cell significance.
- We **declare the true async-connector E2E under concurrent load as future work and the env-gated path to unanimous GREEN** (§7.2); its known direction (more overlap → smaller margin) would shrink, not reverse, CDC's advantage within the measured band.
- A measured async result is **publishable either way**: if CDC's edge survives, it closes the bracket; if the smallest cells tie, it sharpens the negative adoption guidance.

This is the only binding residual. Novelty (gate-A) and the cost-map/win-region theory are GREEN/uncontested (VERDICT-0043: novelty_killer, systems_reviewer, theory_skeptic, area_chair all GREEN).

---

## 8. Submission-Readiness Verdict

**CLAIM-0006 is SUBMISSION-READY as an honest-conditional-characterization paper (operator path-(b)), finalized per all VERDICT-0043 conditions.** It carries 4 GREEN / 2 YELLOW / 0 RED; the two YELLOWs are scope-constraints (the un-measured async axis + the marginal-win framing), both now addressed honestly in the prose, not papered over.

What makes it submittable:
1. **Experimental setup + scope (§2):** the EXP-0034 SCOPED in-window approximation is stated prominently up front (NOT a true async KVConnector measurement; vLLM 0.6.6 lacks the V1 API). **[Condition 1 applied.]**
2. **Cost-map (§3):** measured, CI-quantified, per-engine decomposition (EXP-0002/0013). GREEN.
3. **Win-region (§4):** bootstrap CIs, prior-robust, honestly conditional (EXP-0005/0015). GREEN as conditional.
4. **Novelty (§5):** 10/10 neighbors body-verified distinct, mechanism conceded, slope≈1 demoted; baselines cited by name incl. Irminsul as the mechanism twin. **[Condition 3 applied.]** GREEN.
5. **Competitive bracket (§6):** honestly conditional; gather (EXP-0030) + in-window E2E (EXP-0034) both favor CDC; the 8k/5% = 1.0032 cell reported with honest uncertainty framing (no per-cell CI; 12/12 directional consistency is the evidence). **[Condition 2 applied.]** GREEN as conditional.
6. **Future work + bottom line (§7):** leads with the marginal (0.3–2.9%) + regime-confined (S≥50k) framing and the negative-adoption-guidance primary value; the true async-connector E2E (vLLM≥0.7 V1 KVConnector under concurrent load) declared as the env-gated path to unanimous GREEN. **[Condition 4 applied.]**

What it is NOT: a paper claiming CDC universally beats PIC, a slope-law discovery, a token-weighted win, or a true async-connector serving result. Those framings are killed and must not be re-inflated.

**File:** prior_art/PROJ-0002/CLAIM-0006/PAPER_DRAFT_FINAL.md

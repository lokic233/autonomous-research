# CLAIM-0006 — Publication-Ready Synthesis (Honest-Conditional Characterization)

**Claim:** CLAIM-0006 — Prefix-Cache Invalidation Cost-Map + Workload-Conditioned Win-Region of CDC Repair
**Project:** PROJ-0002 · **Target venue:** MLSys
**Author of this synthesis:** researcher-0002-writeup · reporting to orchestrator 22bd6bef · **Date:** 2026-05-31
**Status:** writeup-hardening synthesis (CPU, documentation only; NO claim/verdict/map/experiment edits)
**Scope of this file:** consolidate the GREEN/uncontested core of CLAIM-0006 into a submittable paper
skeleton (abstract + contribution + honest limitations), per the operator's path-(b): submit as an
*honest conditional characterization* TODAY, with EXP-0030 (real-lmcache measured crossover) as future work.

Every number below is cited to an exact EXP id and is copied (not re-derived) from the registry evidence
(CLAIM-0006.yaml VERDICT-0017..0037, EXP result.md files, novelty_boundary_2026-05-31.md). Nothing invented.

---

## 0. ONE-PARAGRAPH POSITIONING (what this paper IS and ISN'T)

This is a **characterization paper**, not a mechanism paper. The CDC-over-radix repair *mechanism* is
explicitly conceded non-novel (Irminsul + the PIC family — body-verified, §3). The contribution is the
**engine-internal recompute-cost map** of prefix-cache invalidation under agentic mid-prompt tool
injection, its **workload-conditioned win-region** with bootstrap CIs, and an **honest, committee-vetted
competitive bracket** that states exactly where CDC-style contiguous repair wins and where it does not.
It is submittable as a conditional characterization; the one open empirical gate (a measured crossover vs
the *published* fused lmcache CacheBlend kernel, EXP-0030) is scoped as future work, not hidden.

---

## 1. THE RECOMPUTE-FRACTION COST-MAP (the core artifact)

### 1.1 The relation
For a pure mid-prefix insertion of R tokens into a reused prefix of length S, a content-defined re-syncing
scheme (CDC) recomputes the R new tokens plus a bounded boundary re-sync window W. Its recompute fraction is

    recompute% = (R + W) / S  ≈  R/S = inj/seq   (for W << R; slope ~1)

and is **flat in edit position** (prepend ≈ interior ≈ terminal), EXCEPT the sequence-start attention-sink
chunk (see §1.4).

### 1.2 What is an ACCOUNTING IDENTITY vs what is MEASURED (the load-bearing distinction)

This is the single most important honesty boundary in the paper, and the committee enforced it
(VERDICT-0017). State it explicitly:

- **ACCOUNTING IDENTITY (derived, NOT a discovery):** "recompute% ~ inj/seq with slope ~1" for a perfectly
  re-syncing scheme is *algebra of contiguous-chunk KV bookkeeping* — recompute = R + W, fraction = (R+W)/S,
  slope 1 by construction with no free parameter. CacheBlend (arXiv:2405.16444, EuroSys'25 §4) states the
  same identity as a tuning dial ("recompute r% of tokens ⇒ r% of full-prefill overhead"). Pope et al.
  (arXiv:2211.05102) gives the underlying KV accounting. **Cite CacheBlend §4 + Pope for the identity so a
  reviewer cannot claim it is uncited or over-claimed as emergent.** Do NOT pitch slope~1 as a "law."

- **WHAT IS ACTUALLY MEASURED (legitimately empirical, the real contribution):**
  1. That CDC *achieves* the near-W=0 re-sync on realistic agentic insertions (not adversarial re-chunk
     cascades) — i.e. that real injections land on the identity line. Quantified per-engine with CIs (EXP-0013).
  2. That this is a **CDC-mechanism-specific** property, NOT a cross-engine law — the decisive decomposition.
  3. The empirical **workload distribution** of inj/seq locating *where on the identity line real traffic
     sits* (EXP-0005/0015, §2).

### 1.3 Per-engine cost-map with CIs (EXP-0013, CPU, stdlib, 405 cells/engine, Student-t + Wilson + bootstrap)

The decisive result is that the cost-map is **two different cost laws**, and slope~1 belongs to ONE engine class:

| engine | slope of recompute% vs inj/seq | 95% CI | R² | governing variable |
|---|---|---|---|---|
| **CDC** | **0.958** | **[0.937, 0.980]** | **0.972** | inj/seq (slope~1, tight) |
| PIC (lean) | 0.907 | [0.738, 1.076] | 0.333 | inj/seq (noisier, W floor) |
| vLLM-APC | 0.476 | [−1.94, 2.89] | **0.0007** | **position, NOT inj/seq** |
| SGLang-RadixAttention | 0.475 | [−1.94, 2.88] | **0.0007** | **position, NOT inj/seq** |
| FlashInfer | 0.475 | [−1.94, 2.88] | **0.0007** | **position (== host engine)** |

- CDC slope is stable per seq-length (4k:0.989, 8k:0.930, 32k:0.956; R²→0.999) — **not an averaging artifact**.
- The three contiguous baselines are **position-driven**: position spread ≈ **69.3 pp** (vLLM-APC/Radix/
  FlashInfer) vs **CDC 0.13 pp** (max 0.52 pp). Their R²≈0 vs inj/seq means they have no inj/seq relationship.
- **Engine-AVERAGED slope is an artifact:** averaging the 3 contiguous engines gives slope 0.258, R²=0.075 —
  a meaningless fit. The honest statement: slope~1 is the **CDC accounting identity**, not a cross-engine law.

### 1.4 Caveats baked into the cost-map (state, do not bury)
- **PROXY:** token-count recompute fraction, not GPU wall-clock (wall-clock is gate-B; see §4).
- **Sequence-start attention-sink:** position-independence holds EXCEPT the first content-defined chunk
  (CDC sink fraction 0.119% of seq; Irminsul body-confirms the position-0 sink is the one genuinely
  position-dependent corner). The paper must write "position-independent EXCEPT the sequence-start sink."
- Anchor reproduction (EXP-0002): the original "~2%" reproduces exactly (CTX=4000, inj=40 → 2.0–2.4%) but
  is a **thin contour at inj/seq≈1%**, not a universal property: surface min 0.02% / median 1.34% / max
  53.05%; breaks to 5.3% @200tok/4k, 20% @1000tok/4k, 49–53% @1000tok/1k.

---

## 2. THE WORKLOAD-CONDITIONED WIN-REGION (EXP-0015, bootstrap CIs, 20k tasks / 291,454 injections)

### 2.1 The honest headline (state the win-region as CONDITIONAL-COUNT-LEVEL-ONLY)

The win-region must be framed on **two axes** that point in opposite directions; conflating them is the
over-claim the committee killed:

| metric | value | 95% CI | framing verdict |
|---|---|---|---|
| **Token-weighted** win-region (inj/seq≤1%), base prior | **0.037** | [0.0361, 0.0379] | token / unconditional framing **UNSUPPORTED** |
| Token-weighted win-region across ALL 16 priors | 0.027 – 0.081 (median 0.037) | ≤0.004 half-width | **never exceeds ~8%** under any prior |
| Count-fraction win-region (inj/seq≤1%), marginal | 0.2461 | [0.2426, 0.2495] | minority of injections |
| **Conditional count-level win GIVEN S≥50k** (CDC home) | **0.4573** | **[0.4531, 0.4613]** | **the surviving, defensible claim** |
| Count-frac-given-S≥50k across 16 priors | 0.411 – 0.520 (median 0.477) | — | **prior-STABLE ~½** |

### 2.2 The precise honest statement (drop into the paper verbatim)

> "**By injected tokens — the work that actually costs latency — the win-region is negligible** (3.7% at the
> base prior; ≤8.1% under every prior tested; ≥92% of injected tokens fall in the mid/degrade regimes where
> CDC ties a fair PIC baseline). Any token-weighted or unconditional 'CDC saves recompute on agentic traffic'
> framing is **not supported**. **By injection count, conditioned on large reused context (S≥50k), small tool
> injections (inj/seq≤1%) are common and CDC wins ~46% of them (0.457 [0.453,0.461]), prior-robustly (41–52%
> across a 4×4 prior grid).** This conditional count-level win-region is the defensible characterization."

So: the win-region is real and prior-robust **only** as a *conditional, count-level* statement
(S≥50k ∧ inj/seq≤1%). It is a meaningful minority of *injections* but a small minority of *tokens*. This
weakens the unconditional / token framing and does not weaken further than VERDICT-0023 already states.

### 2.3 Why S≥50k is the right condition
EXP-0005/0015: as context-scale rises (modeling 200k–1M long-horizon agents) the *share* of traffic that is
large-context grows to 60–76%, consistent with SWE-ContextBench's >97%-cache-read finding for long-horizon
SWE work. So the conditional region, while a minority today, covers a growing fraction of real traffic.

---

## 3. NOVELTY POSITIONING (gate-A — FULLY CLOSED at body level, 10/10 neighbors)

**Gate-A is GREEN/uncontested** (2/5 reviewers GREEN on novelty+theory; the 3 YELLOW are on the orthogonal
measurement gate, §4). Body-verified facts (novelty_boundary_2026-05-31.md):

- **10/10 closest neighbors body-read (full LaTeXML HTML bodies), ZERO cost-map collision:**
  - Don't Break the Cache (2601.06007): black-box provider $/TTFT vs prompt-size & tool-COUNT; no inj/seq
    axis, no recompute-fraction, no engine-internal granularity. [The #1 "same functional form" collapse-fear
    — REFUTED at body level: their linearity is $-savings vs prompt-size, not recompute% vs inj/seq.]
  - Irminsul (2605.05696): CDC-over-radix **mechanism twin** (body-confirmed); metrics = token-recovery% /
    prefill-energy / attn-sink, NOT a recompute cost-map. Indexed in ≥2 sources (Semantic Scholar + OpenAlex).
  - PIC family — EPIC (2410.15332), CacheBlend (2405.16444), Cache-Craft (2502.15734), MEPIC (2512.16822),
    KVFlow (2507.07400), CacheClip (2510.10129): all 6 body-verified distinct; metrics = TTFT/throughput/
    quality/memory/redundant-compute. **The word "injection" appears 0× in all six bodies.**
  - ContiguousKV (2601.13631): offload-I/O re-prefill / read-amplification system; append-suffix, not
    mid-prefix injection; "injection" 0×. variable-size-block (2604.23994): discrete-diffusion block-COMMIT
    generation-quality; not autoregressive KV invalidation; "injection"/"prefix cache" 0×.

- **Mechanism conceded non-novel:** CDC-over-radix repair = Irminsul + PIC genus; CDC insertion-resilience =
  FastCDC/Rabin (foundational). Do NOT pitch the mechanism.

- **slope~1 demoted to accounting identity** (citing CacheBlend §4 r%↔overhead + Pope et al.), per §1.2.

- **Defensible novelty kernel (narrow, body-distinguished):** "An engine-internal characterization of
  prefix-cache recompute COST as a function of injection-to-sequence ratio (recompute% ~ inj/seq), MEASURED
  on the real block/token accounting of vLLM-APC / SGLang-Radix / FlashInfer, together with the empirical
  WORKLOAD-CONDITIONED win-region of CDC-style repair over that surface." No prior work draws this contour.

Residual on the novelty axis: **none** (the read-depth caveat — a cost-map encoded ONLY as an unlabeled
plotted curve invisible to HTML-grep — is flagged at VERY LOW risk; every neighbor's caption/axis framing is
TTFT/throughput/quality/memory, none mentions injection).

---

## 4. THE COMPETITIVE BRACKET (honest, committee-vetted framing)

The competitive story is **deliberately conditional** — this is the framing that survived hostile review:

| comparator | result | source | honest reading |
|---|---|---|---|
| **Contiguous baselines** (vLLM-APC / SGLang-Radix / FlashInfer) | CDC 8.3×–465× cheaper (token-recompute), grows with ctx | EXP-0003 | **STRUCTURAL ARTIFACT** of contiguous whole-suffix recompute (EXP-0006); do NOT headline. |
| **Fair re-impl PIC** (selective recompute over real vLLM page table) | CDC wins serving ALL 12 cells; TTFT PIC/CDC 1.05–1.79×, throughput CDC/PIC 1.00–1.13× | **EXP-0026** (real vLLM 0.6.6 PagedAttention, Qwen2.5-7B, H100) | CDC's contiguous-prefill advantage **survives the non-contiguous paged KV layout**. LIMITATION: lmcache absent → PIC is faithful re-impl, NOT the published fused kernel. |
| **Oracle / fused PIC** (flash-optimal, zero gather overhead) | CDC wins **2/6** cells, both at HIGH inj/seq (25%: 1.05–1.18×); **LOSES at low inj/seq (1–5%: oraclePIC/CDC 0.61–0.99×)** incl the win-region corner | **EXP-0027** (H100 SDPA oracle bound) | CDC's serving advantage is **itself conditional on inj/seq** — opposite direction to the recompute-fraction win-region (a real, publishable nuance). EXP-0026's "wins all 12" was PARTLY the re-impl PIC's gather overhead, as the committee suspected. |
| **Real published lmcache CacheBlend fused kernel** | not yet measured | **EXP-0030** (design filed, FOLLOWUP_DESIGN.md) | **documented FUTURE WORK** — the measured crossover. |

Supporting kernel evidence (consistent, but kernel-level not full serving): EXP-0014 (CDC faster all 8 TTFT
cells, 1.02–2.68×), EXP-0021 (all 8 cells CI95 excludes 1.0, 30 reps/cell), EXP-0025 (throughput: CDC wins
22/24, PIC only 2/24 marginal at 8k/5%), EXP-0023 (analytic serving bridge: 0/8 cells invert).

**Honest framing sentence for the paper:**
> "Against the dominant production stack (real vLLM PagedAttention), CDC-style contiguous repair wins on TTFT
> and throughput in every measured cell (EXP-0026). Against a *fused/oracle* PIC, that advantage is itself
> conditional on inj/seq — CDC wins at high injection but a fused PIC matches or beats it at low injection
> (EXP-0027). We therefore characterize CDC's competitive position **conditionally** and identify the
> measured crossover against the published lmcache CacheBlend fused kernel (EXP-0030) as the decisive
> remaining experiment."

---

## 5. ABSTRACT + THE SINGLE WEAKEST LINK

### 5.1 Proposed abstract (submittable)

> Agentic LLM serving repeatedly injects tool results into a reused prompt prefix, invalidating prefix
> caches mid-sequence. We characterize the *cost* of this invalidation as an engine-internal recompute-
> fraction map over the injection-to-sequence ratio (inj/seq). Measuring the real block/token accounting of
> vLLM-APC, SGLang-RadixAttention, and FlashInfer, we show these contiguous-prefix engines are
> **position-driven** (recompute cost ≈ (1−position), R²≈0.0007 vs inj/seq; ~69 pp swing across edit
> position), whereas a content-defined re-syncing (CDC) repair is **inj/seq-driven and position-independent**
> (slope 0.958, 95% CI [0.937,0.980], R²=0.972; 0.13 pp position spread). We make explicit that this slope~1
> is a *mechanism-derived accounting identity* (cf. CacheBlend's r%↔overhead), not an emergent law, and that
> the CDC repair mechanism is not novel (Irminsul, the PIC family). Our contribution is the cost-map plus a
> **workload-conditioned win-region**: over a realistic agentic workload (20k tasks, 291k injections), CDC's
> recompute win-region is negligible by injected *tokens* (≤8% under every prior), but **conditioned on large
> reused context (S≥50k), CDC wins ~46% of injections (0.457 [0.453,0.461]), prior-robustly (41–52%)**. We
> bracket CDC's serving advantage honestly: it wins every cell against a re-implemented PIC on real vLLM
> PagedAttention (EXP-0026), but against a *fused/oracle* PIC the advantage is conditional on inj/seq —
> winning at high injection and losing at low injection (EXP-0027). We present this as an honest conditional
> characterization and identify a measured crossover against the published fused lmcache CacheBlend kernel as
> the decisive future experiment.

### 5.2 The single weakest link a hostile reviewer attacks (state as honest future work)

**EXP-0030: the measured crossover vs the *published fused* lmcache CacheBlend kernel is not yet run.**

- The attack: "Your strongest serving result (EXP-0026, CDC wins all 12) used a *re-impl* PIC, not the
  published fused kernel. Your own oracle bound (EXP-0027) predicts CDC **loses at low inj/seq (1–5%)** —
  exactly the win-region corner and exactly where CacheBlend's fused kernel was designed to excel. So you
  haven't shown CDC beats real CacheBlend where it matters."
- The honest response (path-(b)): we **concede this and scope it as future work**. The paper does not claim
  CDC beats the fused kernel at low inj/seq; EXP-0027 already states the honest prior is that CDC *loses*
  there. The contribution is the cost-map + conditional win-region + honest competitive bracket — all of
  which stand independent of the EXP-0030 outcome. EXP-0030's design is filed (FOLLOWUP_DESIGN.md; real
  vLLM-v1 + LMCacheConnectorV1, dense low-inj/seq sweep, paired-bootstrap CIs, quality guard). **A measured
  crossover is publishable EVEN IF CDC loses** — it completes the conditional characterization rather than
  refuting it.

This is a ~30-day GPU integration step (operator-owned env `ros-vllm`), the documented long pole. It is the
*only* binding residual; novelty (gate-A) and theory are GREEN/uncontested.

---

## 6. SUBMISSION-READINESS VERDICT

**CLAIM-0006 is SUBMISSION-READY TODAY as an honest-conditional-characterization paper (operator path-(b)).**

What makes it submittable now:
1. Cost-map: measured, CI-quantified, per-engine decomposition (EXP-0002/0013). GREEN.
2. Win-region: bootstrap CIs, prior-robust, honestly conditional (EXP-0005/0015). GREEN as conditional.
3. Novelty: 10/10 neighbors body-verified distinct, mechanism conceded, slope~1 demoted (cited). GREEN.
4. Competitive bracket: honestly conditional, committee-vetted (EXP-0003/0006/0026/0027). GREEN as conditional.
5. The one gap (EXP-0030) is scoped as future work, not hidden — and the paper's claims do not depend on it.

What it is NOT: a paper claiming CDC universally beats PIC, or a slope-law discovery, or a token-weighted win.
Those framings are killed and must not be re-inflated. The paper's spine is **"here is the cost-map; here is
where real traffic sits on it; here, conditionally, is where CDC wins; here, honestly, is what we have not yet
measured."** That is a defensible MLSys characterization paper.

**File:** prior_art/PROJ-0002/CLAIM-0006/WRITEUP_SYNTHESIS.md

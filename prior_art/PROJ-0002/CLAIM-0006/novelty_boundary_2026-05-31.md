# Novelty Boundary — CLAIM-0006 (body-level prior-art distinction)
agent: researcher-novelty-boundary-0006 | role: researcher (prior-art/novelty) | date: 2026-05-31
project: PROJ-0002 | claim: CLAIM-0006 | reporting to: orchestrator 22bd6bef
scope: VERDICT-0017 GREEN-gate (A) — body-level distinction of the surviving single leg
       (engine-internal inj/seq recompute COST-MAP) from its two closest neighbors + PIC family.

## What I could actually READ (anti-hallucination provenance)
- **FULL HTML BODY retrieved & parsed** for the two GREEN-gate works:
  - "Don't Break the Cache" arXiv:2601.06007 (LaTeXML HTML, ~49k chars text) — Sections 1–7 + Appendices A–C read.
  - Irminsul arXiv:2605.05696 (LaTeXML HTML, ~66k chars text) — Sections 1–8 + Appendices A–H read.
  These are BODY-LEVEL reads, not abstract-only. Files: /tmp/txt_2601.06007.txt, /tmp/txt_2605.05696.txt.
- **ABSTRACT-LEVEL only** for the PIC family (EPIC 2410.15332, CacheBlend 2405.16444, Cache-Craft
  2502.15734, MEPIC 2512.16822, KVFlow 2507.07400, CacheClip 2510.10129). I read each arXiv abstract;
  I did NOT exhaustively read their full bodies. My claims about them are scoped to abstract-level
  framing (they are mechanism papers; metric = TTFT/throughput/quality/redundant-compute). Residual
  risk that one buries a recompute%-vs-injection cost-map in an appendix is LOW (their stated metric
  framing is mechanism+TTFT) but NOT body-verified — flagged below.

================================================================================
## NEIGHBOR 1 — "Don't Break the Cache" (arXiv:2601.06007, PwC) — THE decisive GREEN-gate
================================================================================
VERDICT-0017's #1 fear: it "reports cost ~ injected-tool-tokens / prompt-size — the SAME functional
form," so CLAIM-0006 may collapse to a replication. **BODY-LEVEL READING REFUTES THE COLLAPSE.**

What it ACTUALLY measures (body-verified, §3.3 Evaluation Protocol):
- "We measure two primary metrics across all conditions: **API cost** and **time to first token (TTFT)**."
  Cost = dollars (from API-reported token counts × provider pricing); TTFT = wall-ms via streaming.
- It is a **BLACK-BOX provider-API study** across OpenAI / Anthropic / Google. NO engine is touched.
  Body has ZERO occurrences of: vLLM, SGLang, FlashInfer, radix, recompute-fraction, "fraction",
  inj/seq, slope, cost-map, content-defined, "edit position". (verified by grep on full text.)
- Its "linear" result (Abstract + §6.1/§6.2): "cost savings scale linearly with **prompt size**"
  and are "consistent regardless of **tool-call count**." The independent variables are PROMPT SIZE
  (500–50k tokens) and TOOL-CALL COUNT (3–50) — NOT injection-size / sequence-length ratio. The
  dependent variable is $-savings and ms-TTFT vs a no-cache baseline — NOT a recompute FRACTION.
- The four "strategies" (No-Cache UUID breaker / cache-system-prompt / exclude-tool-results / etc.)
  are PROMPT-LAYOUT guidance ("place dynamic content at the end to avoid breaking the cache"). There
  is NO repair mechanism, NO position-independence-of-cost FINDING, NO engine-internal granularity.

### Distinction (VERIFIED at body level):
| axis | Don't Break the Cache (2601.06007) | CLAIM-0006 (engine-internal cost-map) |
|---|---|---|
| (a) recompute-FRACTION vs injection-size cost-map | **NO** — measures $ & ms, not recompute% | YES (recompute% across inj/seq surface) |
| (b) position-independence-OF-COST finding | **NO** — only layout heuristic ("put dynamic at end") | YES (position spread median 0.39pp; inj/seq is the driver, not depth) |
| (c) engine-internal vs black-box granularity | **BLACK-BOX provider API** (no engine) | ENGINE-INTERNAL (vLLM-APC/Radix/FlashInfer block/token accounting) |
| functional form | "$ ~ linear in prompt-size; flat in tool-count" | "recompute% ~ inj/seq, slope~1; flat in position" |

**CONCLUSION (VERIFIED):** 2601.06007 does NOT publish (a), (b), or (c). The "same functional form"
worry is FALSE at body level: their linearity is *$-savings vs prompt-size* (a billing curve over an
opaque provider cache), NOT *recompute-fraction vs injection/sequence ratio* inside an engine. They
even lack the injection-ratio axis entirely (their axes are absolute prompt-size and tool-COUNT).
=> The novelty distinction from 2601.06007 is now **VERIFIED, not assertion-only.** This closes the
single most load-bearing GREEN-blocker for the surviving leg. CITE as the closest empirical neighbor
+ motivation; distinguish on (a)/(b)/(c).

================================================================================
## NEIGHBOR 2 — Irminsul (arXiv:2605.05696) — mechanism twin; 2nd-index status UPDATED
================================================================================
### (i) Mechanism identity — CONFIRMED at body level (mechanism novelty is DEAD, as suspected)
Body: "Irminsul extends SGLang's radix cache with **content-hash keying over CDC-chunked segments**
and a delta-rotation rule for k_r." CDC = **Gear-hash rolling state** over a 64-tok window, expected
chunk ~128 tokens clamped [32,512], xxHash64 fingerprints. Same motivation verbatim spirit as
CLAIM-0006: "bit-identical tokens at shifted positions void prefix caches at the first byte of
divergence." => This IS CLAIM-0006's "CDC repair over radix." MECHANISM = NOT NOVEL. (Confirms
red_zone "CDC-over-radix MECHANISM occupied.")

### (ii) Does Irminsul publish the recompute-fraction inj/seq cost-map? — NO (body-verified)
Irminsul's metrics are: **token-recovery %** ("recovers up to ~83% of prompt tokens above
exact-prefix"), **prefill ENERGY savings** (NVML counters; 1 - E_hit/E_miss), **cache hit-rate**, and
**attention-sink fractions** (W vs S, the first-chunk carve-out analysis). Body has ZERO occurrences
of: "recompute fraction", "cost map", "inj/seq", "injection size", "slope", "as a function of",
"scales with", "linear in". Its 24 "law" hits are CITATION NOISE (OpenClaw post-mortems), NOT a
recompute law. Its "fraction" hits are reuse-fraction / attention-sink-fraction, NOT a
recompute-fraction-vs-injection cost-map. Its closest thing to a predictive curve is the
"partition-shift diagnostic" (marginal recovery = fraction of tokens shifted past the first variation
point) — that predicts RECOVERY/ROI of its OWN mechanism, NOT the recompute-cost contour as f(inj/seq).
=> Irminsul does NOT publish CLAIM-0006's surviving leg. **VERIFIED.**

### (iii) >=2-INDEPENDENT-INDEX rule — STATUS CHANGED (was the prior blocker)
Prior note (LaneA) said Irminsul was a SINGLE index (arXiv only; Semantic Scholar not yet indexed) =>
mechanism collision was a WEAKEN-flag, not an admissible KILL. **As of 2026-05-31 that has changed:**
- Semantic Scholar: NOW INDEXED — CorpusId 288013360, paperId a90ce0eaebf122f01b07acd8163b7400862b79ab.
- OpenAlex: NOW INDEXED — W7160639578, doi 10.48550/arXiv.2605.05696, pub 2026-05-07.
- DBLP: a hit named "irminsul" exists but is a DIFFERENT work (unrelated authors) — does NOT count.
So Irminsul is retrievable in >=2 independent INDICES beyond the arXiv abstract page. CAVEAT for the
committee's exact rule: these indices all point to the SAME single primary work (one arXiv paper, one
author group). So this satisfies "the work is independently INDEXED/retrievable by >=2 sources" — it
does NOT create a 2nd independent *work* corroborating the mechanism. The PIC FAMILY (next section)
is what supplies independent corroboration that the mechanism-genus is occupied. Net: the
mechanism-collision can now be treated as a firm KILL on MECHANISM novelty (Irminsul indexed x2 +
PIC-family genus multi-source), NOT merely a single-source flag.

================================================================================
## PIC FAMILY (abstract-level reads) — corroborate mechanism-genus occupancy; none has the cost-map
================================================================================
| work | id | metric framing (abstract) | (a) cost-map? | (b) pos-indep-of-COST? | (c) granularity | VERIFIED? |
|---|---|---|---|---|---|---|
| EPIC | 2410.15332 | PIC; LegoLink; up-to-8x TTFT | NO (TTFT) | reuse-at-any-position (mechanism, not cost finding) | engine | ABSTRACT-only |
| CacheBlend | 2405.16444 | selective recompute of non-prefix KV; prefill speedup | NO (speedup/quality) | NO | engine | ABSTRACT-only |
| Cache-Craft | 2502.15734 | chunk-cache reuse + small-fraction recompute; -51% redundant compute (RAG) | NO (redundant-compute %, not f(inj/seq)) | NO | engine | ABSTRACT-only |
| MEPIC | 2512.16822 | memory-efficient PIC; block-level recompute | NO | NO | engine | ABSTRACT-only |
| KVFlow | 2507.07400 | workflow-aware KV EVICTION/prefetch (not invalidation) | NO | NO | engine | ABSTRACT-only |
| CacheClip | 2510.10129 | KV reuse beyond strict prefix for RAG; TTFT | NO | NO | engine | ABSTRACT-only |

All six are MECHANISM papers (reuse + selective/partial recompute), measured on TTFT / throughput /
redundant-compute / quality. None states a recompute-FRACTION-vs-injection-size COST-MAP or a
position-is-not-the-driver COST finding in its abstract. Cache-Craft's "-51% redundant compute" is the
nearest — but it is a single aggregate RAG number, NOT a contour over an inj/seq surface, and it is
chunk-reuse at arbitrary RAG positions, not mid-prefix tool-injection cost characterization.
RESIDUAL UNVERIFIED RISK (LOW): I did not read these six bodies; a cost-map buried in an appendix
cannot be 100% excluded from abstract alone. Flagged as the one remaining body-level GREEN-blocker
on the PIC side (cheap to close: ~1 hr of body reads, CPU-only).

================================================================================
## slope~1 — IS IT AN ACCOUNTING IDENTITY OR AN EMERGENT LAW? (committee framing point)
================================================================================
**I CONFIRM the committee (VERDICT-0017): slope~1 is a MECHANISM-DERIVED ACCOUNTING IDENTITY, not an
emergent discovery.** Reasoning (no new experiment needed; it's algebra of contiguous-chunk KV):
- KV cache stores per-token K,V contiguously; a contiguous-prefix cache (PagedAttention/APC, Radix)
  reuses the maximal matching prefix and recomputes everything after the first divergence
  (Kwon et al. PagedAttention 2309.06180; the prefill/decode KV accounting in Pope et al. 2211.05102).
- For a pure INSERTION of R tokens into a reused prefix of length S where a content-defined / re-syncing
  scheme localizes the edit, the recomputed set = {the R new tokens} + {a boundary re-sync window W}.
  Recompute fraction = (R + W)/S. For W << R this is exactly R/S = inj/seq, i.e. slope 1 BY
  CONSTRUCTION. There is no free parameter; the "slope~1" is the derivative of a linear token-accounting
  ratio, not a fitted empirical exponent. (Contrast: a genuine emergent "law" would have a non-trivial
  exponent that does NOT fall out of token bookkeeping — e.g. the super-quadratic injection-penalty
  hypothesis that was already REJECTED as YELLOW k~1.3 in committee_naviC, MEMORY.md.)
- COROLLARY (also identity, not discovery): "position is not the cost driver." For a pure insertion the
  recomputed-token COUNT = R + W regardless of WHERE the insert lands (early/late), because a re-syncing
  scheme recovers the unchanged suffix at any depth. So recompute% is flat in position by the same
  accounting — EXCEPT at the sequence-start sink (Irminsul's first-chunk carve-out shows the position-0
  attention-sink IS special; CLAIM-0006's "position-independent" must caveat the p=0 sink, which Irminsul
  body-confirms is the one genuinely position-dependent corner).
**Push-back nuance (in CLAIM-0006's favor, modest):** the identity tells you slope~1 IF the scheme
re-syncs perfectly. The contiguous baselines do NOT re-sync, so THEIR curve is (1-f)·(1) — also an
identity. The only thing that is *measured* rather than *derived* is (1) that CDC actually achieves the
near-W=0 re-sync on realistic agentic insertions (vs adversarial re-chunk cascades), and (2) the
empirical WORKLOAD distribution of inj/seq (EXP-0005: median 2.8%) that locates where on the identity-
line real traffic sits. Those two are legitimately empirical. But the slope~1 "law" itself is NOT a
discovery — demote to "an accounting identity we quantify + locate on a real workload." Committee is
correct; do not re-inflate it to a law.

================================================================================
## DEFENSIBLE NOVELTY KERNEL (what survives, scoped to what I verified)
================================================================================
CLAIM-0006's defensible, body-distinguished novel contribution is NARROW:
  "An ENGINE-INTERNAL characterization of prefix-cache recompute COST as a function of injection-to-
   sequence ratio (recompute% ~ inj/seq) under agentic mid-prompt tool injection, MEASURED on the
   real block/token accounting of vLLM-APC / SGLang-Radix / FlashInfer, together with the empirical
   WORKLOAD-CONDITIONED win-region of CDC-style repair over that surface (where on the identity-line
   real agentic traffic lands: median inj/seq~2.8%, CDC-wins ~25%, ~46% conditioned on S>=50k)."
What is NOT novel (do not pitch): the CDC-over-radix REPAIR MECHANISM (Irminsul, body-confirmed twin;
PIC genus EPIC/CacheBlend/Cache-Craft/MEPIC); CDC insertion-resilience (FastCDC/Rabin, foundational);
the slope~1 "law" and position-independence (mechanism-derived accounting identity per Pope/Kwon).

================================================================================
## DISTINCTIONS THAT REMAIN ASSERTION-ONLY (residual GREEN-blockers for the committee)
================================================================================
1. **[LOW residual] PIC-family bodies not read.** EPIC/CacheBlend/Cache-Craft/MEPIC/KVFlow/CacheClip
   distinction is ABSTRACT-level only. Cannot 100%-exclude a cost-map in an appendix. Cheap to close
   (CPU, ~1 hr body reads). Recommend the orchestrator dispatch this before committee re-vote.
2. **[CLOSED → was the #1 blocker] 2601.06007 distinction is now BODY-VERIFIED** (above). No longer
   assertion-only.
3. **[CLOSED → was a blocker] Irminsul 2nd-index** now satisfied (Semantic Scholar + OpenAlex).
   Mechanism collision is firm. (Caveat: same single primary work indexed x2, not 2 independent works.)
4. **[ORTHOGONAL, still open — NOT mine] Eval GREEN-gate**: token-count proxy vs GPU wall-clock on a
   REAL PIC artifact at the ~5% crossover. This is the GPU gate (human-go), untouched here; it is the
   binding remaining blocker, independent of novelty.
5. **[MINOR] position-independence must caveat the p=0 attention-sink** (Irminsul body shows sink is
   sequence-start-local and genuinely position-dependent there). CLAIM-0006 should state "position-
   independent EXCEPT the sequence-start sink chunk," else a reviewer with Irminsul in hand dings it.

================================================================================
## PIC-FAMILY BODY DISTINCTION (researcher-pic-bodies-0006, 2026-05-31)
## — closes the LOW residual GREEN-blocker (PIC bodies were abstract-only)
================================================================================
reporting to: orchestrator 22bd6bef | scope: VERDICT-0017 GREEN-gate (A), PIC side only.
TASK: the prior researcher body-read 2601.06007 + Irminsul but only ABSTRACT-read the PIC
family. I retrieved & parsed the FULL LaTeXML HTML BODIES of all 6 PIC-family neighbors and
checked each for: (a) recompute-fraction-vs-injection-size cost-map / inj-seq law, (b) a
position-INDEPENDENCE-OF-COST finding (not a position-independent *caching mechanism*), (c)
engine-internal recompute-fraction granularity.

### PROVENANCE (anti-hallucination — exactly what I read)
- **FULL HTML BODY retrieved & parsed** for ALL SIX via https://arxiv.org/html/<id>
  (real LaTeXML bodies, title-verified, not no-HTML stubs). Text files on cli:dengcchi-mac:
  /tmp/pictxt_2410.15332.txt (EPIC, 56k chars), /tmp/pictxt_2405.16444.txt (CacheBlend, 76k),
  /tmp/pictxt_2502.15734.txt (Cache-Craft, 148k), /tmp/pictxt_2512.16822.txt (MEPIC, 65k),
  /tmp/pictxt_2507.07400.txt (KVFlow, 44k), /tmp/pictxt_2510.10129.txt (CacheClip, 67k).
- These are now BODY-LEVEL reads (sections + figure captions + eqn text), NOT abstract-only.
  I grep-verified the full text of each for the cost-map signature set + read the context of
  every near-miss hit (Cache-Craft CCI/CFO model, CacheBlend r% knob, EPIC O(15%N^2) note).
- **DECISIVE GLOBAL GREP RESULT (all 6 bodies):** ZERO occurrences of any of {inj/seq,
  injection ratio, injection-to-sequence, injection size/length, cost map, cost contour,
  recompute fraction (as a measured law), recompute as a function of injection, position-
  independent cost, cost is independent of position, slope}. The word "injection" appears
  **0 times** in EVERY ONE of the six bodies. None frames the agentic mid-prefix *injection*
  problem at all; all six are RAG-chunk-reuse / multi-agent-prefix-reuse papers.

### Per-work body-distinction table (does it publish CLAIM-0006's surviving leg?)
Leg = engine-internal recompute-FRACTION-vs-inj/seq COST-MAP + position-not-the-cost-driver finding.
| Work | id | (a) inj/seq recompute cost-map? | (b) position-INDEP-OF-COST finding? | (c) engine-internal recompute granularity | Read depth | VERIFIED? |
|---|---|---|---|---|---|---|
| **EPIC** | 2410.15332 | **NO** — metric = TTFT (up-to-8x) + throughput (7x) + accuracy; no inj/seq axis. The one cost-vs-size statement is `O(15%·N²)` (a COMPLEXITY note about CacheBlend's quadratic cost vs absolute prompt length N — NOT recompute% vs injection ratio). LegoLink recomputes each chunk's first-k tokens (a fixed structural rule), not a fraction fit to injection size. | **NO** — "position-independent" = the *caching mechanism* (reuse chunks regardless of prefix position); never a finding that recompute COST is flat in position. | engine (LegoLink over PIC) | FULL BODY | **VERIFIED distinct** |
| **CacheBlend** | 2405.16444 | **NO** — `r%` is a *fixed control knob*: "if we recompute r% of tokens per layer, the total compute overhead will be r% of full prefill" — an *accounting identity stated as a tuning dial*, chosen to minimize *attention deviation* (quality), NOT a measured map of recompute% as f(inj/seq). Metrics = TTFT/throughput/quality (F1/ROUGE). The token-selection is by KV-deviation magnitude, not injection size. | **NO** — fuses caches "regardless of prefix or not" (mechanism); no position-cost contour. | engine (selective KV recompute) | FULL BODY | **VERIFIED distinct** |
| **Cache-Craft** | 2502.15734 | **NO (closest near-miss, resolved)** — its model is `CFO as a function of CCI`. CCI (Cache Context Impact) = sigmoid of an outside-vs-inside contextualization ratio = a *reusability/quality* proxy per chunk; CFO/output-deviation drives a recompute-token *selection* model (which & how many tokens to fix to preserve ROUGE). This is a recompute-SELECTION-vs-QUALITY model, **not** a recompute-FRACTION-vs-INJECTION-RATIO cost contour. Headline "-51% redundant compute" is a single aggregate RAG number. "any position" = the *mechanism* (reuse chunks at non-prefix order), not a cost finding. | **NO** — "reuse at any position" is the mechanism claim; no cost-vs-position law. | engine (chunk-cache + selective recomp) | FULL BODY | **VERIFIED distinct** |
| **MEPIC** | 2512.16822 | **NO** — contribution = shifting recompute from token-level to BLOCK-level so "only the first block is request-specific" + RoPE fusion for shareability; goal = MEMORY/HBM footprint reduction under concurrency. No inj/seq axis; "injection" absent. Mentions tool-using agents as a *reuse-amplifier* motivation, not an injection-cost study. | **NO** — "position-independent" = mechanism (chunk KV reuse across positions/requests/batches). | engine (paged block-level PIC) | FULL BODY | **VERIFIED distinct** |
| **KVFlow** | 2507.07400 | **NO** — workflow-aware EVICTION priority + KV PREFETCH/scheduling for multi-agent radix caches. Zero "injection", zero "fraction", no "invalidat*". Recompute appears only as the *penalty of eviction* ("evicted → recomputed from scratch upon reuse"). Metrics = throughput/latency/speedup. Pure scheduling work. | **NO** | engine (SGLang radix scheduling) | FULL BODY | **VERIFIED distinct** |
| **CacheClip** | 2510.10129 | **NO** — RAG KV-reuse via auxiliary-small-model-guided token SELECTION for selective recomputation (exploits attention sparsity: top 10-20% of tokens carry most attention). Metric = TTFT. Recompute is selection-by-attention-importance, not a fraction fit to injection size. Zero "injection"/"fraction(-cost)". | **NO** — position handling = position-ID rearrangement (mechanism), no cost-vs-position finding. | engine (calibration + token selection) | FULL BODY | **VERIFIED distinct** |

### KEY VERIFIED FINDINGS
1. **NO COLLISION. None of the 6 PIC-family bodies pre-empts CLAIM-0006's cost-map leg.** All six
   are mechanism/systems papers measured on TTFT / throughput / quality / memory / redundant-compute.
   None has an injection-to-sequence axis (the word "injection" is absent from all six), none
   reports recompute-FRACTION as a measured *law/contour* over inj/seq, and none states a
   position-INDEPENDENCE-OF-COST finding (their "position-independent"/"any position" language is
   uniformly about the *caching mechanism*, not a cost contour).
2. **The two near-misses are body-resolved, not asserted away:**
   - **CacheBlend `r%`** is a *tuning knob* whose identity ("overhead = r% of full prefill") is the
     SAME contiguous/selective-recompute accounting CLAIM-0006 itself reduces to (cf. the slope~1
     identity section above) — but CacheBlend uses it as a dial to trade quality, it does NOT *map*
     recompute% as a function of injection/sequence ratio. So it CORROBORATES that the accounting is
     known (reinforcing: the slope~1 piece is NOT novel) while NOT pre-empting the *characterization
     over an injection surface conditioned on real agentic traffic*.
   - **Cache-Craft CFO(CCI)** is a quality-driven recompute-*selection* model, not an inj/seq cost map.
3. **EPIC `O(15%·N²)`** is the nearest cost-vs-size statement in the whole family, but it is a
   *complexity bound vs absolute prompt length N* of CacheBlend's quadratic selective-recompute — it
   is NOT recompute-fraction vs injection-to-sequence ratio, and EPIC raises it to *motivate killing*
   that quadratic cost, not to characterize it as a law.

### SECONDARY NOTE FOR THE COMMITTEE (does NOT change gate-A, flag for honesty)
CacheBlend's stated "recompute r% ⇒ r% of full-prefill overhead" makes explicit, in a published
EuroSys'25 Best-Paper body, the linear recompute%↔compute accounting that CLAIM-0006's slope~1 leg
rests on. This is FURTHER body-level support for the committee's existing demotion of slope~1 from
"law" to "accounting identity" (VERDICT-0017). It does NOT touch the surviving cost-map leg (which is
the *empirical inj/seq surface + workload-conditioned win-region*, not the slope identity), but the
writeup should cite CacheBlend §4 for the r%↔overhead identity so a reviewer can't claim the identity
is uncited/over-claimed.

================================================================================
## GATE-A STATUS AFTER THIS WORK
================================================================================
**Novelty GREEN-gate (A) is now FULLY CLOSED at body level for the cost-map leg.**
- 2601.06007 "Don't Break the Cache": BODY-VERIFIED distinct (prior researcher) — black-box $/TTFT
  vs prompt-size & tool-count, no inj/seq cost-map. [the #1 collapse-fear, refuted]
- Irminsul 2605.05696: BODY-VERIFIED mechanism twin (CDC-over-radix), no cost-map; 2-indexed. [mechanism dead, cost-map intact]
- PIC family (EPIC, CacheBlend, Cache-Craft, MEPIC, KVFlow, CacheClip): **all 6 now BODY-VERIFIED
  distinct** (this work). No appendix cost-map exists; "injection" absent from all six. The LOW
  residual flagged by the prior researcher (#1 in their residual list) is CLOSED — no cost-map
  collision in any PIC neighbor.

**Residual after this work (none on the novelty/gate-A axis):**
- The ONLY remaining binding GREEN-blocker is the ORTHOGONAL **Eval gate (B)**: GPU wall-clock TTFT
  on a REAL PIC artifact (CacheBlend/EPIC published) across the inj/seq surface at the ~5% crossover
  (CPU proxy conflates contiguous-chunk vs scattered-HKVD). Untouched here (GPU, human-go). NOT a
  novelty residual.
- MINOR carry-over (from prior researcher, unchanged): position-independence must caveat the p=0
  attention-sink chunk (Irminsul carves it out as genuinely position-dependent).
- HONEST SCOPE NOTE: I body-read these 6 via arXiv LaTeXML HTML. That captures section text + figure
  captions + equation glosses. I did NOT separately fetch external figure-image pixels or any
  ancillary/supplementary PDF beyond the arXiv HTML render; a cost-map encoded ONLY as an unlabeled
  plotted curve with no caption/axis text is not something HTML-grep can see. Risk this changes the
  verdict is VERY LOW (every paper's stated metric framing, figure captions, and axis labels are
  TTFT/throughput/quality/memory; none mentions injection or an inj/seq axis anywhere in caption text),
  but I flag it rather than assert pixel-level reading I did not do.

================================================================================
## PROPOSED MAP-0001 DELTAS (PROPOSE-ONLY — orchestrator applies)
================================================================================
1. CLAIM-0006 open_gaps entry — append: "PIC-family (EPIC/CacheBlend/Cache-Craft/MEPIC/KVFlow/
   CacheClip) all BODY-VERIFIED distinct from the inj/seq cost-map leg (pic-bodies-0006, 2026-05-31):
   ZERO 'injection' axis in any of the 6 bodies, no recompute%-vs-inj/seq contour, no position-
   independence-OF-COST finding (their 'position-independent' = caching mechanism only). Novelty
   GREEN-gate (A) now FULLY CLOSED at body level; only binding residual = eval gate (B) GPU wall-clock
   [human-go]."
2. key_prior_work annotations — refine the PIC entries to body-verified status:
   - EPIC 2410.15332: "(PIC/LegoLink; TTFT/throughput metrics; recompute=first-k-tokens-per-chunk
     structural rule + O(15%N^2) complexity note re CacheBlend; NO inj/seq cost-map — BODY-VERIFIED)"
   - CacheBlend 2405.16444: "(EuroSys'25; selective KV recompute; r% is a quality-tuning knob with
     identity 'r% recompute => r% prefill overhead' — cite for the slope~1 accounting identity; NO
     inj/seq cost-map — BODY-VERIFIED)"
   - Cache-Craft 2502.15734: "(chunk-cache RAG; CFO(CCI) is a recompute-SELECTION-vs-quality model,
     not an inj/seq cost contour; -51% redundant-compute is one aggregate; NO cost-map — BODY-VERIFIED)"
   - MEPIC 2512.16822: "(block-level recompute for HBM efficiency; NO inj/seq cost-map — BODY-VERIFIED)"
   - KVFlow 2507.07400: "(workflow-aware eviction/prefetch scheduling; NO invalidation law/cost-map — BODY-VERIFIED)"
   - CacheClip 2510.10129: "(RAG KV reuse, aux-model token selection via attn sparsity; TTFT; NO cost-map — BODY-VERIFIED)"
3. red_zones — no change to mechanism red-zone (CDC-over-radix stays DEAD). OPTIONAL add a clarifying
   note: "PIC-family selective-recompute (CacheBlend r%, Cache-Craft CFO/CCI, CacheClip aux-model
   selection) occupies the recompute-token-SELECTION mechanism genus — distinct from, and does NOT
   pre-empt, the engine-internal inj/seq recompute COST-MAP characterization (gate-A body-closed)."
4. Update MAP-0001 last_updated + source line to record "+pic-bodies-0006 (2026-05-31): all 6 PIC
   bodies body-verified distinct, novelty gate-A fully closed, only eval gate-B residual."

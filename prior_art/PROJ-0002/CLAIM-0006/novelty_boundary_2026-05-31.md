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

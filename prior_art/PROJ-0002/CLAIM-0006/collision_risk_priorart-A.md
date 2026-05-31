# Collision Risk — CLAIM-0006 (researcher-cdc-priorart-A, 2026-05-31)

## FATAL-on-mechanism (but currently single-source => WEAKEN, not KILL)
- **Irminsul** (arXiv:2605.05696, 2026-05-07): CDC content-defined chunking over SGLang radix cache for
  agentic position-independent caching. Mechanism-identical to CLAIM-0006's "CDC repair." Motivation
  identical ("bit-identical tokens at shifted positions void prefix caches"). It does NOT present the
  inj/seq cost-map nor the 'invalidation law'. Anti-hallucination rule: a novelty KILL needs >=2
  independent sources; Irminsul is presently only on arXiv (Semantic Scholar not yet indexed). => loud
  FLAG. Re-verify when a 2nd index appears; then mechanism-novelty is formally dead.

## HIGH / MEDIUM (mechanism family — partial-recompute / PIC)
- Cache-Craft (2502.15734) HIGH; CacheBlend (2405.16444) MEDIUM; EPIC (2410.15332) MEDIUM;
  MEPIC (2512.16822) MEDIUM; CacheClip (2510.10129) MEDIUM. All = "reuse non-prefix KV + selectively
  recompute a small fraction to fix it." CLAIM-0006's CDC repair is one realization of this family.
  >=2 independent sources confirm the FAMILY exists (admissible as prior art).

## FOUNDATIONAL
- CDC insertion-resilience (FastCDC, Rabin, US11928092B2, ETH "Breaking & Fixing CDC"): textbook. The
  core property CLAIM-0006 leans on is decades old. Novelty cannot rest on "CDC localizes an insertion."

## LOW (cost/eval axis — leaves the cost-map novel)
- "Don't Break the Cache" (2601.06007): black-box provider-API agentic prompt-cache eval. Closest to a
  cost characterization, but NO engine recompute-fraction, NO f(inj/seq) law, NO repair mechanism, NO
  head-to-head vs APC/Radix/FlashInfer. Distinguishable; CITE as motivation.

## Net
- MECHANISM novelty: dead-on-arrival in spirit (Irminsul + PIC family), formally a WEAKEN pending 2nd source.
- FRAMING novelty (Invalidation LAW + conditional inj/seq cost-map + recompute-fraction head-to-head): NO
  collision found -> NOVEL. This is the only defensible committee story.

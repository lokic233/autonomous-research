# PROJ-0010 — Error-Fork KV Fragmentation: Tool-Error Subtrees Are Non-Shareable (RadixAttention Economics)

Seeded: 2026-06-01 by orchestrator-r7-001 (design committee proj0910_design, 6/6 ALL_COMMITTEE_DONE).
Verdict: YELLOW / seed-with-mandatory-fixes (FINAL_VERDICT B=yellow). First claim: CLAIM-0021.

## THESIS
In cross-session prefix sharing (RadixAttention/SGLang, vLLM APC), the KV cache is a radix tree branching at
the first divergent token. A tool error (is_error) injects a high-entropy state/timestamp-laden result +
corrective reasoning; structural cause: that error subtree is rarely reproduced by a future session (errors
nondeterministic), so prefill DOWNSTREAM of an early error may be permanently forked out of the shared tree
unless the agent RE-CONVERGES to canonical state. Live CC: errors hit 9.3% of calls / 60% of sessions; among
error sessions mean 63% / median 79% of footprint is downstream of the first error. NON-TRIVIAL claim: does
downstream prefill RE-CONVERGE (re-enter the shared tree), and is the non-shareable fraction predictable from
error position/type over the joint baseline.

## FIRST CLAIM (CLAIM-0021)
A predictable, non-negligible fraction of post-error prefill is permanently non-shareable across sessions, and
error position/type predicts it over the joint baseline. The LOAD-BEARING NOVEL claim is RE-B1 re-convergence
(an empirical cross-session property ABSENT from PROJ-0007), NOT non-shareability magnitude.

## PRE-REGISTERED RE GATES (with committee MANDATORY FIXES baked in)
- RE-B0 (magnitude floor): >=20% of corpus footprint downstream of an error in error-bearing sessions
  (live 63%). Floor gate.
- RE-B1 (re-convergence reality check + LOAD-BEARING NOVEL claim) [FIX-2 + FIX-4]: a post-error segment is
  "re-converged" iff a tool-call signature AND its cross-session **error-RESULT identity** (not just
  name\0canon_args) recurs in >=1 OTHER session's pre-error shared prefix. If the same error recurs across
  sessions (same missing-file/repo), error subtrees ARE re-shared -> "permanently forked" weakened. Formal
  differentiator from PROJ-0007/DEAD-0015: nondeterministic-irreproducible (errors) vs deterministic-volatile-
  but-canonicalizable (PROJ-0007 drift). If ~100% re-converges -> errors benign -> CLEAN KILL.
- RE-B2 (LOAD-BEARING KILLER, over JOINT baseline): per session, label = downstream-of-first-error footprint
  in top half of non-shareable mass. B0 = {log1p(gap), log1p(freq), tool-mix}. B1 = B0 + error features
  (error position fraction, #errors, error-tool class, **length-residualized** error-result entropy proxy
  [FIX-3]). PASS iff dAUC_LB95 > 0 AND dAUC_point >= 0.03 [stat fix]. If <=0 -> fully explained by ordinary
  cadence -> clean negative.
- RE-B2b (matched-success-divergence baseline) [FIX-1, UPGRADE GATE]: measure non-shareable mass on a control
  group of SUCCESSFUL calls matched by result length/entropy. If error-group non-shareable fraction is
  statistically indistinguishable from the matched success group -> "error-fork" thesis falsified as ordinary
  trajectory divergence. THE yellow->green upgrade gate.
- RE-B3 (cross-instrument, HARD GATE): Codex replication — sign agreement REQUIRED for PASS [FIX].
- STAT DISCIPLINE: fold-to-fold dAUC std, ALL 5 folds positive (sign-stability), Herfindahl of positive-class
  mass (>0.2 => flag 2-3-session domination).
- PRE-REG: OSS prior-art section (SGLang RadixAttention/HiCache + vLLM APC + internal RE-B7/RE-B8) with stated
  non-overlap; live arXiv-ID re-verification before authority.

## NOVELTY / NON-COLLISION (committee-checked)
First error-aware shareability accounting; RadixAttention/APC assume divergence is task-content-driven, neither
models errors as a distinct fork class nor measures re-convergence rate. Not PROJ-0003 (failure attribution/
recovery — B measures KV-cache SHAREABILITY cost, not cause/recovery). Not DEAD-0015/PROJ-0007 (canonicalization-
recoverable drift — B's forks are error nondeterminism, NOT canonicalization-recoverable; that distinction is
the load-bearing point). Not DEAD-0016 (byte-identical repeats). No decode-time SD.

## L0 GATING EXPERIMENT
EXP (CPU, Mac stdlib, reuse EXP-0054 parse+JOIN). Cross-session tool-signature + error-result multiset
membership + session-level logistic B0 vs B1 + 2000x bootstrap, <15s. YELLOW->GREEN contingent on ALL fixes
incorporated into pre-registration BEFORE L0 entry.

# EXP-0043 — CLAIM-0012 GREEN-path (VERDICT-0046 remaining gaps)

**Agent:** researcher-0012-green-r3 · **Claim:** CLAIM-0012 · CPU/stdlib-only · re-analysis of logged traces (no new experiments).
**Full synthesis:** `prior_art/PROJ-0003/CLAIM-0012_GREENPATH_r3_2026-05-31.md`

## What this experiment adds beyond EXP-0042
EXP-0042 already covered CC-LOSO + Cox-vs-Hawkes BIC + Bonferroni — I **independently re-ran robust_L4.py and reproduced it exactly** (ΔBIC CC+9.74/Codex+26.85/Gemini+13.76; CC tool-strat fails Bonferroni 0.078; LOSO collapse to p≈0.19). This experiment adds the two gaps EXP-0042 did NOT cover:

### (A) (B,M)-plane placement (results/bm_plane.csv)
Goh-Barabási burstiness B (Kim&Jo finite-size-corrected) + lag-1 memory M on pooled inter-failure gaps, bootstrap CIs:
- CC: B_corr 0.429 [0.216,0.533], M 0.179 [−0.128,0.207]
- Codex: B_corr 0.276 [0.126,0.382], M 0.228 [−0.211,0.275]
- Gemini: B_corr 0.214 [−0.367,0.336], M 0.071 [−0.192,0.311]
- Point estimates land in the earthquake/SRE cascade quadrant (B>0 AND M>0), distinct from memoryless human-email (B>0,M≈0).
- **WEAKENING:** M-CI crosses 0 on all 3 → the memory axis is NOT defensible from the (B,M) statistic alone; the Hawkes ΔBIC is the load-bearing memory evidence. SRE/human anchors are literature-cited (not re-measured on-node — flagged).

### (B) Label audit (results/label_audit_samples.csv, 285 samples)
- Labels are harness-NATIVE (CC is_error, Gemini status, Codex 99% nonzero-exit) → committee's heuristic-label concern defused; NO leakage.
- **NEW WEAKENING:** label-COMPOSITION problem. Gemini failures = 30/60 schema-argerror + 20/60 path-gate + only 1/60 genuine exec → ~98% trivial malformed-call clustering. CC = 48/146 permission-gate. Codex = clean heterogeneous exec failures (cleanest leg).

## Verdict: STILL YELLOW. Over-dispersion 3-harness solid; discriminating self-excitation = 1 strong (Codex) + 1 fragile (CC, EXP-0040 mode) + 1 trivial-population (Gemini). Does NOT resolve to 3-harness GREEN at claimed altitude. Reframe to Codex-led + caveated. Prior-art sweep done (web available): estimand open, altitude bar raised by 2604.15084 (static-heterogeneity-mimics-burstiness) + Barabási-2005 universal-burstiness null.

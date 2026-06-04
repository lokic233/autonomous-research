# PROJ-0026 — Data-systems-for-ml: length-sorted sequence PACKING inflates gradient-noise-scale (GNS) via domain co-location = hidden data-parallelism tax (EMPIRICAL PHENOMENON)
Fresh area: data-systems-for-ml (sequence-packing ORDERING axis). EMPIRICAL-phenomenon. Survivor of scout-K's 10-killer
search. CLEARS killer #10 (could-the-L0-fail): the headline GNS_sorted/GNS_shuffled ratio is GENUINELY UNCERTAIN +
parameter-DEPENDENT (3 null exits the sim must run to rule out). THESIS: length-sorted greedy sequence packing
(SPFHP/best-fit-decreasing, the standard production packer) inflates per-step gradient-noise-scale (GNS, McCandlish
B_simple=tr(Sigma)/||g||^2) vs globally-shuffled packing, because document LENGTH correlates with DOMAIN -> same-length
=same-domain docs co-locate in the same packed row + thus the same minibatch -> collapses within-batch domain
diversity. Headline: at fixed token budget, length-sorted packing yields a measurably LARGER GNS (>=1.3x in the
realistic regime) than shuffle-then-pack -> its EFFECTIVE batch size < nominal = a hidden data-parallelism tax the
seminal packing paper's 'without impacting performance' does NOT cover (that claim is about the ATTENTION cross-
contamination axis; this is the orthogonal BATCH-COMPOSITION/minibatch-IID axis). Passes all 10 killers: NOT metric-
validity (GNS measured from real gradients, behavioral not counting); NOT closed-form (GNS under correlated minibatches
depends on the empirical (length,domain) joint + realized per-example gradient covariance, must be measured); foundational
incumbents ADDRESSED+VERIFIED (Krell 2107.02027 SPFHP/NNLSHP 'without impacting performance' = ATTENTION axis only,
silent on batch-composition; McCandlish 1812.06162 B_simple ASSUMES IID minibatches — the exact assumption length-sort
breaks); NOT known-mechanism-costume + STRONGEST-baseline (the baseline arm = SHUFFLE-THEN-PACK, same packer/masking/
token-efficiency, differs ONLY in row-ordering — isolates the ordering axis, no strawman); NOT wrong-currency (effective
batch size via GNS = the canonical data-parallelism currency); NOT trivially-small/assumed-shape (magnitude driven by
the REAL corpus length<->domain correlation, measured not injected — code/chat short, books/web long); NOT omitted-
mitigation (shuffle-then-pack + large shuffle buffers IS the standard mitigation + IS the baseline arm; sweep finite
buffer); citations VERIFIED (Krell=attention-axis, McCandlish=IID-assumption read correctly), claim is explicitly ABOUT
an IID violation (no IID overstatement); NOT mechanism-textbook (gradient-diversity/GNS are textbook BUT the causal
pathway packer-length-sort->domain-correlated-rows->GNS is not, + Krell argues the OPPOSITE); ★ #10 L0-COULD-FAIL: ratio
is parameter-DEPENDENT w/ 3 null exits — (A) length _|_ domain -> ratio~1; (B) within-PACK averaging (each row = several
docs) washes out domain-homogeneity at batch level -> ratio~1 (which effect wins is emergent, the STRONGEST residual
risk -> moderate green prob); (C) sign-flip ratio<1 if length-homogeneous batches have lower grad-norm variance. Anti-
circular: FROZEN identical model across both arms (only batch composition differs -> any GNS diff is purely composition,
not weights); GT = domain labels (harness/corpus), metric reads gradients only. Honest-negative: ratio <=~1.05 at
realistic buffer -> Krell's 'no impact' extends to the ordering axis -> clean negative. ORCHESTRATOR BOUNDARY-CHECK
(scout-flagged): distinct from OCCUPIED CLAIM-0051 (streaming shuffle-buffer variance-vs-RUN-LENGTH; RR/GraB incumbent;
batch-mean-gradient-variance metric) — THIS is length-sorted-PACKER domain-co-location -> GNS/effective-batch tax; Krell-
packing incumbent; GNS currency. Different mechanism/incumbent/metric. L1: real 100-300M pretraining fixed token budget
both arms matched nominal batch -> loss-vs-tokens + steps-to-target (sorted ~ smaller effective batch) + sweep shuffle-
buffer to find where the gap closes (production recommendation: min buffer for length-sorted packers).

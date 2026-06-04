# PRE-REGISTRATION — EXP-0064 (CLAIM-0056)
researcher-0062 | PROJ-0026 | TASK-0054 | committed BEFORE running.

## CLAIM
Length-sorted greedy sequence packing (SPFHP / best-fit-decreasing — the standard production packer)
inflates per-step gradient-noise-scale (GNS, McCandlish B_simple = tr(Sigma)/||g||^2) versus
globally-shuffled packing, BECAUSE document length correlates with domain, so same-length docs
(=same-domain) co-locate in the same packed row and thus the same minibatch, collapsing within-batch
domain diversity.
HEADLINE: GNS_sorted / GNS_shuffled >= 1.3 at a realistic shuffle buffer.

EMPIRICAL-PHENOMENON. Selected because it CLEARS killer #10: the headline ratio is genuinely
uncertain + parameter-dependent (within-pack averaging may neutralize it). Run HONESTLY; report
whichever way it comes out. Negatives are WINS.

## CORPUS (REAL TEXT — stated)
On-disk REAL text, 4 domains with naturally DIFFERENT length distributions (no injected correlation):
  - CODE       : Python stdlib *.py source files (functions/snippets)         [variable, code tokens]
  - MAN1       : /usr/share/man/man1 troff prose (command manuals)            [medium-long prose]
  - MAN5       : /usr/share/man/man5 troff prose (file-format manuals)        [short-medium prose]
  - DOCSTRING  : docstrings extracted from stdlib *.py (natural-language doc)  [short-medium]
Target ~3000-6000 docs total across domains. The length<->domain correlation is whatever the REAL
corpus produces — MEASURED, not asserted.
Tokenization: whitespace+punct stdlib tokenizer (no torch/numpy available — PURE STDLIB).
Tiny per-token vocab hashed to a fixed embedding table (frozen) — see model.

## TWO ARMS (identical packer + identical masking; differ ONLY in row emission order)
Packer = SPFHP-style best-fit-decreasing into fixed-length rows (MAXLEN tokens):
  sort docs by length DESC, greedily place each into the first row with room, else open new row.
Both arms produce the SAME set of packed rows (same token efficiency, same masking).
  ARM A SORTED   : emit packed rows in packer order (length-sorted).
  ARM B SHUFFLED : emit packed rows after GLOBAL shuffle with a FINITE shuffle buffer.
SHUFFLE-BUFFER SWEEP: buffer in {1k, 10k, inf} rows (inf = full shuffle). Realistic = 10k.

## ANTI-CIRCULAR GUARD (critical)
ONE FROZEN tiny model used IDENTICALLY across BOTH arms. Model = frozen token-embedding table
(hashed vocab -> D-dim, fixed random init, seed-frozen) + frozen linear head to vocab; per-row loss
= next-token cross-entropy (mean over row positions, attention-masked at doc boundaries). Gradient
taken w.r.t. a SINGLE trainable parameter block (the embedding table) so per-minibatch gradients are
real, comparable, and CHEAP (pure-stdlib analytic CE gradient — STATED below). Because weights are
IDENTICAL between arms, ANY GNS difference is PURELY batch composition, NOT weights.
GT = domain labels (corpus-owned). The GNS metric reads ONLY gradients; domain labels used only for
diagnostics (entropy/MI), never to compute the gradient.

GRADIENT (pure stdlib, exact for this model): softmax cross-entropy over the frozen linear head;
dL/dE[token] accumulated analytically. We use a SHARED frozen head W (vocab x D) and treat E (vocab x D)
as the trainable block. Gradient vector g = flattened dL/dE. This is a REAL gradient of a real loss
on a real frozen model — no proxy fabrication. (If numpy/torch were importable we'd use them; they are
NOT on this machine -> pure-stdlib lists/array module.)

## GNS ESTIMATOR (McCandlish 1812.06162 B_simple)
For each arm + each buffer setting:
  - Partition emitted rows into minibatches of size MB rows.
  - Per minibatch i: gradient g_i (mean over rows in the batch).
  - Full-batch gradient g_full = mean over ALL rows (arm-independent in content; identical set).
  - tr(Sigma) estimated from the variance of per-minibatch gradient estimates:
      tr(Sigma) ~ (1/(N-1)) * sum_i ||g_i - g_bar||^2 * MB   (per-example trace scaling)
    using the standard two-batch-size or variance-of-means estimator; we use variance-of-means:
      B_simple = tr(Sigma) / ||g_full||^2 with tr(Sigma) = MB * mean_i ||g_i - g_bar||^2.
  - Report GNS per arm, then RATIO GNS_sorted/GNS_shuffled with bootstrap 95% CIs over minibatches.
g_full content is identical across arms (same rows); only the PARTITION INTO MINIBATCHES differs,
which is exactly the batch-composition effect under test.

## THE THREE NULL EXITS (killer #10 — MUST explicitly rule out or report)
(A) length _|_ domain: MEASURE corpus length<->domain MUTUAL INFORMATION (bits). If MI ~ 0, same-length
    co-location does NOT imply same-domain -> ratio ~1.0. Report MI + per-domain length histograms.
(B) WITHIN-PACK AVERAGING (strongest residual risk): each row averages SEVERAL docs; this may wash out
    domain homogeneity at BATCH level even if length<->domain correlate. Report mean docs-per-pack +
    realized within-batch domain ENTROPY sorted-vs-shuffled. Which effect wins is EMERGENT -> MEASURE.
(C) sign-flip: ratio < 1 if length-homogeneous batches have lower gradient-norm variance. Sign not guaranteed.

## DIAGNOSTICS
- length<->domain MI (bits) + normalized MI.
- mean docs-per-pack (+ distribution).
- within-batch domain entropy: sorted vs shuffled (mean over minibatches), per buffer.
- per-domain token-length histograms.

## DECISION RULE (frozen)
- HELD          : GNS ratio >= ~1.3 at realistic buffer (10k) AND sorted has LOWER within-batch domain
                  entropy AND effect persists at finite buffer.
- HONEST-NEGATIVE: ratio <= ~1.05 at realistic buffer -> report WHICH exit (B within-pack averaging /
                  A low MI / C sign-flip<1.0). DO NOT force a positive.
- PARTIAL       : ratio between 1.05 and 1.3.

## BUDGET: CPU-only, SERIAL (multiprocessing BLOCKED), <= 15 min.
## OUTPUT: RESULTS.md + CSVs (gns_by_buffer, entropy_by_buffer, length_hist, mi). Honest reporting.

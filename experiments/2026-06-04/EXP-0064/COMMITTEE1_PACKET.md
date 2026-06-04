# COMMITTEE#1 — CLAIM-0056 (PROJ-0026, data-systems-for-ml) — length-sorted packing inflates GNS (effective-batch tax)
## EMPIRICAL-PHENOMENON, effect=keep-exploring/PARTIAL. NOT metric-validity (GNS measured from REAL gradients, behavioral). NO closed-form headline. Anti-circular (FROZEN identical tiny model across both arms -> any GNS diff = purely batch composition). Vote HONESTLY by role.

## CLAIM: length-sorted greedy packing (SPFHP/best-fit-decreasing, standard production packer) inflates per-step GNS (McCandlish B_simple) vs globally-shuffled packing, because document length correlates with domain -> same-length=same-domain docs co-locate in the same packed row + thus minibatch -> collapses within-batch domain diversity -> effective batch < nominal (a data-parallelism tax the seminal packing paper's 'without impacting performance' = ATTENTION-axis-only claim doesn't cover). Headline target was >=1.3x.

## L0 RESULT — PARTIAL (cleared killer-#10: the L0 COULD have failed, and a null exit partially DID):
GNS_sorted/GNS_shuffled @ realistic 10k buffer: 1.220 CI[1.081,1.367] (MAXLEN128, docs/pack 2.0) -> 1.165 (256, dpp3.1) -> 1.098 CI-incl-1.0 (512, dpp5.8). MONOTONE DECAY with docs-per-pack = the finding. Realistic-regime 1.10-1.22: ABOVE the 1.05 noise floor, BELOW the 1.3 headline -> PARTIAL.
THE 3 NULL EXITS ADJUDICATED: (A) length _|_ domain RULED OUT (corpus length<->domain MI=0.232 bits, NMI 0.171); (B) WITHIN-PACK AVERAGING TRIGGERS = the DOMINANT MODERATOR (dpp5.8 -> ratio 1.10 CI-incl-1.0; entropy gap shrinks 1.147 vs 1.182) — the predicted strongest residual risk, MEASURED, it bounds the effect; (C) sign-flip RULED OUT (ratio>1 everywhere).
MECHANISM CONFIRMED: sorted batches have LOWER within-batch domain entropy at EVERY setting (1.016 vs 1.144 @MAXLEN128) — the hypothesized pathway holds; magnitude throttled by within-pack averaging. REAL on-disk corpus (3329 docs, 4 domains, natural length spread), pure-stdlib, FROZEN tiny model (anti-circular).

## THREE THINGS TO STRESS-TEST: (a) is a BOUNDED 1.10-1.22x (vs the 1.3 target), confined to the LOW-docs-per-pack regime (short-seq/long-tail-length corpora) + decaying to ~1.0 as packs get dense (dpp>5), candidate-grade — or too small/regime-narrow to matter (production pretraining often packs DENSE)? (b) is the GNS inflation on a FROZEN tiny analytic-CE model representative of a MID-TRAINING real model (the researcher flags regime-dependence)? (c) NOVELTY vs Krell — Krell's 'without impacting performance' is explicitly the ATTENTION cross-contamination axis; is the batch-composition/effective-batch axis genuinely uncovered, or implied by McCandlish-IID + general knowledge that sorted batches aren't IID?

## CLAIM YAML
claim: "Length-sorted greedy sequence packing (SPFHP/best-fit-decreasing, the standard\
  \ production packer) inflates the per-step gradient noise scale (GNS, McCandlish\
  \ B_simple=tr(Sigma)/||g||^2) versus globally-shuffled packing, because document\
  \ length correlates with domain so same-length->same-domain documents get co-located\
  \ in the same packed row and thus the same minibatch, collapsing within-batch domain\
  \ diversity. At a fixed token budget, length-sorted packing yields a measurably\
  \ LARGER GNS (>=1.3x in the realistic regime) than shuffle-then-pack \u2014 meaning\
  \ its EFFECTIVE batch size is smaller than its nominal batch size, a hidden data-parallelism\
  \ tax that the seminal packing paper's 'without impacting performance' claim (which\
  \ concerns only the attention cross-contamination axis) does not cover."
why_it_matters: "FRESH AREA (data-systems: sequence-packing ORDERING axis). EMPIRICAL-phenomenon,\

## L0 RESULTS (EXP-0064)
# RESULTS — EXP-0064 / CLAIM-0056
**Length-sorted greedy packing inflates per-step GNS vs globally-shuffled packing — PARTIAL (mechanism confirmed, magnitude below 1.3 headline; within-pack averaging [null exit B] is the dominant moderator).**
researcher-0062 | PROJ-0026 | TASK-0054 | L0 CPU-only, pure-stdlib, SERIAL | run.py, prereg committed before.

## VERDICT: PARTIAL (lean-positive on mechanism, negative on the >=1.3 headline)
Ratio GNS_sorted/GNS_shuffled lands **1.10–1.22** at realistic buffer — above 1.05, below the 1.3 headline.
The mechanism (null exit A & C ruled out; entropy direction correct) is REAL and CONFIRMED, but **null
exit B (within-pack averaging) is the dominant moderator** and progressively neutralizes the effect as
docs-per-pack grows. Honest reporting per the pre-registered decision rule.

## CORPUS (REAL on-disk text — stated)
3329 real docs, 4 domains with naturally different length distributions (NO injected correlation):
- CODE      (Python stdlib *.py def/class blocks): 1585 docs, mean 114.8 tok
- DOCSTRING (triple-quoted strings from stdlib)  : 1471 docs, mean  54.2 tok  (SHORT)
- MAN1      (/usr/share/man/man1 troff)          :  253 docs, mean 110.9 tok
- MAN5      (/usr/share/man/man5 troff)          :   20 docs, mean 218.1 tok  (LONG)
Pure-stdlib tokenizer (regex word/punct). No numpy/torch on machine -> pure stdlib lists/array.

## ANTI-CIRCULAR GUARD (honored)
ONE frozen tiny model used IDENTICALLY across both arms & all MAXLENs: frozen hashed-vocab embedding
table E (V=1024,D=8, trainable block) + frozen linear head W; per-row next-token softmax-CE over a frozen
K=12 candidate set; exact analytic dL/dE gradient (real gradient of a real loss). Weights IDENTICAL between
arms -> every GNS difference is PURELY batch composition. Domain labels feed diagnostics only, never the gradient.

## HEADLINE TABLE — GNS_sorted/GNS_shuffled vs shuffle-buffer & docs-per-pack
The MAXLEN sweep is the docs-per-pack lever = the direct test of NULL EXIT B (within-pack averaging).

| MAXLEN | mean docs/pack | buffer | GNS_sorted | GNS_shuf | RATIO | 95% CI        | ent_sorted | ent_shuf |
|--------|----------------|--------|-----------|----------|-------|---------------|-----------|----------|
| 128    | 2.00           | 1k     | 7.96      | 6.65     | 1.198 | [1.042,1.342] | 1.016     | 1.141    |
| 128    | 2.00           | 10k    | 7.96      | 6.52     | **1.220** | **[1.081,1.367]** | 1.016 | 1.144 |
| 128    | 2.00           | inf    | 7.96      | 6.52     | 1.220 | [1.081,1.367] | 1.016     | 1.144    |
| 256    | 3.09           | 1k     | 5.82      | 4.83     | 1.206 | [0.960,1.619] | 1.056     | 1.170    |
| 256    | 3.09           | 10k    | 5.82      | 5.00     | 1.165 | [0.985,1.485] | 1.056     | 1.162    |
| 256    | 3.09           | inf    | 5.82      | 5.00     | 1.165 | [0.985,1.485] | 1.056     | 1.162    |
| 512    | 5.79           | 1k     | 3.37      | 3.07     | 1.098 | [0.772,1.545] | 1.147     | 1.182    |
| 512    | 5.79           | 10k    | 3.37      | 3.07     | 1.098 | [0.772,1.545] | 1.147     | 1.182    |
| 512    | 5.79           | inf    | 3.37      | 3.07     | 1.098 | [0.772,1.545] | 1.147     | 1.182    |

**The monotone trend IS the finding:** ratio 1.22 -> 1.17 -> 1.10 as docs/pack 2.0 -> 3.1 -> 5.8.
At low averaging (MAXLEN=128, dpp=2.0, realistic 10k buffer) the effect is **real and significant**
(ratio 1.22, CI excludes 1.0). As pack density rises, within-pack averaging washes out the domain
homogeneity and the ratio decays toward 1.0 — exactly the predicted strongest null exit (B).

## THE THREE NULL EXITS — explicitly adjudicated
- **(A) length _|_ domain — RULED OUT.** length<->domain MI = **0.232 bits**, NMI = 0.171, H(domain)=1.357.
  Correlation is real (MAN5 long ~218 tok, DOCSTRING short ~54 tok, CODE/MAN1 medium ~111). Not null-A.
- **(B) within-pack averaging — TRIGGERS at production pack density (the dominant moderator).** Mean docs/pack
  = 5.79 at MAXLEN=512 collapses the ratio to 1.10 (CI includes 1.0) and the entropy gap to 1.147 vs 1.182.
  At dpp=2.0 the effect survives (1.22). **Which effect wins is emergent and pack-density-dependent — MEASURED, not assumed.**
- **(C) sign-flip — RULED OUT.** Ratio > 1.0 at every point (sorted GNS always >= shuffled). No sign flip.

## MECHANISM CONFIRMED (entropy)
Sorted batches have LOWER within-batch domain entropy than shuffled at every setting (e.g. 1.016 vs 1.144
at MAXLEN=128). Length-sort co-locates same-length=same-domain docs in the same minibatch, reducing batch
domain diversity -> higher gradient variance -> higher GNS. The pathway is exactly as hypothesized; the
magnitude is just throttled by within-pack averaging.

## SHUFFLE-BUFFER
1k vs 10k vs inf are near-identical here (corpus = 575–1668 rows, so 10k buffer ~ full shuffle; 1k differs
slightly at MAXLEN=128 where rows>1k: 1.198 vs 1.220). Buffer is NOT the binding constraint at this scale —
pack density is. L1 must sweep buffer at production row counts (millions) where finite buffer bites.

## DECISION (frozen rule)
Realistic regime (10k buffer): ratio 1.10 (dpp=5.79) to 1.22 (dpp=2.0). >1.05 but <1.3 => **PARTIAL.**

## PRE-REG
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

## ORCHESTRATOR NOTE: PRIOR-ART VERIFIED — Krell 2107.02027 SPFHP/NNLSHP 'without impacting performance' = ATTENTION axis only (silent on batch-composition); McCandlish 1812.06162 B_simple ASSUMES IID minibatches (the assumption length-sort breaks); 2408.09621 (perplexity only); 2512.14427 (cross-doc reasoning only). Novelty = the packer-length-sort -> domain-correlated-batches -> GNS-inflation pathway = an effective-batch tax Krell doesn't cover. The L0 genuinely CLEARED killer-#10 (uncertain outcome, one null exit partially triggered + bounded the effect). If candidate-grade, L1: real 100-300M pretraining fixed token budget both arms matched nominal batch -> loss-vs-tokens + steps-to-target + sweep docs-per-pack (the binding lever — low dpp = largest gap) + shuffle-buffer at production row counts (millions). If you judge the bounded 1.10-1.22x is too regime-narrow OR the frozen-tiny-model GNS won't transfer to mid-training OR not novel enough vs Krell+McCandlish, YELLOW/RED honestly. Real 6/6 by role.

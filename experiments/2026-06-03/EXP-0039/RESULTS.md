# RESULTS — EXP-0039 / CLAIM-0041

**Researcher:** researcher-0039 | L0 (CPU-only, stdlib-only, SERIAL, ~20s wall) | 2026-06-03
Lexical token-set **Jaccard** near-dup signal (sentence-transformers/numpy unavailable — STATED in prereg).
Anti-circular: latent `fact_id` is the ONLY ground truth for "duplicate"; the dedup gate reads ONLY surface text.
Raw: `results/amplification.csv` (45 rows), `results/policies.csv` (540 rows), `results/amp_sensitivity` (in log).
5 seeds. Grid: restore∈{.2,.4,.6} × paraphrase∈{0,.3,.6} × horizon∈{long,short} × cap∈{120,200} × thr∈{.3,.5,.7}.

## VERDICT: **PARTIAL** (held only in a tuned/conditional regime; key parts FAIL)

---

## (A) WRITE-AMPLIFICATION — CONDITIONAL, not universally >25%

The main grid used a bounded fact universe (250 facts, T=1000 writes) → universe SATURATES, so
amplification pins at **0.75** for all restore rates. That is an artifact of saturation, not a
clean test. The honest sensitivity run (large universe, no saturation) shows amplification **tracks
the re-store rate**:

| fact universe | restore=0.2 | restore=0.4 | restore=0.6 |
|---|---|---|---|
| 250 (saturates) | 0.75 | 0.75 | 0.75 |
| 1000 / 5000 (no sat.) | **0.197 (<25%)** | 0.399 | 0.601 |

**Honest answer (A):** Write-amplification exceeds 25% **iff** facts recur often (re-store rate ≳ 0.25)
OR the fact universe is small relative to the horizon (saturation). It is **NOT universally >25%** —
at restore=0.2 with a large universe, amplification is only ~20%, BELOW the claimed threshold.
Whether real agent-memory streams clear 25% is an **empirical question for L1** (real MemGPT/Letta/
Generative-Agents logs). The claim's ">25%" is plausible but regime-dependent, not guaranteed.

## (B) DEDUP vs SIZE-CAP vs NO-DEDUP at MATCHED CAP

- **no-dedup uncapped** recall = 1.000 everywhere (keeps everything → unbounded growth; the trivial
  upper bound, not a fair budget competitor). Under a cap it reduces to size-cap mechanics.
- **dedup − size-cap recall delta** (bootstrap 95% CI over per-config means):
  - thr=0.3: mean **+0.013**, CI **[-0.048, +0.072]** — **includes 0** (no win; often LOSES)
  - thr=0.5: mean **+0.103**, CI **[+0.076, +0.130]** — excludes 0 (wins)
  - thr=0.7: mean **+0.113**, CI **[+0.084, +0.144]** — excludes 0 (wins)
  - ALL configs pooled: mean **+0.076**, CI **[+0.049, +0.101]** — excludes 0
- Best regime (paraphrase=0, long-horizon, cap=120, thr=0.5): per-seed delta CI **[+0.090, +0.142]**.
- dedup beats size-cap by >0.01 in **90/108** configs — but **LOSES** (negative delta) in 18 configs,
  concentrated at **thr=0.3 + short-horizon** (e.g. -0.31, -0.29, -0.27): a loose gate FALSE-DEDUPS,
  collapsing distinct facts (gate precision only **0.37** at thr=0.3) and dropping needed memories.

**So: dedup beats size-cap at matched size ONLY with a well-chosen threshold (≥0.5).** This is the
load-bearing bar and dedup CLEARS it in the tuned regime — but the win is NOT threshold-robust, and
the prereg explicitly screened against "tune a knob." The threshold IS a knob here. Partial credit.

## Gate precision/recall (lexical vs fact_id) + ORACLE gap

- Gate precision mean **0.752**, recall mean **0.839** (over thr 0.3–0.7). At thr=0.3 precision craters
  to ~0.37 (false dedup); at thr=0.7 precision ~1.00 but recall falls (esp. under paraphrase: 0.38–0.54
  at paraphrase=0.6) — the classic precision/recall tradeoff the lexical signal cannot escape.
- **ORACLE gap** (oracle reads fact_id; dedup reads text): oracle−dedup recall mean **+0.120**, max **+0.795**.
  The lexical gate leaves LARGE headroom vs ideal content-dedup — and in short-horizon at thr=0.3 the
  gate is so much worse than oracle that dedup underperforms even size-cap. A real embedding gate (L1)
  would close part of this gap but paraphrase still defeats surface signals partially.

## Where dedup LOSES (honest negatives — the load-bearing failures)
1. **Low threshold (0.3):** false-dedup collapses distinct facts → recall BELOW size-cap. CI includes 0.
2. **Short-horizon + large cap + loose gate:** size-cap already retains the recent facts queries need,
   so dedup's "save slots for old facts" advantage is wasted, and false-dedup hurts → dedup loses.
3. **High paraphrase (0.6):** gate recall drops to ~0.4–0.5 → dedup catches few true dups → its edge
   over size-cap shrinks toward the oracle gap; in some configs near-zero (+0.005, +0.006).

## CLAIM DISPOSITION
- (A) ">25% redundant writes": **NOT universally true** — holds only when re-store rate ≳25% or universe saturates. CONDITIONAL.
- (B) "dedup beats BOTH no-dedup AND size-cap at matched size": **HOLDS in the tuned regime (thr≥0.5)**
  with CI excluding 0, but **FAILS at loose threshold and in short-horizon/high-paraphrase regimes**, and
  the win requires choosing the threshold (a knob). dedup never reaches the oracle (large content-signal gap).
- **Net: PARTIAL.** Content-dedup CAN beat age-eviction at matched size, but only with a tuned threshold
  and a recall-horizon that values old facts; it is not a free, robust, knob-free win. Size-cap is a
  stronger baseline than the claim assumed: it ties or beats dedup whenever the gate is loose, paraphrase
  is high, or queries want recent facts.

## What a real L1 should measure
- Real agent-memory traces (MemGPT/Letta conversation+archival logs, Generative-Agents reflection streams):
  measure the **real re-store/amplification rate** — is it actually >25%? (This sim shows it's only >25%
  if facts genuinely recur that often.)
- Swap the lexical Jaccard gate for a **real sentence-embedding cosine** gate; re-measure gate precision/
  recall and the oracle gap (embeddings should shrink but not eliminate the paraphrase-driven gap).
- Real **downstream task recall** (does the agent still answer queries needing old facts?) under dedup vs a
  size-cap (recency) AND an importance/LRU eviction baseline — at matched store size.
- Sweep threshold per-corpus; report whether a single robust threshold exists or it must be tuned (the
  knob concern). Test against importance-weighted eviction, not just pure recency.

## PRIOR-ART CAVEAT
RAG/datastore dedup is on RETRIEVAL corpora (read path) — well studied. Agent **memory** systems (MemGPT/
Letta, Generative-Agents reflection/importance) ARE published and DO manage write/eviction. Novelty here is
narrow: characterizing **write-path amplification** + asking whether **pre-write content-dedup beats
recency size-cap at matched recall**. Our L0 says: only conditionally, and it's threshold-sensitive — so
the contribution, if any, is the *negative-leaning characterization* (size-cap is a strong baseline;
content-dedup is not a robust free win), not a new winning mechanism.

# COMMITTEE#1 — CLAIM-0041 (PROJ-0012, retrieval-and-memory — FIRST claim in the EXPANDED fresh topic-bias)
## MEASUREMENT/characterization study, effect=keep-exploring / PARTIAL (negative-leaning). LIGHTWEIGHT posture: one sharp claim per fresh area. Screened vs all 3 anti-patterns + anti-circularity. Vote honestly. novelty_killer: agent memory systems (MemGPT/Letta, Generative-Agents reflection/importance) ARE published and DO manage eviction; RAG/datastore dedup is the READ path. The narrow claimed novelty = WRITE-PATH amplification characterization + pre-write dedup BEATING a recency size-cap at matched recall.

## L0 FINDINGS (anti-circular: latent fact_id = duplicate GT; gate reads surface text only; env: lexical Jaccard, no embeddings):
(A) Write-amplification is CONDITIONAL, NOT universally >25%: it TRACKS the re-store rate (0.197<25% @restore=0.2; 0.399@0.4; 0.601@0.6); only clears >25% at restore>=~0.25 OR a saturated fact-universe. The main-grid 0.75 was a saturation ARTIFACT (researcher flagged honestly).
(B) dedup vs SIZE-CAP eviction at MATCHED size (the load-bearing bar): dedup-minus-size-cap recall delta CLEARS only with a TUNED threshold >=0.5: thr0.3 +0.013 CI[-0.048,+0.072] INCLUDES 0 (and LOSES short-horizon to -0.31 — a loose gate false-dedups and collapses distinct facts); thr0.5 +0.103 CI[+0.076,+0.130]; thr0.7 +0.113 CI[+0.084,+0.144]. Wins 90/108 configs but LOSES 18/108. THE THRESHOLD IS A KNOB (the prereg explicitly screened vs Jensen-floor) -> the win is conditional/knob-tuned/horizon-dependent, NOT robust/free.
Gate precision 0.75 / recall 0.84 overall (precision craters to 0.37 @thr0.3; recall 0.38-0.54 under high paraphrase @thr0.7). ORACLE(fact_id) - dedup recall gap mean +0.12 / max +0.80 — lexical signal leaves large headroom, never reaches ideal.

## HONEST SYNTHESIS: content-dedup CAN beat age-eviction at matched size, but only with a tuned threshold AND a recall-horizon that values old facts. SIZE-CAP is a STRONGER baseline than the claim assumed — it ties/beats dedup whenever the gate is loose, paraphrase is high, or queries want recent facts. Neither cleanly held nor killed. Negative-leaning.

## CLAIM
claim: "In long-horizon agent memory systems, the write path WRITE-AMPLIFIES \u2014\
  \ a non-trivial fraction (>25%) of memory writes are semantically REDUNDANT (the\
  \ agent re-stores a fact equivalent to one already in its store, because writes\
  \ are not deduplicated) \u2014 AND a cheap pre-write semantic-dedup gate (embed-and-near-dup-check\
  \ the candidate write against existing memories, NO LLM call) cuts memory-store\
  \ GROWTH by a non-trivial fraction at MATCHED downstream task-recall, beating BOTH\
  \ (a) no-dedup append-everything AND (b) a recency/size-cap eviction baseline at\
  \ matched store size \u2014 because redundant re-stores are common and detectable\
  \ pre-write, and a size-cap (which evicts by age, not content) discards still-needed\
  \ old memories that dedup would have kept."
why_it_matters: "FRESH AREA (retrieval-and-memory \u2014 first claim in the expanded\

## L0 RESULTS (EXP-0039)
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

## PRE-REG (committed pre-run e941521)
# PRE_REGISTRATION — EXP-0039 / CLAIM-0041

**Researcher:** researcher-0039 | **Project:** PROJ-0012 | **Task:** TASK-0031
**Level:** L0 (CPU-only, stdlib-only, SERIAL, ≤15 min) | **Date:** 2026-06-03
**Committed BEFORE running.** Honest pipeline — negatives are WINS.

## THE CLAIM (CLAIM-0041)
In long-horizon agent memory systems, the write path WRITE-AMPLIFIES — a non-trivial
fraction (>25%) of memory writes are semantically REDUNDANT (re-storing a fact equivalent
to one already held) — AND a cheap pre-write semantic-dedup gate (embed-and-near-dup-check
the candidate write vs existing memories, NO LLM call) cuts memory-store GROWTH at MATCHED
downstream task-recall, beating BOTH (a) no-dedup append-everything AND (b) a recency/size-cap
eviction baseline at matched store size — because a size-cap evicts by AGE not CONTENT and
discards still-needed old memories that dedup would keep.

Two falsifiable parts:
- (A) Is there material write-amplification (>25% semantically-redundant writes)?
- (B) Does cheap pre-write dedup cut store GROWTH at MATCHED task-recall, beating BOTH
      no-dedup AND size-cap eviction at matched store size?

## EMBEDDING / DEDUP SIGNAL (STATED)
sentence-transformers / numpy are NOT available on this Mac (confirmed). Per L0 scope we use a
DETERMINISTIC LEXICAL near-dup signal: each memory's text is tokenized into a word set; the
near-dup signal between two memories is **token-set Jaccard similarity** (|A∩B|/|A∪B|). The
dedup gate fires (skips write) iff max Jaccard vs any stored memory ≥ THRESHOLD. This is a
content-overlap proxy for embedding cosine. We report the gate's real precision/recall vs the
latent fact-id ground truth, so the lexical-vs-embedding gap is measured honestly (a real L1
would swap in true embeddings).

## ANTI-CIRCULARITY (load-bearing)
- Each memory carries a HIDDEN latent `fact_id`. A write is TRULY redundant iff its fact_id is
  already present in the store. This is the ONLY ground truth for "duplicate".
- The dedup GATE reads ONLY the surface text (Jaccard near-dup), NEVER the fact_id.
- ORACLE gate reads the fact_id directly (perfect dedup) — used to bound the gap between the
  cheap content signal and ideal dedup.

## ORCHESTRATOR NOTE: LIGHTWEIGHT posture — if this is candidate-grade, the L1 ask is real MemGPT/Letta/Generative-Agents traces (real re-store rate — does it clear 25%?) + a REAL sentence-embedding dedup gate + real downstream task-recall vs recency-cap AND LRU/importance eviction at matched size. But if the committee judges 'tuned-knob win over a strong size-cap baseline + amplification-is-an-artifact', converge it and move to the next fresh area (don't deep-mine PROJ-0012).

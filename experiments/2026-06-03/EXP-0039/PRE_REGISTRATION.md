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
- We report gate precision (of skipped writes, fraction that were true dups) and recall
  (of true-dup writes, fraction the gate caught), plus oracle gap on the (size, recall) frontier.

## WRITE-STREAM MODEL (long-horizon agent memory)
- A universe of N_FACTS latent facts. Stream of T writes over "time".
- Each write: with prob (1 - RESTORE_RATE) a NEW fact (fresh fact_id, fresh text);
  with prob RESTORE_RATE a RE-STORE of a previously-seen fact (write-amplification).
- A re-stored fact's surface text is a PARAPHRASE of the original with prob PARAPHRASE_RATE
  (different tokens → lexical gate may MISS it) else near-identical text (gate catches easily).
  Paraphrase = drop/substitute a fraction of tokens + add filler tokens, fact_id UNCHANGED.
- True write-amplification rate (A) = fraction of writes that re-store an already-stored fact_id.

## QUERIES / TASK-RECALL
- After the write stream, QUERIES each need a specific past fact_id. Needed fact_ids are drawn
  to target a RECALL_HORIZON: queries preferentially need facts written H steps ago (old facts),
  to stress AGE-based eviction. task-recall = fraction of queries whose needed fact_id is STILL
  PRESENT in the store (any memory with that fact_id).

## THREE POLICIES (matched store cap)
- (a) NO-DEDUP append-everything: write every candidate. Under a cap, evict oldest when full
      (so it fills the cap with dup copies → wastes budget).
- (b) SIZE-CAP eviction: cap CAP, evict OLDEST when full (recency). Evicts by AGE, can drop a
      still-needed OLD fact while keeping recent dup copies. THE HONEST STRONG BASELINE.
- (c) PRE-WRITE DEDUP: before writing, if max-Jaccard vs store ≥ THRESHOLD, SKIP the write
      (no new slot consumed). Still capped at CAP with oldest-eviction on overflow — but dedup
      means fewer slots wasted on dups → fewer evictions → old needed facts survive.
  All three operate at the SAME cap CAP (matched store size). (a) and (b) differ only in that
  (a) is effectively (b) when CAP binds; we keep (a) as an UNCAPPED-growth reference too:
  report (a) both uncapped (to show growth) and capped (== b mechanics) — the load-bearing
  comparison is (c) DEDUP vs (b) SIZE-CAP at matched CAP.

## METRICS
- A: true write-amplification rate (latent fact-id re-store fraction).
- Store GROWTH: distinct slots used over time; for uncapped no-dedup = total writes.
- task-recall per policy at matched CAP.
- DEDUP − SIZE-CAP recall delta at matched CAP (the crux), bootstrap 95% CI over seeds.
- Gate precision/recall (lexical vs fact_id) + ORACLE (fact_id) gap.

## SWEEPS
- RESTORE_RATE ∈ {0.2, 0.4, 0.6}
- PARAPHRASE_RATE ∈ {0.0, 0.3, 0.6}  (dedup detectability degrades as paraphrase rises)
- RECALL_HORIZON ∈ {short, long} (how old needed facts are)
- CAP ∈ {a few values relative to distinct facts}
- THRESHOLD ∈ {0.3, 0.5, 0.7}
- SEEDS ≥ 5; bootstrap CI on dedup-minus-sizecap recall delta at matched CAP.

## DECISION RULES (pre-committed)
- HELD: (A) amplification >25% in realistic (restore>0) streams, AND (B) DEDUP beats BOTH
  no-dedup AND size-cap on the (size, recall) frontier at matched CAP — specifically
  dedup-minus-sizecap recall delta CI excludes 0 (positive) at matched size.
- PARTIAL: amplification confirmed but dedup only ties size-cap (delta CI includes 0) OR dedup
  wins only in a narrow regime (e.g. low paraphrase only).
- NEGATIVE (still a WIN to report): amplification <25% in realistic streams, OR cheap dedup
  LOSES recall (false-dedup drops a needed memory: gate precision low so it skips a non-dup, or
  collapses distinct facts), OR SIZE-CAP eviction already matches dedup growth+recall (content-
  dedup adds nothing over age-eviction → content-dedup unjustified).

## HONEST-NEGATIVE BRANCH
If size-cap matches dedup at matched size, we state plainly: content-dedup is just a worse/equal
cap and is unjustified. Beating SIZE-CAP at matched size is the LOAD-BEARING bar.

## PRIOR-ART CAVEAT
RAG/datastore dedup is on RETRIEVAL corpora (read path). Memory systems (MemGPT/Letta,
Generative-Agents reflection) ARE published. Novelty here = WRITE-PATH amplification
characterization + pre-write dedup BEATING size-cap at matched recall. Memory systems exist;
we are not claiming to invent agent memory.

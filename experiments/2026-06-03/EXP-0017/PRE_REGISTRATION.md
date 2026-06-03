# PRE-REGISTRATION — EXP-0017 (L0, CLAIM-0013, PROJ-0001)
researcher-0017 | committed BEFORE running | honest pipeline (negative/insufficient = WIN)
Node: cli:dengcchi-mac | CPU-only, stdlib-only (Python 3.9.6, no numpy), SERIAL (multiprocessing BLOCKED). Trust on-disk CSVs.

## THE CLAIM (CLAIM-0013)
"In long-horizon agents with external memory/RAG, a non-trivial fraction (>20%) of retrieval calls are
REDUNDANT — they return content already present in the live context window — AND a cheap pre-retrieval
check (lexical/embedding overlap of the query vs in-context spans, NO extra model call) can identify a
meaningful share BEFORE issuing the retrieval, skipping them to cut retrieval latency + injected-token
cost WITHOUT harming task accuracy."

This is a MEASUREMENT/CHARACTERIZATION study. TWO falsifiable parts:
- (A) the redundant-retrieval FRACTION as a function of workload.
- (B) a cheap NON-ORACLE check's precision/recall/AUC + the accuracy-safety of skipping at its real errors.

## SCOPE / HONESTY ABOUT DATA (workload-conditionality)
Real long-horizon agent+RAG traces with ground-truth "is this answer already in-context" labels are NOT
trivially installable offline on this Mac (no network egress assumed, stdlib-only). So this L0 is a
**model-based characterization on a CONSTRUCTED trace generator**, with redundancy reported AS A FUNCTION
of the assumed workload (NOT a false universal). The generator is parameterized; we sweep the parameters
and report conditionality. A real L1 must use real traces + a real embedding check + real task accuracy.

## TRACE / CORPUS MODEL (the generative process — independent of the check's features)
A long-horizon agent runs T turns. It holds a LIVE CONTEXT WINDOW = a bounded deque of the last W spans
(retrieved-content spans + turn outputs). At each turn the agent may issue a retrieval query q_t that
targets a "need" — a specific information item (one of N corpus items). The retrieval returns the matching
corpus span s_t.

GROUND-TRUTH REDUNDANCY (defined INDEPENDENTLY of the cheap check's features, anti-circular):
  A retrieval at turn t is GT-REDUNDANT iff the *target need item* (its underlying semantic id) is ALREADY
  materially present in the live context window at decision time — i.e. an earlier span carrying the SAME
  need-item-id is still resident in the window (not yet evicted). This is a property of the latent item-id
  bookkeeping, NOT of any token/lexical overlap. The cheap check NEVER sees the item-id.

Generative knobs (workload axes, swept):
  - p_repeat : probability a turn's need re-targets a recently-seen item (drives base redundancy).
  - W        : context window size (spans). Larger W => more redundant (item still resident).
  - paraphrase_rate : fraction of re-targeting turns where the *query wording* (and stored span wording)
       is heavily paraphrased vs the original (controls DETECTABILITY by a lexical check — a redundant
       retrieval can be lexically near-dup OR a hard paraphrase). This decouples "is it redundant" (item-id)
       from "is it lexically detectable" so the check's recall is honestly limited.
  - vocab/noise: spans built from a shared vocabulary with per-item keyword cores + filler noise.

Redundancy is a property of item-id resident-in-window; detectability is a separate axis (paraphrase_rate).
This separation is the anti-circularity guard: GT label uses item-id; check uses only realizable text overlap.

## CHEAP CHECK (realizable signals ONLY — NO LLM call, NO item-id)
At decision time, BEFORE retrieving, compute overlap between the QUERY tokens q_t and each in-context span,
take the MAX overlap over resident spans, threshold it. Two cheap signals (both stdlib):
  1. Lexical Jaccard of token sets (and 3-gram Jaccard) between query and span.
  2. Cheap HASHED-EMBEDDING cosine: deterministic feature-hashing of tokens into a fixed-dim vector
     (the "hashing trick", stdlib only — explicitly a cheap surrogate, NOT a learned embedding), cosine.
The check fires "REDUNDANT -> skip" when max overlap >= threshold tau. Sweep tau over a grid.

## METRICS
M_A (redundancy fraction): fraction of retrievals that are GT-REDUNDANT, per workload point. Report vs knobs.
M_B (check quality): precision / recall / F1 and ROC-AUC of the cheap check's score vs GT-redundant label,
     plus the ORACLE (which reads GT label perfectly => AUC 1.0) for the HEADROOM GAP.
M_C (accuracy-safety Pareto): a skip policy skips retrieval when the check fires. Task-success model:
     a turn SUCCEEDS iff the needed item is available to the model at that turn = (we retrieved it) OR
     (it is genuinely already resident in window, i.e. GT-redundant). A WRONG skip = check fires but the
     item was NOT resident (false-positive redundancy) => needed content absent => TASK FAILS.
     We trace (tokens_saved_frac, task_accuracy) as tau sweeps, vs baselines.

## BASELINES (must beat trivial/strong, not strawmen)
  - ALWAYS-RETRIEVE: never skip. accuracy = 1.0 (always has content), tokens_saved = 0. (upper acc bound)
  - NEVER-RETRIEVE: always skip. tokens_saved = max; accuracy = fraction of turns that were GT-redundant.
  - RANDOM-SKIP @ matched skip-rate: skip uniformly at random at the SAME skip rate the check produces at
    each tau (so token savings matched) — THE key comparator. The cheap check is only non-empty if at a
    matched skip-rate it achieves HIGHER task accuracy than random-skip.
  - ORACLE-SKIP: skips exactly the GT-redundant ones (precision=recall=1) => the achievable frontier.

## SEEDS / STATS
>=5 seeds (use 8). Bootstrap 95% CI (>=2000 resamples) on: redundancy fraction; AUC; and the
(accuracy_check - accuracy_random) DELTA at matched skip-rate; and tokens-saved.

## HONEST-NEGATIVE BRANCH (pre-committed)
Report NEGATIVE if ANY of:
  (N1) redundant fraction < 20% across the *realistic* workload band (moderate p_repeat, W) — claim part A fails;
  (N2) the cheap check CANNOT beat random-skip at matched skip-rate (CI on accuracy-delta includes/below 0)
       — the gate is empty (it adds nothing over skipping randomly);
  (N3) skipping at the check's real operating point harms task accuracy beyond a small budget (>2 pts abs
       below always-retrieve at any non-trivial savings) with no safe (savings>0, acc-loss<=budget) point.
PARTIAL if A holds but B is only conditionally useful (detectable only at low paraphrase_rate).
HELD only if A (>20% in realistic band) AND B (beats random-skip, AUC>0.5 clearly, and a safe Pareto point exists).

## PRIOR-ART (must distinguish; adaptive-retrieval IS published — be honest)
Self-RAG, FLARE, SKR ("when to retrieve"), adaptive-RAG, RAG cache/dedup, context-aware retrieval gating
all exist. NOVELTY here is narrow & must be stated as such: the specific *in-context-redundancy* gate —
skip a retrieval because the answer is ALREADY in the live window — measured anti-circularly vs an
independent redundancy GT and vs random-skip at matched rate. We do NOT claim novelty of adaptive retrieval.

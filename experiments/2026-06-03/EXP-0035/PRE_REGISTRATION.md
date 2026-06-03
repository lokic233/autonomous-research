# PRE-REGISTRATION — EXP-0035 / CLAIM-0038
researcher-0035 | L0 (CPU-only, stdlib-only, SERIAL, ≤15 min) | committed BEFORE running.

## CLAIM-0038
In multi-tool LLM agents, wrong-tool-selection errors are PREDICTABLE from the SCHEMA GEOMETRY
of the available tool set alone (pairwise semantic overlap of tool name+desc+params, computed
BEFORE the call, NO model rollout). Selection-error rate rises with max pairwise tool-description
similarity in the active toolset — AND this cheap schema-overlap signal predicts error-prone
toolsets/calls strictly better than (a) random and (b) a generic prompt-difficulty predictor,
AND adds signal BEYOND the agent's own tool-choice logprob/confidence.

## TWO FALSIFIABLE PARTS
- (A) Does pre-call schema-overlap geometry predict wrong-tool-selection with real AUC > chance?
- (B) Does it beat random + generic-difficulty AND add signal BEYOND the agent's self-logprob?

## ENVIRONMENT CONSTRAINT (stated honestly)
No numpy / no transformers / no sentence-transformers on this Mac (Python 3.9.6, stdlib only).
=> Schema-overlap feature uses a DETERMINISTIC LEXICAL/HASHED token-overlap (bag-of-tokens cosine
over name+description+param tokens), NOT a real neural sentence embedding. This is an L0 PROXY for
"semantic overlap". L1 must use real schema embeddings (see L1 plan in RESULTS).

## THE GENERATIVE MODEL (anti-circular by construction)
Each call: a toolset of K tools. Each tool has a SCHEMA (synthetic token bag drawn from latent
"topic" vectors). The CORRECT tool for the call is one specific tool. There is a LATENT
CONFUSABILITY between the correct tool and its nearest distractor in the toolset — this latent
confusability is what DRIVES selection error. The schema-overlap predictor only ever reads the
OBSERVABLE schema tokens (lexical overlap), which is a NOISY readout of latent confusability.

Crucially we SEPARATE three orthogonal latent factors:
  1. CONFUSABILITY c  — latent pairwise similarity of correct tool vs nearest distractor.
                        Drives wrong-tool error. Observable via NOISY schema lexical-overlap.
  2. TASK DIFFICULTY d — intrinsic prompt difficulty, INDEPENDENT (by default) of confusability.
                        Observable via a generic difficulty predictor (noisy readout of d).
  3. AGENT SELF-LOGPROB lp — agent's own choice confidence: a noisy (miscalibratable) readout of
                        BOTH c and d (the agent partly "feels" confusion + difficulty), plus noise.

Selection-error latent logit:  z = b0 + bc*c + bd*d  (+ optional coupling)  ; P(err)=sigmoid(z).
Error label y ~ Bernoulli(P(err)).   <-- y is generated from LATENT c,d, NEVER from schema tokens.

ANTI-CIRCULARITY: the schema-overlap predictor reads ONLY schema token overlap (a noisy proxy of c),
never y, never c directly. Oracle reads true latent c (and gives the oracle-gap ceiling).

## PREDICTORS OF SELECTION ERROR (all scored on held-out calls)
  (a) RANDOM @ matched positive-rate (chance baseline; AUC~0.5).
  (b) GENERIC PROMPT-DIFFICULTY  = noisy readout of d only.
  (c) AGENT SELF-LOGPROB/CONFIDENCE = -lp (low confidence -> high error risk); a separate noisy signal.
  (d) SCHEMA-OVERLAP signal = max (and mean) pairwise lexical schema similarity in active toolset
                              (pre-call, schema-only). PRIMARY predictor.
  ORACLE = true latent confusability c (ceiling; quantifies oracle gap of schema proxy).

## METRICS (the two)
  M1: AUC of each predictor for wrong-tool-selection (ranking metric, threshold-free).
  M2: INCREMENTAL signal of schema-overlap OVER self-logprob:
      delta-AUC = AUC(logprob + schema combined) - AUC(logprob alone).
      Combined score = standardized(-logprob) + standardized(schema_max). (fixed equal-weight, no tuning)
      Also report partial association (schema vs y | logprob bucket).
      Bootstrap 95% CI on delta-AUC and on (AUC_schema - AUC_difficulty).

## SWEEP
  - confusability-vs-difficulty coupling rho in {0.0, 0.5} (independent vs coupled)
  - self-logprob calibration noise sigma_lp in {low, high}
  - toolset size K in {3, 6, 12}
  - schema-proxy noise (lexical readout noise) fixed moderate; overlap distribution via topic draws
  - >= 5 seeds per cell; N calls per cell ~ 4000; bootstrap B=1000 on key deltas.

## DECISION RULE (pre-committed)
  HELD (claim holds) iff ALL:
    - AUC_schema_max > 0.55 (real, > chance) on independent (rho=0) cells, and
    - (AUC_schema - AUC_difficulty) CI lower bound > 0  (beats generic difficulty), and
    - delta-AUC (schema incremental over self-logprob) CI lower bound > 0 (adds beyond logprob).
  PARTIAL iff schema beats random+difficulty but delta-AUC CI includes 0 in some/most cells.
  NEGATIVE iff schema AUC ~ chance, OR doesn't beat difficulty, OR adds nothing beyond self-logprob
    (relabeling — the CLAIM-0015/0037 failure mode), OR requires the oracle (reads c/y) to work.

## HONEST-NEGATIVE BRANCH
If selection error is NOT predictable from schema overlap (AUC~chance), OR schema-overlap doesn't
beat generic difficulty, OR adds nothing beyond the agent's own tool-choice logprob (relabeling),
OR needs an oracle — we REPORT THE NEGATIVE. Negatives/relabeling findings are WINS.

## PRIOR ART CAVEAT
Tool RETRIEVAL (ToolLLM/Gorilla/ToolBench) and tool-disambiguation work exist; tool-selection is
published. NOVELTY tested here: the PRE-CALL SCHEMA-GEOMETRY confusability signal as a selection-
ERROR predictor that adds BEYOND the agent's own self-logprob. We do NOT claim to invent tool selection.

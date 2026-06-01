# PROJ-0008 — Redundant Tool-Call Prefill Tax (interior byte-identical tool re-invocations under exact-prefix KV caching)

**Created:** 2026-06-01 by orchestrator-r6-001 (design committee proj0008_design, 5/5 yellow seed-with-fixes; charter Candidate A; Candidate B REJECTED — ToolCacheAgent/LLM-dCache collision).
**Layer:** prefill-time, within-session interior exact-repeat (3rd distinct miss-mode; distinct from PROJ-0002 edit-invalidation, PROJ-0005 BPE seam, PROJ-0007 cross-session drift).
**First claim:** CLAIM-0018.

## THESIS (RESCOPED per committee — central fix)
On real long-horizon agent trajectories, a measurable fraction of tool invocations are BYTE-IDENTICAL re-invocations of an
earlier same-session call, separated by a large divergent intervening-token span. Each pays a full prefill an EXACT-PREFIX
KV-cache (vLLM APC / SGLang RadixAttention / TensorRT-LLM / provider prompt caching) cannot recover (prefix-caching reuses
only prefixes, never interior repeats). This is a prefill-recompute CHARACTERIZATION on real traces measured against
PRODUCTION-DEPLOYED EXACT-PREFIX caches — NOT a universal structural law and NOT a new caching mechanism.

## SCOPE BOUNDARY (mandatory, committee fix #1+#4) — DO NOT claim "structurally unrecoverable" full stop
Non-prefix interior KV reuse mechanisms EXIST and are published: CacheBlend (2405.16444), PromptCache (2311.04934), LMCache
("any reused text, not necessarily prefix"). The claim is TRUE only against exact-prefix APC/RadixAttention/TensorRT-LLM.
RE-A2 MUST be scoped to "unrecoverable by exact-prefix caching" AND add a second baseline tier: what fraction of interior
repeats would a CacheBlend/LMCache-class non-prefix reuse recover? (Either test it as tier-2 OR state the explicit scope
boundary "this study characterizes the tax under production-deployed exact-prefix caches; non-prefix KV fusion is an open
mechanism we do not implement/evaluate." Silence is not acceptable.)

## FIRST FALSIFIABLE CLAIM (CLAIM-0018, rescoped)
Across >=2 corpora (CC + Codex), within-session byte-identical tool re-invocations = fraction f of total tool-call prefill
tokens (session-clustered 95% CI excludes 0), the tax SURVIVES an exact-prefix KV-cache baseline (>=95% of repeats have
>=1 block of prefix divergence -> exact-prefix reuse recovers 0), AND per-call exact-prefix-non-recoverability +
result-reusability is predicted model-free by tool-output DETERMINISM CLASS over a STRONG baseline. PASS = (a) f CI>0 AND
(b) >=95% repeats exact-prefix-unrecoverable AND (c) determinism-class dAUC 95% LB>0 over the JOINT {token-gap +
tool-frequency + TOOL-IDENTITY one-hot} baseline BOTH corpora.

## PRE-REGISTERED RE GATES (LOCK timestamp BEFORE the run; 7 mandatory committee fixes folded in)
- RE-A1 LOAD-BEARING/KILLER (fix #2): determinism-class dAUC over {token-gap + tool-frequency + TOOL-IDENTITY one-hot} JOINT
  baseline (OR stratify within-tool), 95% LB>0 BOTH corpora. Determinism class is near-collinear with tool NAME (Read=READ,
  Bash=VOLATILE) — the predictor must beat tool-identity, not memorize it. If joint matches/beats class -> demote to
  "agents repeat popular tools" workload restatement (clean negative).
- RE-A2 EXACT-PREFIX-survival KILLER (fix #1): >=95% repeats exact-prefix-unrecoverable. Scoped to exact-prefix caches;
  + tier-2 non-prefix-reuse fraction (CacheBlend/LMCache class) reported OR explicit scope-boundary stated (fix #4).
- RE-A3 result-equivalence CO-PRIMARY (fix #7): report byte-identical f AND result-equivalence rate as co-primary (byte-
  identical args != byte-identical results for WRITE/VOLATILE). The 9.8% headline must not conflate arg-repetition with
  recoverable-output repetition.
- RE-A4 min effect-size + COST TRANSLATION (fix #3): f>=2% of tool-call prefill tokens AND an estimated FLOPs/TTFT impact
  under realistic chunked-prefill batching ($/latency grounding, not a bare arbitrary threshold).
- RE-A5 cross-corpus sign replication CC+Codex.
- RE-A6 anti-tautology, TIGHTENED (fix #6): exclude trivially-cacheable adjacent error-retries via a STRUCTURAL retry-detection
  heuristic (same tool+args following an error on a prior call to the same tool), not just a bare "within K tokens" cutoff;
  surviving tax = LONG-GAP interior repeats not explained by retry.
- RE-A7 determinism class CONDITIONED ON INTERVENING-WRITE STATE (fix #5): a READ is invalidated by an intervening WRITE to
  the same target; the predictor must condition on session state or acknowledge the ceiling this imposes.
PRE-MEASURED LIVE SIGNAL (design session, CC n=226): 9.8% within-session byte-identical repeats; 100% have intervening
tokens (median gap 12,512) -> exact-prefix cannot recover; READ dup 3.1% vs WRITE/Bash 11.4% (counterintuitive WRITE>READ).
INSTRUMENTS: Mac CPU stdlib, reuse EXP-0007 CC tool_result join + EXP-0037 Codex call_id dedup + EXP-0042 bootstrap. NO GPU L0.
L1 (optional, orchestrator/GPU-dispatched): real vLLM APC-enabled prefill-FLOP/TTFT recovery from an interior-content memo.

## NON-COLLISION
PROJ-0002 (content-EDIT prefix invalidation) — A = byte-IDENTICAL interior repeat, never a prefix, no edit (opposite).
PROJ-0005 (intra-session BPE seam HIT->MISS) / PROJ-0007 (cross-session template drift breaking shared HEAD) — A = within-
session INTERIOR exact-repeat never a reusable prefix (3rd distinct miss-mode). DroidSpeak/PrefillShare = cross-agent reuse.
Cemetery: DEAD-0010 (idle SPECULATIVE prefill — A recomputes REALIZED repeats), DEAD-0011/12/13/14 (DECODE-SD; A is PREFILL).
ToolCacheAgent (OpenReview tX3YcbNa5w, withdrawn ICLR2026) + LLM-dCache 2406.06799 = tool-result CACHE mechanisms; A MEASURES
the realized residual tax under exact-prefix caching (no cache built). PROMOTION owes: body-verify CacheBlend 2405.16444 /
PromptCache 2311.04934 / LMCache + 2603.16104 (PRIOR_ART_ADEQUATE=no at seed, owed before promotion).

## HONEST KILL PATHWAYS (all clean/publishable)
RE-A1 fail (gap/popularity/tool-identity explains it -> workload restatement, demote); RE-A2 fail (repeats exact-prefix-
reusable -> tax illusory, kill); f<2% (agents rarely self-repeat, kill); RE-A3 result-equivalence ~0 for the repeats (no
recoverable output, tax illusory). "Prefix-caching is sufficient for agent self-repetition" is itself a useful negative.

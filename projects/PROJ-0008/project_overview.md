# PROJ-0008 — Redundant Tool-Call Prefill Tax (under EXACT-PREFIX KV-caching)

**Created:** 2026-06-01 by orchestrator-r6-001 (design committee proj0008_design, 5Y+1G yellow seed-with-fixes; charter Candidate A; Candidate B REJECTED as first seed — ToolCacheAgent OpenReview tX3YcbNa5w owns its space).
**Layer:** prefill-time within-session interior exact-repeat (distinct from PROJ-0002 edit-invalidation, PROJ-0005 BPE seam, PROJ-0007 cross-session drift — a 4th distinct miss-mode).
**First claim:** CLAIM-0018.

## THESIS (RESCOPED per committee — load-bearing fix)
On real long-horizon agent trajectories, a measurable fraction of tool invocations are BYTE-IDENTICAL re-invocations of an
EARLIER same-session call, separated by a large divergent span of intervening tokens. Each pays a full prefill + decode that
a PRODUCTION-DEPLOYED EXACT-PREFIX KV-cache (vLLM APC / SGLang RadixAttention block-hash / TensorRT-LLM / provider prompt
caching) CANNOT recover, because the cached prefix up to the 2nd call differs from the 1st and exact-prefix caching only
reuses prefixes, never interior repeats. SCOPE BOUNDARY (committee-mandated): this is the tax under EXACT-PREFIX caches ONLY
— non-prefix interior KV-fusion systems (CacheBlend 2405.16444, PromptCache 2311.04934, LMCache) CAN target interior reuse;
they are a named scope boundary / second-tier baseline, NOT claimed structurally impossible. This is a prefill-recompute
CHARACTERIZATION on real traces + named structural cause, NOT a new caching mechanism.

## FIRST CLAIM (CLAIM-0018)
Across >=2 corpora (CC+Codex), within-session byte-identical tool re-invocations = fraction f of total tool-call prefill
tokens (session-clustered 95% CI excludes 0); the tax SURVIVES an exact-prefix APC/RadixAttention (block=16) baseline (>=95%
of repeats prefix-unrecoverable); AND per-call exact-prefix-non-recoverability is predicted model-free by tool-output
DETERMINISM CLASS over a STRONG {token-gap + tool-frequency + TOOL-IDENTITY} JOINT baseline (dAUC 95% LB>0 both corpora).

## L0 GATING EXP (CPU-only, stdlib, reuse EXP-0007/0037/0042 parsers). PRE-REGISTER all RE gates BEFORE run (locked ts):
- RE-A1 LOAD-BEARING/KILLER: determinism-class dAUC over the {token-gap + tool-frequency + TOOL-IDENTITY one-hot} JOINT
  baseline, 95% LB>0 BOTH corpora. (COMMITTEE FIX: tool-identity ADDED — determinism class is near-collinear with tool name
  Read≈READ/Bash≈VOLATILE; must beat that or demote to "agents repeat popular tools".)
- RE-A2 APC-survival KILLER (RESCOPED): >=95% of repeats unrecoverable by EXACT-PREFIX caching (>=1 block prefix divergence).
  SECOND-TIER (committee-mandated): also report what fraction WOULD be recoverable under non-prefix KV reuse (CacheBlend/LMCache
  class) as a named scope boundary — OR formally state the exact-prefix scope boundary. Silence not acceptable.
- RE-A3 byte-identical (PRIMARY, conservative) + result-equivalent (CO-PRIMARY per theory_skeptic): measure result-equivalence
  rate alongside f — byte-identical args != byte-identical results for WRITE/VOLATILE; the 9.8% headline must not conflate.
- RE-A4 min effect-size + COST TRANSLATION: f>=2% of tool-call prefill tokens AND a pre-registered FLOPs-or-TTFT impact estimate
  under realistic chunked-prefill batching ($/latency grounding; 2% alone is arbitrary).
- RE-A5 cross-corpus sign replication CC+Codex.
- RE-A6 anti-tautology (TIGHTENED): exclude trivially-prefix-reusable adjacent retries; define K with justification OR use a
  structural retry-detection heuristic (same tool+args following an error on a prior call to same tool); must NOT miss long-gap
  retry-after-investigation. Surviving tax = LONG-GAP interior repeats.
- RE-A7 determinism class CONDITIONED on intervening-WRITE state (a READ invalidated by an intervening WRITE to same target);
  predictor must condition on session state or acknowledge the ceiling.
KILL/negatives (all clean+publishable): RE-A1 fail (gap/popularity/tool-identity explains it -> "agents repeat popular tools"
restatement, demote); RE-A2 fail (repeats exact-prefix-reusable -> tax illusory, kill); f<2% (rare self-repeat, kill).
PRE-MEASURED LIVE SIGNAL (design session, CC n=226): 9.8% byte-identical within-session repeats; 100% have intervening tokens
(median gap 12,512) -> exact-prefix cannot recover; READ dup 3.1% vs WRITE/Bash 11.4% (counterintuitive — WRITE repeats MORE,
naive "READ is cacheable" WRONG; discriminator must adjudicate).
INSTRUMENTS: Mac CPU stdlib; parsed CC/Codex/Gemini traces. L1 (optional, H100-coordinator-gated, only if RE-A1+RE-A2 clear):
real vLLM APC-enabled prefill-token-recompute count + recovered TTFT from an interior-content memo.

## PROMOTION-GATE OWED (committee PRIOR_ART_ADEQUATE=no — NOT a seeding blocker): cite CacheBlend 2405.16444, PromptCache
2311.04934, LMCache (non-prefix reuse), ToolCacheAgent OpenReview tX3YcbNa5w, LLM-dCache 2406.06799 before any promotion.

## NON-COLLISION: 4th distinct prefill miss-mode vs PROJ-0002 (edit->recompute), PROJ-0005 (BPE seam HIT->MISS), PROJ-0007
(cross-session drift breaking shared HEAD). Interior within-session exact-repeat never a reusable prefix. Distinct from
DEAD-0010 (idle SPECULATIVE prefill) + DEAD-0011/12/13/14 (all DECODE-SD). DroidSpeak/PrefillShare = cross-agent (not single-session).

## HONEST KILL PATHWAY: RE-A1 fail = popularity/tool-identity restatement (demote); RE-A2 fail = exact-prefix already recovers
(tax illusory, kill); f<2% = rare self-repeat (kill). Each is a first-class publishable negative.

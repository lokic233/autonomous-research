# PROJ-0005 — Tool-Result Re-Tokenization Boundary Churn Defeats Exact-Prefix KV-Cache Reuse

**Created:** 2026-06-01 (orchestrator-r4-001, refill-to-4-investing after PROJ-0001 converged).
**Charter source:** projects/PROJ-0005/CANDIDATE_CHARTERS.md (Candidate A), selected by honest 6-member design
committee (runtime/committee_run_proj5_design, ALL_COMMITTEE_DONE, 6/6 real votes, .err clean of EMPTY_OUTPUT).
Verdict: YELLOW / SEED-A-WITH-FIXES (systems_reviewer+product_realist GREEN, 3 YELLOW fixable-measurement-design,
0 RED on A; Candidate B -> RED [roofline accounting identity = DEAD-0009/0010 class]; Candidate C -> backup [TA-Fast
reduction risk]).
**Topic bias satisfied:** inference-optimization / LLM-serving / KV-cache / agentic-systems.
**Status:** L0-DESIGN (investing). occupied_territory = LEXICAL/tokenizer-layer exact-prefix KV-cache hit->miss
demotion from BPE boundary churn at tool-result injection seams (prefill-time; NOT PROJ-0002 SEMANTIC invalidation;
NOT PROJ-0004 DECODE-time draft acceptance; INVERSE of DEAD-0006 token-prefix-predicts-sharing).

## THESIS
Injecting a tool result into an ongoing context perturbs the BPE token boundaries straddling the injection seam,
so the re-tokenized token-ID prefix diverges from the cached prefix at a structurally-predictable rate — silently
demoting an exact-prefix KV-cache (vLLM APC / RadixAttention block-hash) HIT to a MISS for a quantifiable fraction
of tool-call turns, predictable model-free from the seam's delimiter class (no attention/semantic signal).

## FIRST CLAIM (CLAIM-0014) — amended per committee fixes
Across >=2 agent-trace corpora and >=2 PRODUCTION tokenizers, the fraction of tool-result-injection turns whose
re-tokenized token-ID prefix diverges from the naive-concat-cached prefix — measured at BLOCK granularity (blocks-
invalidated-per-turn against a real vLLM/SGLang block-hash schedule, block=16 tokens), NOT raw LCP — has a 95% CI
excluding 0, EXCEEDS a clean-\n-append control (CI>0 on the difference, the pre-registered PRIMARY anti-tautology
endpoint), and is predicted (AUC CI>0.5) by the seam's delimiter class alone (model-free). PASS requires all three.
FAIL = block-churn ~0 / >95% blocks survive (engines already canonicalize -> clean kill), OR == clean-append control,
OR delimiter-class non-predictive, OR the phenomenon is a re-tokenization-REGIME-mix artifact (engines that cache/
concat token-IDs have churn structurally 0).

## COMMITTEE-MANDATED FIXES (7; bake into the claim/L0 design BEFORE execution)
1. BLOCK-GRANULARITY PRIMARY ENDPOINT (HIGHEST: 3-reviewer convergence): report blocks-invalidated-per-turn vs a
   real block-hash schedule (block=16), NOT raw LCP. >95% blocks survive => fleet-FLOP-waste claim falsified, no L1.
2. RE-TOKENIZATION REGIME CHARACTERIZATION: stratify corpus by (a) full-prompt-retokenize-per-turn [churn possible]
   vs (b) token-ID-cache/delta-tokenize [churn structurally 0]. Headline churn must not be a regime-mix artifact.
3. CLEAN-APPEND CONTROL = PRE-REGISTERED PRIMARY ANTI-TAUTOLOGY GATE: churn must EXCEED clean-\n-append (CI>0)
   BEFORE delimiter-predictor AUC is reported. churn ≈ control => "BPE does BPE" clean kill.
4. REFRAME AS CHARACTERIZATION + CITATIONS: re-tokenization≠concatenation is KNOWN FOLKLORE (token healing /
   Microsoft guidance). Frame as a CHARACTERIZATION contribution (delimiter-conditioned rate + model-free predictor +
   silent APC/RadixAttention miss on real agent traces). MUST cite: token/boundary healing prior art; "Don't Break
   the Cache" arXiv:2601.06007 (closest agentic cache-cost neighbor; distinguish: A=white-box tokenizer mechanism +
   delimiter predictor, 2601.06007=black-box provider $/TTFT).
5. PRODUCTION TOKENIZER FIDELITY: use production Rust HF Tokenizers (not naive Python BPE lacking boundary/prefix-
   space/special-token handling).
6. CHAT-TEMPLATE / SPECIAL-TOKEN CANONICALIZATION CONTROL: include chat-template-injected delimiters
   (<|im_start|>, <tool_call>, etc.) that may reset BPE state + canonicalize the seam (if templates prevent churn,
   effect vanishes in production = informative negative).
7. NON-COLLISION ATTESTATION vs DEAD-0006: frame explicitly as the INVERSE of DEAD-0006 (token-prefix IDENTITY is
   ASSUMED to guarantee reuse; retokenization silently breaks that identity). Not a re-litigation.
+ MANDATORY live prior-art search before L0 (web was blocked at design; close the gap: "tokenization boundary cache
  invalidation" / "BPE seam prefix cache" / "re-tokenization KV reuse").

## GATING EXPERIMENT (L0, CPU, cheap kill)
Per trajectory: reconstruct pre/post-injection contexts as the engine assembles them; tokenize the cached-prefix-then-
append path vs the full re-tokenized path with a PRODUCTION tokenizer; compute BLOCK-level invalidation (block=16)
vs the longest-common-ID-prefix; bucket by delimiter class; bootstrap CI; compare vs clean-\n-append control (primary
gate); fit a model-free delimiter-class predictor (AUC+CI); stratify by re-tokenization regime. Hours, no GPU, no
model weights. KILL: block-churn ~0 or == control = "engines already canonicalize seams" (publishable negative ->
redirects serving teams to PROJ-0002 semantic axis). L1 (only if L0 passes): H100 vLLM APC hit/miss counters +
recompute TTFT on a capped trajectory set, bounded+watchdogged (H100 safe; MI350X not required).

## WHY IT MATTERS (Meta)
Exact-prefix KV reuse (APC / RadixAttention) is THE dominant multi-turn-agent TTFT optimization; a silent,
structurally-predictable hit->miss at tool seams = wasted prefill FLOPs at fleet scale; the delimiter predictor
yields a trivial mitigation (seam canonicalization before hashing). A clean negative redirects effort. Serving-cost
result on a real Meta-shaped agent workload, zero data-collection cost (reuses PROJ-0003 trace corpora).

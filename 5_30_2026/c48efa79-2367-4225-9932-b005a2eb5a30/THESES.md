# THESES — session c48efa79 · 2026-05-30/31 · all verdicts + veto reasoning

6-agent committee: CC4.8, CC4.7, CC4.6, Codex5.5, Gemini3.5, Agent-D.
Rule: GREEN=6 GREEN; YELLOW=any YELLOW & no RED; RED=any RED. Measured artifacts = source of truth.

This session ran an INDEPENDENT 6-agent committee over the same three repos (forkedkv/edmm/
agent-failure-attribution) and converged on overlapping conclusions to session 048fcb0d via a
different vote path, then pushed FURTHER: caught a multi-layer correctness bug, killed two theses
by self-administered control experiments, and explored a new failure-attribution domain.
14 vote rounds, 11 experiments (E1–E12). NOTE the convergence: this session's T2≈048fcb0d's NT2,
T1≈NT1. Independently re-derived under hostile review — not copied.

## T2 — Mid-Prompt KV Cache-Invalidation Cost-Map  → **GREEN (6/6)** [the session's result]
One-sentence: tool-call mid-prompt injection is an architectural prefix-hash cache-invalidation
pathology (NOT an engine bug) inflicting an 8–13× live-engine TTFT penalty that reproduces across
vLLM (8.21×) and SGLang (12.77× @32k/7B) and grows with context; a per-edit-class cost taxonomy
(append=FREE 0.90–0.96×, interior fixed-width 1.3–2.4×, interior variable 3.0–8.2×, prepend up to
13.6×) plus an empirical quantification (tested stacks) of WHY interior edits are not cheaply
KV-repairable (suffix K/V diverges at every layer ≥1). NO runtime-primitive claimed. Reframed to a
CONDITIONAL cost-map + design constraint with ~0% current-harness incidence stated up front.
- Evidence: E2 (SGLang cross-engine), E3 (edit taxonomy), E4b (multi-layer suffix divergence,
  max|dK| 4.04 at L≥1 — the correctness bug that killed the interior-repair claim), E4c (terminal
  repair exact + 5–82×, but = what RadixAttention append already does), E5 (325 real Claude Code
  sessions: ~99.9% append, ~0% interior incidence → reframed).
- Vote path (11 rounds): R3 5G/1R → E2 → R4–R9 narrowing (caught 2 overclaims) → R9 6/6 GREEN →
  E5 self-audit BROKE it (R10 4G/2Y) → R11 reframed to conditional cost-map → **6/6 GREEN**.
- Veto reasoning recorded: Agent-D RED (R3–R6) "vLLM-bug, SGLang won't show >5×" → falsified by
  E2 (conceded). CC4.8+Codex RED (R6) "E4 proved only layer-0 equality" → CONFIRMED by E4b (real
  bug). CC4.8+Agent-D (R7) "terminal repair = RadixAttention append" → runtime-primitive WITHDRAWN.
  R8 YELLOWs: "13.6× prepend mislabeled as interior" + "'impossibility' overclaims" → both fixed
  verbatim. R10 YELLOWs (CC4.7, Codex): "~0% incidence ⇒ reframe, don't claim broad impact" → done.

## T1 — VMM Mapping-Table as Schedulable Resource  → **YELLOW** (demoted, NVIDIA-scoped)
One-sentence: per-context CUDA-VMM mapping-table entries are an exhaustible HBM-orthogonal resource
(~520K on H100, OOM at cuMemSetAccess) no scheduler tracks.
- Evidence: forkedkv M4b (K≈520K), E1 cross-vendor (AMD ROCm sustained ≥4M mappings, zero VMM
  failure → ceiling is NVIDIA-driver-specific, NOT a cross-vendor law).
- Veto reasoning: Agent-D RED "collapses on ROCm; a microbench isn't a scheduler" → E1 CONFIRMED
  the ROCm half (demoted to NVIDIA-scoped characterization). GREEN-gate (reserve/query API +
  cross-vendor) not closed this session — MI350X went into repair. Matches 048fcb0d's NT1 finding.

## T3 — Agentic KV-Divergence Workload Model  → **KILLED (6/6)**
One-sentence (proposed): token-prefix sharing overstates true KV sharing; an a-priori divergence
model beats RadixAttention's reactive token matching.
- Veto reasoning: E6 tested it on 12 real agent branch pairs. A discipline CONTROL (identical
  207-tok prefix at two seq lengths → max|dK| 6.25e-2 ≫ 5e-3 tol) proved the apparent KV-vs-token
  divergence was fp16 SDPA kernel nondeterminism, NOT semantic. With the artifact controlled,
  token-prefix sharing PREDICTS KV sharing → RadixAttention already captures it. 6/6 KILL. The
  intended angle was self-falsified before any vote rubber-stamped it.

## T4 — Layer-Stratified Positional KV Reusability  → **KILLED (gate)** (R13: 0G/4Y/1R/1K)
One-sentence (proposed): repeated content's KV is reusable in a layer-stratified way (RoPE-
recoverable shallow vs context-mix-irrecoverable deep).
- Evidence: E8 measured a clean decomposition (pre-RoPE K & V bit-identical at L0; V divergence
  0→15.6 by L27). E9 GATE (committee-specified): only 1/28 layers reusable within tol → 0.054%
  prefill-FLOP saving ceiling at 1.5% real incidence (≪ 2% KILL bar). CC4.8: L0 exactness partly a
  RoPE tautology. Clean negative; the measurement is real but actionable impact ≈ zero.

## T5 — Error-Class Predicts Agent Recovery Competence  → **YELLOW** (R14: 0G/5Y/1K)
One-sentence: a coding agent's identical-failing-call repeat rate depends on error class
(path_missing 18.6% vs other 6.1%, ~3×) on 6,510 real Claude Code tool calls.
- Evidence: E10 (real-trace census). GREEN-gate attempted: E11 cross-harness (codex traces:
  9 errors/208 calls — UNDERPOWERED) + E12 intervention A/B. E12 first cut looked decisive
  (control 0/20 vs treatment 20/20) but E12b HARDENED CONTROL showed control recovers 8/8 on its
  own → the win was a TOY-SETUP ARTIFACT (impoverished control). Retracted before any GREEN claim.
- Veto reasoning: all agents — real but THIN (single harness, ~200 well-classified errors, no
  robust intervention, crowded reflexion/self-debug prior art). Stays YELLOW.

## HONEST NULLS / RETRACTIONS THIS SESSION (anti-coping discipline)
1. E6: T3's KV-vs-token divergence = fp16 kernel artifact (control-caught). 
2. E7: fp16 chunked/cached prefill does NOT flip greedy tokens (0/60) — "prefix caching changes
   outputs" thesis unsupported.
3. T5 sub-claims: a coarse 46.8% error-class signal dissolved to 18.6% (classification artifact);
   "178 failure spirals" → 10 redundant retries (0.2%, parse-bug-corrected, negligible).
4. E12 intervention: +100pt result retracted as control-impoverishment artifact (E12b).
Four self-caught overclaims/nulls. Per discipline: honest negatives are wins.

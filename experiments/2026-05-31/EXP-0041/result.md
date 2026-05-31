# EXP-0041 (L3) — CLAIM-0012 discriminating ablations (the committee's 2 killer tests)

**Claim:** CLAIM-0012 — tool-call failures are temporally OVER-DISPERSED within a session
(3-harness-replicated, permutation-null-survived, M4-survived). PURELY DESCRIPTIVE.
**Verdict gated on:** VERDICT-0045 (6/6 YELLOW) → 2 discriminating ablations that separate TRUE
within-session temporal-memory burstiness from (a) trivial RATE-HETEROGENEITY (Cox mixture-Poisson)
and (b) deterministic RETRY-CASCADE control-flow.
**Level:** L2 (CPU-only, stdlib, ~10s wall). Reuses EXP-0037/0038 parse + runs-test + permutation +
dispersion machinery, EXTENDED to carry `tool_name` + arg-text per call.

---

## HEADLINE: BOTH ABLATIONS SURVIVE on all 3 harnesses → burstiness EARNED → recommend GREEN.

### KILLER 1 — Tool-stratified permutation null (the load-bearing test)
Permute failure labels ONLY among calls to the SAME `tool_name` within each session (block
permutation; N=2500). Each tool keeps its own marginal failure rate fixed → destroys WITHIN-tool
temporal memory while PRESERVING between-tool rate heterogeneity. If Z collapses → over-dispersion
was rate-heterogeneity (trivial Cox mixture). If Z survives negative → genuine within-tool memory.

| Harness | Whole-session perm Z | **Tool-stratified Z (CANONICAL)** | one-sided p | Attenuation | Verdict |
|---|---|---|---|---|---|
| Claude Code | -4.15 | **-2.38** | ~0.009 | ~43% | **SURVIVES** |
| Codex (deduped) | -15.72 | **-13.51** | ≪1e-10 | ~14% | **SURVIVES** |
| Gemini | -3.82 | **-3.43** | ~3e-4 | ~10% | **SURVIVES** |

All three remain significantly negative (clustered) AFTER fixing each tool's own failure rate.
→ The over-dispersion is NOT explained by between-tool rate mixing (some-tools-fail-more). There
is genuine within-tool temporal memory. **Rate-heterogeneity alternative REJECTED on all 3.**

#### Granularity caveat (reported honestly, `stouffer_strat_overctrl`)
Canonical strata = the raw `tool_name` the harness exposes (CC: Bash/Read/Edit/…, 15 tools; Codex:
exec_command/web_search/…, 5 tools; Gemini: run_shell_command/read_file/…, 7 tools). For Codex
(~90% exec_command) we ALSO ran an OVER-CONTROL that splits exec_command by command verb
(`exec:git`, `exec:npm`, … → 42 strata): Codex Z collapses to **-1.90 (p≈0.06, NOT sig)**.
This is EXPECTED and is over-control, not a kill: stratifying by command verb conditions on the very
locus the burstiness lives in (consecutive failures of the same verb = the within-tool memory we are
testing). The verb is a derived sub-classification, not a tool the agent selects. CC and Gemini have
genuinely distinct tool_names so canonical == over-control for them (CC -2.40, Gemini -3.42 — both
survive). **Conclusion holds at the principled (tool_name) granularity; the only collapse appears
under a strata definition that absorbs the signal.**

### KILLER 2 — Retry-cascade collapse
Collapse immediate `fail → same-intent-retry → fail` runs into a single root event (label = OR over
the run). Same-intent = same (refined) tool AND token-Jaccard(arg-text) ≥ threshold. Exact arg match
(θ=1.0) almost never fires because real retries MODIFY the command (ping→curl→curl, `which`→`command -v`);
fuzzy θ=0.6 / 0.4 capture true same-intent retries. Recompute whole-session permutation Z on collapsed seq.

| Harness | Base Z | Collapsed Z (θ=1.0 exact) | Collapsed Z (θ=0.6) | Collapsed Z (θ=0.4) | % calls removed (θ=0.6) | Verdict |
|---|---|---|---|---|---|---|
| Claude Code | -4.15 | -4.20 | **-3.79** | -3.74 | 0.42% | **SURVIVES** |
| Codex | -15.72 | -15.50 | **-13.94** | -13.62 | 0.67% | **SURVIVES** |
| Gemini | -3.82 | -3.66 | **-4.34** | -4.29 | 6.4% | **SURVIVES (strengthens)** |

Retry cascades are RARE (≤0.7% of CC/Codex calls, ~6% Gemini) and removing them barely dents Z (and
strengthens Gemini). → The clustering is NOT deterministic retry-loop control-flow. **Retry-mechanics
alternative REJECTED on all 3.** Dispersion index stays >1 throughout (CC 1.51-1.61, Codex 1.25-1.40,
Gemini 1.86-2.03); burstiness B stays positive (CC ~0.35, Codex 0.16-0.22, Gemini ~0.16).

### (3) Mixture-of-Poissons vs single-Poisson (optional strengthening)
2-component Poisson mixture on window-5 failure counts is BIC-preferred over single-Poisson on all 3
(ΔBIC: CC 20.9, Codex 2.4, Gemini 10.9; mix params w,λ1,λ2 e.g. CC [0.74,0.13,1.36]). This DOCUMENTS
that rate-heterogeneity is ALSO present (the Cox alternative is real) — but it does NOT explain away
the burstiness, because KILLER-1 already removed between-tool rate-mixing and the signal survived.
The mixture and the temporal memory COEXIST: both rate-heterogeneity and genuine within-tool clustering
contribute. The claim should acknowledge the mixture component explicitly.

---

## RECOMMENDATION: GREEN (with framing guardrails)

Both committee-mandated killer ablations SURVIVE on all 3 harnesses at the principled granularity:
1. Tool-stratified permutation → within-tool temporal memory is REAL (not rate-mixing).
2. Retry-cascade collapse → not deterministic control-flow.

The burstiness is EARNED, not a trivial artifact. **No reframe to "non-stationary rate" required** —
the signal is stronger than that weaker fallback.

### Honest guardrails the paper MUST carry (do not overclaim):
- **CC leg is the weakest:** tool-stratified Z=-2.38 (p≈0.009) — survives but thin; carried by Stouffer
  aggregation (per-session median strat-Z = 0.0). Codex is the strong leg (Z=-13.5). Gemini solid (-3.43).
- **Rate-heterogeneity co-exists** (mixture BIC-preferred all 3). Frame the result as "over-dispersion
  with a within-tool temporal-memory component that SURVIVES rate-stratification," NOT "burstiness is
  purely temporal." Both Cox-mixture and Hawkes-like memory are present; the contribution is that the
  memory component is non-zero after controlling for the mixture.
- **Granularity is a reviewer attack surface:** report BOTH tool_name-stratified (survives) and
  verb-stratified-over-control (Codex collapses) and explain why tool_name is the principled choice.
  Do not hide the over-control number.
- Keep PURELY DESCRIPTIVE: arrival-process statistic only, no error-class conditioning, no recovery prediction.

---

## Files
- `impl/burst_L3.py` — implementation (stdlib-only CPU; reuses EXP-0038 machinery)
- `results/harness_summary_L3.csv` — per-harness all metrics (whole/strat/overctrl/collapse×3θ/dispersion/B/poisson)
- `results/per_session_L3.csv` — per-session z_whole / z_tool_strat / z_strat_overctrl / z_whole_coll_06

## Reproduce
```
/usr/bin/python3 experiments/2026-05-31/EXP-0041/impl/burst_L3.py
```
Corpora: ~/.claude/projects, ~/.codex/sessions, ~/.gemini/tmp. CPU-only, ~10s, no GPU/model CLIs.

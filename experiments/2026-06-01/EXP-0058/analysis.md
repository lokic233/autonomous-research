# EXP-0058 — Analysis: Multi-Tool Batch Admission Mis-Estimation (PROJ-0012 / CLAIM-0023)

**Agent:** researcher-0023-L0-r7 | **Sub-monitor:** sub-monitor-0012-r7 | **prompt_version:** v001
**Pre-registration:** `impl/PRE_REGISTRATION.md` LOCKED `2026-06-01T20:52:44Z`, committed (HEAD f1c7eae) BEFORE this run.
**Run:** `logs/run_main.log` | **Results:** `results/summary.json` | seed 20260601 | wall 16.9 s | CPU, stdlib only.

## DISPOSITION (one line)
**EARLY-KILL-DEAD-0018-RESKIN — the FIX-2 early-kill trigger FIRED.** A clean, first-class NEGATIVE: a co-issued
parallel-tool batch's total prefill mass is predicted by the **maximum per-call whale among its calls**, and a cheap
pre-execution **joint-argument** oracle adds **nothing** (dAUC = −0.0045, 95% LB = −0.017, folds not all positive) over a
baseline that already contains {count, mean-gap, mean-freq, tool-mix, tool-pair/triple, matched-max/sum-per-call}. The
batch axis therefore collapses onto the per-call whale axis that PROJ-0009 already killed (DEAD-0018). `result_effect =
kill`. Reinforced independently by RE-B0 (mass not concentrated enough) and RE-B1 (call-count is not useless).

---

## 0. DESIGN-GATE RESOLUTIONS (binding, resolved with live evidence BEFORE the run)

### FIX-1 strawman — RESOLVED (a genuine count-driven PRE-EXECUTION decision point exists)
Codex emits **genuine co-issued parallel tool calls**: 60.0% of consecutive `function_call` runs have length ≥ 2 (the
model streams ≥2 calls with **no `function_call_output` between them** — all emitted before any result exists), and within
a run the median consecutive `function_call` timestamp gap is **0.001 s** (p90 0.075 s, n=1713). At that instant the
agent-runtime must admit/dispatch N calls knowing only **count + arguments**, never result lengths — exactly the
orchestrator-side batch-dispatch decision point the charter's FIX-1 reframe names. This is distinct from the strawman
(Sarathi-Serve 2403.02310 / vLLM `max_num_batched_tokens` chunk **after** payloads exist). Cite/disclaim: DynaServe
2504.09285 (general length heterogeneity, not count!=total); both arXiv IDs **live-verified 2026-06-01**.

### FIX-4 cross-instrument — RESOLVED honestly as SINGLE-INSTRUMENT (Codex) BY DESIGN
**Claude Code emits ZERO co-issued parallel tool calls in this corpus** (253 files): every assistant message carries
exactly one `tool_use` (dist `{1: 2554}`) and every user message exactly one `tool_result` (dist `{1: 2555}`). CC turns
are strictly sequential single-call round-trips. The design committee's CC "50% multi-call / 75.7% top-decile mass" came
from **stream-offset adjacency (gap<5 tok) clustering of SEQUENTIAL calls** — those clusters are NOT co-issued batches;
using them as the unit would be the FIX-1 strawman itself. Consequently the parallel-batch claim is **single-instrument
(Codex) by design**, declared honestly — **NOT** a WAIVED-WITH-FLAG escape. **RE-B5 cross-instrument HARD GATE is
NOT-SATISFIABLE** and cannot contribute a PASS.

---

## 1. CORPUS / UNIT
Codex co-issued batch = maximal run of consecutive `function_call` events with no intervening output (call_id co-occurrence).
- 86 Codex sessions (≥ 8 calls). **704 multi-call co-issued batches** (sizes 2/3/4/≥5 = 167/180/281/76); 60.3% of runs
  are multi-call. Whale label = batch-total in top decile (n_whale = 70 batches across 44 sessions).
- RE-B3 no-leakage **by construction**: every X feature is derived from `args_str` only; result text never enters X.

## 2. GATE-BY-GATE RESULTS

| Gate | Metric | Value | Threshold | Verdict |
|---|---|---|---|---|
| **RE-B0** magnitude | multi-call frac | 0.603 | ≥0.25 | ✅ |
| | top-decile batch mass share | **0.481** | ≥0.50 | ❌ marginal-fail |
| **RE-B1** count-insuff. | Spearman(size,total) | 0.267 | <0.30 | ✅ (below) |
| | size-only whale-AUC | **0.626** | ≤0.60 | ❌ premise partial-fail |
| **RE-B2** killer | dAUC(B1−B0) point | **−0.0045** | ≥0.03 | ❌ |
| | dAUC 95% LB (2000× sess-boot) | **−0.017** | >0 | ❌ |
| | all-5-folds-positive | False `[+.006,+.007,−.016,−.018,−.013]` | all>0 | ❌ |
| **RE-B2b** decomp | matched-max-per-call ALONE AUC | 0.795 | — | (captures ~88% of above-chance signal) |
| | per-size-stratum B1 AUC | 2:0.75 / 3:0.70 / 4:0.79 / ≥5:0.94 | >0.5 | separates, but via B0 not joint-arg |
| | dAUC_decomp (B1 − maxnull) | +0.039 | >0 | **driven by B0 count/mix, NOT joint-arg** |
| **RE-B4** mass | masscap lift (B1−B0) | **−0.016** | (descriptor) | no lift; Gini(total)=0.677 |
| **RE-B5** cross-instr | — | NOT-SATISFIABLE | sign-agree | single-instrument by design |
| **STAT** | HHI whale-mass by session | 0.032 (eff-n≈31) | <0.20 | ✅ not driven by few sessions |
| | fold dAUC std | 0.011 | — | tight, consistently ≈0/negative |

## 3. THE FIX-2 EARLY-KILL (decomposition) — FIRED
The load-bearing question is whether the **joint-argument** features add value *beyond the max per-call whale*. They do not:
- matched-max-per-call **alone** → AUC 0.795; full B0 (adds count/mix/pair/triple/matched-sum) → 0.838; B1 (adds the
  claim's joint-arg max/sum) → 0.834. Above-chance signal: max-alone (0.795−0.5)=0.295 vs B1 (0.834−0.5)=0.334 ⇒
  **max-per-call alone already explains ~88%** of it.
- The **claim's increment** (B1 − B0) = **−0.0045** (LB95 −0.017, folds mixed). Zero.
- RE-B2b's "dAUC_decomp = +0.039 beats max-null" is achieved entirely by B0's **count/mix** terms — *not* by the
  joint-arg features under test. So the decomposition statistic does **not** rescue the claim.

⇒ The batch whale reduces to **max(independent per-call whales)**. The batch-level axis collapses onto the per-call whale
axis already killed in PROJ-0009/DEAD-0018. **EARLY-KILL trigger FIRED — immediate termination, DEAD-0018 re-skin.**

## 4. REINFORCING (independent) KILLS
- **RE-B0**: top-decile co-issued batches carry only 48.1% of batched mass (< 50% floor). The genuine co-issued
  distribution is *less* concentrated than the illusory CC sequential-adjacency 75.7% — there is no extreme count-vs-total
  gap to exploit.
- **RE-B1**: size-only whale-AUC 0.626 (> 0.60) — call **count is not useless**; budgeting chunked prefill by call count
  already captures meaningful signal, weakening the "count fails" premise.
- **Robustness** (stricter co-issued def: all within-batch ts-gaps < 1 s, 698 batches): dAUC −0.0039, LB95 −0.017, folds
  not all positive — **same negative**.

## 5. STAT DISCIPLINE (FIX-5)
fold-to-fold dAUC std 0.011; folds `[+0.006, +0.007, −0.016, −0.018, −0.013]` (not all positive — the decisive fact);
whale-mass HHI 0.032 (effective-n ≈ 31 sessions, 44 whale sessions) → **not** driven by a handful of batches/sessions, so
the negative is not a small-n artifact. Per the frozen rule, no GREEN was available regardless (single-instrument).

## 6. SCIENTIFIC TAKEAWAY (publishable negative)
For genuinely co-issued parallel-tool batches (Codex), the joint prefill mass that hits a chunked-prefill scheduler is
governed by the **single largest result among the co-issued calls**, which is itself only weakly predictable and is the
already-killed per-call axis. A cheap **pre-execution joint-argument oracle adds nothing** over knowing call count, tool
mix, and the max per-call signal. **Practical guidance: budget/admit co-issued parallel-tool batches by call count (plus,
if available, a per-call max estimate); do NOT build pre-execution batch-cost oracles from joint argument structure.**
CC (this corpus) does not emit parallel tool calls at all, so the question is Codex-only here.

## 7. DISPOSITION → SUB-MONITOR
**EARLY-KILL-DEAD-0018-RESKIN** (FIX-2 fired) — `result_effect = kill`. First-class clean negative, multiply confirmed
(RE-B2 + RE-B0 + RE-B1 + robustness). This agent does not convene the committee or write the verdict; the sub-monitor
forwards this completed evidence.

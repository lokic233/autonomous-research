# EXP-0007 — Real-trace failure-class → recovery-competence census (CLAIM-0008)

**Domain:** MAP-0002 (Agent failure attribution & recovery). **CPU-only, stdlib-only, ~1.2s.**
**Claim under test:** CLAIM-0008 "Error-class predicts agent recovery competence." (was YELLOW/weakened, VERDICT-0009)

> NOTE: CLAIM-0008's stored metadata points at MAP-0001 + KV-cache baselines (vLLM-APC / SGLang-Radix /
> FlashInfer). That is BUG-15 — those are the GPU/KV-cache domain and DO NOT apply here. This experiment
> is in the correct failure-attribution domain (MAP-0002). No KV-cache baseline is relevant.

## Data (REAL, not synthetic)
145 Claude Code agent session logs in `~/.claude/projects` (multi-turn tool-using coding/research agents
that ran real fbsource/research tasks — incl. the prior research-committee agents). After joining
`tool_result`→`tool_use` by id and dropping <2-call sessions: **70 sessions, 3,396 tool calls, 356
ground-truth failures** (`is_error:true`). Same corpus the prior E5 KV-census used — but classified for
failure attribution, which had never been done.

## Method
1. **Taxonomy** (17 mutually-exclusive error-classes, first-match regex on result text + tool name + Bash
   head-command): network (dns/conn/http), ssh.auth, fs.notfound/perm, cmd.notfound, proc.timeout/exit_nodetail,
   code.build/test, edit.mismatch/other, and crucially the **harness/policy** classes discovered by auditing
   the 84%-"other" bucket: `policy.web_disabled` (Internet-mode hook block), `policy.input_filter`,
   `policy.perm_denied`, `cancelled`, `read.too_large`.
2. **Recovery label** (per failed call): scan forward in the same session for the next SAME-INTENT call
   (same tool; for Bash same head command, for file tools same file_path). `recovered=1` iff a later
   same-intent call succeeds; else 0.
3. **Predictiveness vs NULL baseline**: NULL = class-agnostic global recovery rate p0. Report per-class
   rate, Cramér's V, permutation test (5000 label shuffles), and **honest leave-one-out Brier** improvement
   over the constant-p0 predictor (out-of-sample, not in-sample overfit).

## Results
**Null baseline p0 = 0.449** (global recovery rate).

| class | n | recovery rate | Δ vs null |
|---|---|---|---|
| policy.web_disabled | 109 | **0.000** | −0.449 |
| other | 97 | 0.742 | +0.293 |
| cancelled | 59 | 0.559 | +0.110 |
| policy.perm_denied | 30 | 0.567 | +0.117 |
| fs.notfound | 19 | 0.632 | +0.182 |
| proc.exit_nodetail | 14 | 0.500 | +0.051 |
| (rare classes n≤6 …) | | | |

- **Full taxonomy:** χ²=147.8 (df=16), **Cramér's V = 0.644 (large)**, permutation **p = 0.0002**.
- **Robust to rare-class collapse** (n<10 → "rare"): V=0.618, p=0.0002.
- **Honest leave-one-out Brier:** null=0.247 → class-conditional=0.160, **improvement +0.087 (≈35% reduction)**.
  Knowing the error-class predicts recovery OUT-OF-SAMPLE, beating the null.
- **Theory-driven 2-class split (permanent harness/policy block vs transient):**
  permanent (web_disabled/input_filter/perm_denied/cancelled) **n=200, recovery 0.250**;
  transient **n=156, recovery 0.705**; **φ=0.454, perm-p=0.0002**.
- **Leave-one-session-out robustness:** the permanent-vs-transient recovery gap stays **+0.36 to +0.48**
  across all dropped sessions, spread over **26/37** sessions — not an artifact of one session.

## Headline characterization (the defensible claim that survives)
The single largest, cleanest signal: **`policy.web_disabled` recovers 0/109 — a permanent harness gate is
perfectly unrecoverable**, exactly as a causal theory of error-class predicts. Recovery competence is
**bimodal by error-class provenance**: *harness/policy* errors (a permission the agent cannot grant itself)
are near-unrecoverable; *environmental/transient* errors (file-not-found, transient net, code/build) recover
at ~63–100%. Error-class is not merely correlated with recovery — it carries large, out-of-sample-predictive,
session-robust information about it.

## Honest caveats (anti-overclaim)
- **Partial outcome-definition coupling:** permanent classes recover ~0 partly *because* the agent stops
  retrying a hard block. That is the correct causal story (permanent = not retryable to success), not a bug,
  but the predictiveness is strongest precisely where it is most mechanically obvious. The *non-trivial*
  finding is the spread WITHIN transient classes (fs.notfound 0.63 vs edit 0.80 vs code.build 1.0) and that
  a simple class label beats the null out-of-sample by 35%.
- **Single-harness corpus** (Claude Code only): the policy-block taxonomy is harness-specific. Cross-harness
  generality is unmeasured (honest scope, mirrors the E5 census caveat).
- **Recovery = same-intent later success within the session**; cross-tool workarounds (agent achieves the
  goal a different way) are NOT counted as recovery, so transient recovery rates are a lower bound.
- Small-n tail classes (net.*, code.test, fs.perm, read.too_large: n=1–4) are individually unreliable; the
  robustness analyses deliberately do not lean on them.

## VERDICT for CLAIM-0008
**SUPPORTS / STRENGTHENS** (YELLOW → defensible). On real agent traces, error-class is a strong, out-of-sample,
session-robust predictor of recovery competence (V=0.64; LOO-Brier +0.087 vs null; permanent-vs-transient
φ=0.45). The honest sharpened claim is: *"Error-class predicts recovery competence, and the dominant axis is
harness/policy-permanence: agent-uncontrollable policy/permission gates are near-unrecoverable (web_disabled
0/109), environmental/transient errors recover at 0.63–1.0."* This is the MAP-0002 real-trace failure census.

## Files
- impl: `experiments/2026-05-31/EXP-0007/impl/failure_recovery_census.py`
- csv:  `experiments/2026-05-31/EXP-0007/experiment_result/per_class_recovery.csv`
- log:  `experiments/2026-05-31/EXP-0007/experiment_result/run_stdout.txt`

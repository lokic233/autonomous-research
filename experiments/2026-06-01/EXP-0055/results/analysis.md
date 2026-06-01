# EXP-0055 — Analysis (committee-ready, honest pass-or-kill)

**Project:** PROJ-0009  **Claim:** CLAIM-0020  **Researcher:** researcher-0020-L0-r7
**Pre-registration:** `impl/PRE_REGISTRATION.md` (LOCKED 2026-06-01T19:11:52Z, committed before any results)
**Seed:** 20260601  **Stack:** pure stdlib, Mac CPU  **Run log:** `logs/run_main.log`

## DISPOSITION: **KILL-NEGATIVE** — clean, first-class negative.
**Gate that fired:** RE-A1 (within CC: arg-structure adds nothing over an arg-template B0) **AND** RE-A3
(cross-instrument HARD GATE: the only within-instrument positive does not replicate — the SHELL-class effect
flips sign CC vs Codex). The pre-registered falsification mode ("mere sub-tool identity recovery") is directly
demonstrated.

---

## What was tested
Unit = one tool CALL. Within each high-volume tool, label `y=1` iff `result_tok` (len/4) is above the 90th
percentile *within that tool*. Question: does a cheap PRE-EXECUTION **arg-STRUCTURE** feature set (B1) predict
prefill whales **over and above** a JOINT baseline (B0) that already includes tool identity + an **arg-TEMPLATE**
feature (sub-tool identity: first shell token / file extension / URL host / JSON-key signature)? RE-A2 no-leakage
holds by construction — every feature is derived from `args_str` only; result text never enters X.

Corpora: CC `~/.claude/projects` (65 sessions ≥8 calls, 2 368 calls) and Codex `~/.codex/sessions`
(83 sessions, 2 770 calls).

## RE-A0 — heavy-tail magnitude floor (NOT load-bearing): **PASS both corpora**
Top-decile-length calls carry **78.9 %** of all result-prefill tokens in CC (matches the live PROJ-0009
reference of 78.9 %) and **57.1 %** in Codex. Both ≥ 50 %. The heavy tail the thesis depends on is real; the
question is purely whether it is *pre-predictable within tool over sub-tool identity*.

## RE-A1 — LOAD-BEARING KILLER (per powered tool; PASS iff dAUC_LB95>0 AND dAUC_point≥0.03)

| corpus | tool | n | pos_rate | AUC B0 | AUC B1 | dAUC | LB95 | all-folds+ | RE-A1 |
|---|---|---|---|---|---|---|---|---|---|
| CC | Bash | 1313 | 0.100 | **0.751** | 0.737 | **−0.013** | −0.060 | no | **FAIL** |
| CC | Read | 510 | 0.100 | 0.430 | 0.451 | +0.021 | −0.110 | no (std 0.24) | **FAIL** |
| CC | POOLED(2) | 1823 | 0.100 | 0.694 | 0.668 | −0.026 | −0.077 | no | **FAIL** |
| Codex | exec_command | 1677 | 0.100 | 0.501 | 0.710 | +0.209 | 0.148 | yes | pass* |
| Codex | three_pai_web_search | 618 | 0.097 | 0.449 | 0.610 | +0.161 | 0.039 | yes | pass* |
| Codex | write_stdin | 236 | 0.097 | 0.400 | 0.459 | +0.060 | −0.052 | no | FAIL |
| Codex | POOLED(3) | 2531 | 0.099 | 0.485 | 0.620 | +0.135 | 0.088 | yes | pass* |

`*` within-instrument pass only — killed by RE-A3 / B0-weakness artifact below.

**CC is a clean within-tool negative.** For Bash the arg-TEMPLATE B0 alone reaches AUC 0.751 (75 distinct command
templates: `ls`, `cat`, `python3`, …); adding arg-structure makes it *worse* (dAUC −0.013). This is exactly the
pre-registered falsification: the predictable component of a prefill whale is **sub-tool identity**, and a static
arg-structure feature recovers nothing beyond it.

## Why the Codex "positives" do not count — two independent reasons

**(1) RE-A3 cross-instrument HARD GATE — FAIL (sign flip).** Mapping tools to semantic classes, the SHELL class is
powered in both corpora (CC `Bash`, Codex `exec_command`). dAUC is **−0.013 (CC) vs +0.209 (Codex)** — opposite
signs. The WEB class is powered only in Codex (no CC analog). Sign agreement is REQUIRED for a robust PASS; it
fails. There is no instrument-general within-call predictor.

**(2) B0-weakness artifact (post-hoc, `results/posthoc_fair_template.json`).** The frozen `arg_template` looks for
a string `command` key. Codex serializes the shell command under key **`cmd` as a LIST**, so the template
**degenerated to 4 buckets (96 % in one)** and B0 AUC collapsed to ~0.50 — letting the *same* sub-tool-identity
information leak into B1's structure features. Re-running with a fair template that parses Codex `cmd` lists
(39 distinct templates, B0 AUC 0.501→**0.685**) shrinks Codex exec_command **dAUC 0.209 → 0.083** — i.e. **~60 %
of the apparent arg-structure signal was sub-tool identity recovery after all.** CC Bash is unchanged (dAUC
−0.011), and the SHELL sign-flip persists. (`three_pai`/`write_stdin` have degenerate single-bucket templates too
— their args are `query`/stdin, not URLs/paths — so their B0 is likewise weak and uncomparable across instruments.)

## RE-A4 — heavy-tail MASS gate (secondary, reported)
Top-10 %-scored mass-capture **lift (B1 − B0)** is small everywhere: CC Bash +0.020, CC Read +0.022, Codex
exec_command +0.058. Spearman(B1 score, result_tok): CC Bash 0.27, Codex exec_command 0.34 — modest, and again
mostly B0-recoverable. No corpus shows arg-structure capturing a large incremental share of prefill mass.

## RE-A5 — within-session permutation control
Frozen RE-A5 permutes only `path_depth`/`glob_breadth` within session; for Codex exec_command dAUC **survives**
(0.200), proving those two features are *not* the source. The **post-hoc RE-A5b** (permute ALL six struct
features within session) collapses Codex exec_command dAUC to **0.002** (`session_confound=False`) — so the
Codex residual is a genuine *within-call* signal carried by `arg_len`/`numeric`/`flags`, **not** a session-level
project-size confound. This makes the kill cleaner: the Codex residual is real but instrument-specific and
non-replicating, not a confound we are hiding behind.

## Stat discipline
All-5-folds-positive fails for every CC tool. HHI of whale mass: CC Bash 0.079 (healthy), CC Read **0.460**
(dominated by few sessions — flagged), CC pooled 0.347 (flagged), Codex exec_command 0.029 (healthy). The CC Read
"positive" point estimate is untrustworthy (HHI flag + fold std 0.24 + LB95 −0.11).

## Committee bottom line
Within-tool result-prefill whales are **not** robustly pre-predictable from static argument STRUCTURE beyond
**sub-tool identity** (the command name / file type), and even that identity-based signal does **not transfer
across harnesses** (sign flip CC↔Codex; both also confounded by how each harness serializes args). A
chunked-prefill admission scheduler therefore cannot rely on a cheap arg-structure rule to pre-route whales
within a tool class — at best it can bucket by *sub-tool template*, and that template's predictive value is itself
instrument-specific. **The thesis (CLAIM-0020) is FALSIFIED as sub-tool identity recovery → clean publishable
negative.** RE-A0 confirms the heavy tail is real, so the open scheduling problem (head-of-line blocking from a
predictable-by-identity minority) stands — but the *non-trivial within-tool arg-structure* refinement does not.

### Honest caveats / ceilings
- Char/4 token proxy (CHARS_PER_TOK=4.0), same as EXP-0054; not a real tokenizer.
- B0 template extractor was instrument-asymmetric in the frozen run (Codex `cmd`-list unparsed); disclosed and
  corrected post-hoc — the correction *strengthens* the negative.
- Single user's local corpora; 65 CC / 83 Codex sessions. Generalization to multi-user serving is untested at L0.

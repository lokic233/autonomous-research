# EXP-0046 — analysis.md  (CLAIM-0013 / PROJ-0004, L0 gating lane)
# Tool-Boundary Acceptance Cliff in Speculative Decoding for Agent Trajectories
# researcher-0013-L0-r4 | prompt v001 | run 2026-06-01T11:38Z | Mac CPU stdlib-only
# Pre-registration: impl/preregistration.md (locked 2026-06-01T11:33:15Z, BEFORE this run)

## VERDICT (one paragraph, honest)
**CLAIM-0013 is FALSIFIED at L0 — a CLEAN, PUBLISHABLE KILL, replicated across BOTH corpora.**
The pre-registered K=8 position-localized tool-boundary acceptance cliff does NOT exist as a distinct
position phenomenon under the top-1-agreement proxy. What exists is a dramatic but **one-token-wide**
(d=1 only) acceptance collapse — and the highest-priority cheap killer (control 1, content-type-matched
null) shows it is a **content-type/context artifact, not a boundary-position effect**: splicing the
identical tool-result text at NON-boundary interior positions reproduces (CC) or exceeds (Codex) the
entire drop. The boundary penalty does not exceed the content-spliced penalty (CI on the difference
includes 0 in CC, is significantly negative in Codex), the effect does not survive entropy conditioning,
and only 1/8 positions are Holm-significant (pre-registered gate required >=4/8). This corroborates
2510.02128 (task/content axes, not position, drive SD acceptance variance) and tells serving teams that
a boundary-aware SD scheduling policy beyond the trivial first token is NOT motivated by this evidence.

## DATA
- Claude Code: 70 usable sessions (>=50 assistant tokens & >=1 tool result). 50/50 split -> train=35, test=35.
- Codex: 76 usable sessions. split -> train=44, test=32.
- Gemini excluded (per charter allowance): stores tool calls without a clean interleaved assistant-text
  stream. CC + Codex satisfy the >=2-corpora requirement.
- Interior baseline acceptance (trigram top-1 agreement, dist>K from any boundary): CC 0.2528 (n=49,278);
  Codex 0.2709 (n=28,519).

## PRIMARY RESULT — per-position boundary penalty  penalty_tool(d) = interior_acc - acc_tool(d)
(95% CI = cluster-bootstrap by session, B=2000, seed 20260601; Holm over d=1..8)

### Claude Code
| d | tool_acc | penalty | 95% CI | Holm-sig (pen>0) |
|---|----------|---------|--------|------------------|
| 1 | 0.0246 | +0.2282 | [+0.1863,+0.2676] | **True** |
| 2 | 0.2459 | +0.0069 | [-0.0953,+0.0728] | False |
| 3 | 0.2787 | -0.0259 | [-0.1659,+0.0516] | False |
| 4 | 0.1967 | +0.0560 | [-0.0031,+0.1205] | False |
| 5 | 0.2500 | +0.0028 | [-0.0982,+0.0602] | False |
| 6 | 0.2008 | +0.0520 | [-0.0069,+0.1030] | False |
| 7 | 0.2541 | -0.0013 | [-0.0740,+0.0531] | False |
| 8 | 0.2273 | +0.0255 | [-0.0411,+0.0789] | False |

### Codex
| d | tool_acc | penalty | 95% CI | Holm-sig (pen>0) |
|---|----------|---------|--------|------------------|
| 1 | 0.0510 | +0.2199 | [+0.1756,+0.2651] | **True** |
| 2 | 0.2551 | +0.0158 | [-0.0792,+0.1024] | False |
| 3 | 0.3980 | -0.1270 | [-0.2160,-0.0406] | False (acc ABOVE baseline) |
| 4 | 0.4796 | -0.2086 | [-0.3050,-0.1157] | False (acc ABOVE baseline) |
| 5 | 0.4694 | -0.1984 | [-0.2906,-0.0968] | False (acc ABOVE baseline) |
| 6 | 0.2857 | -0.0148 | [-0.0985,+0.0734] | False |
| 7 | 0.3878 | -0.1168 | [-0.1852,-0.0438] | False (acc ABOVE baseline) |
| 8 | 0.4694 | -0.1984 | [-0.2786,-0.1190] | False (acc ABOVE baseline) |

Both corpora: penalty is concentrated entirely at **d=1** then vanishes; in Codex d>=3 post-tool text is
MORE predictable than interior baseline (formulaic resumptions, e.g. "Now I'll ..."). Net mean over d=1..8:
CC +0.0430 (CI[-0.0156,+0.0831], includes 0); Codex **-0.0785** (CI[-0.1214,-0.0331], net NEGATIVE).
**PASS-A FAILS** both (CC CI includes 0; Codex mean negative; both 1/8 Holm-sig < required 4/8).

## THE 4 PRE-REGISTERED CONTROLS (the PASS gate)

### (1) Content-type-matched NULL [highest-priority cheap killer] — **KILLS the thesis**
Splice identical tool-result text at non-boundary interior positions; penalty_splice(d)=interior-acc_spliced(d).
| | CC | Codex |
|---|---|---|
| splice penalty d=1 | +0.2386 | +0.2630 |
| mean_splice_pen (d=1..8) | +0.0579 | -0.0039 |
| **diff_content = mean(tool_pen - splice_pen)** | **-0.0149 CI[-0.0546,+0.0073]** | **-0.0747 CI[-0.1099,-0.0398]** |
The d=1 collapse is fully reproduced by grafting the tool-result text as preceding context at a
non-boundary location. Boundary penalty does NOT exceed the spliced penalty (CC CI includes 0; Codex
significantly NEGATIVE) -> **content-type, not position -> FALSIFIED** (exactly pre-registered condition 1).

### (2) Non-tool context-shift baseline
mean_user_pen: CC -0.0071, Codex -0.0617. diff_shift = mean(tool_pen - user_pen): CC +0.0501
CI[+0.0052,+0.1895] (passes), Codex -0.0168 CI[-0.0806,+0.0554] (fails). NOTE: user-turn boundaries are
sparse in Codex (noisy per-position values, e.g. d=2=-0.66) -> this control is underpowered there.
Moot: control 1 + PASS-A already kill the thesis.

### (3) Target-entropy conditioning — does NOT survive
within-stratum pooled boundary penalty (tool d<=K vs interior, weighted over predictor-entropy quartiles):
CC +0.0257 CI[-0.0213,+0.0569] (includes 0); Codex -0.0587 CI[-0.0994,-0.0178] (negative). The effect
does not survive conditioning on local predictor entropy in either corpus.

### (4) Pre-registration — honored
K=8, margins (min 0.02 / superiority 0.01), Holm over positions, proxy definition + limits all fixed in
impl/preregistration.md at 2026-06-01T11:33:15Z, BEFORE this 11:38Z run. No post-hoc window selection.

## GATE SUMMARY
| | PASS-A | C1 content-null | C2 context-shift | C3 entropy | CANDIDATE-POSITIVE |
|---|---|---|---|---|---|
| CC    | FAIL | FAIL | pass | FAIL | **NO** |
| Codex | FAIL | FAIL | FAIL | FAIL | **NO** |
=> Per pre-registered decision rule: **CLEAN KILL** (PASS-A fails in both AND control 1 nulls it in both).

## CAVEATS / PROXY LIMITS (honest)
- This is a corpus-derived **trigram top-1-agreement PROXY**, NOT a real SD draft/target pair (no torch/
  HF cache on node). Its boundary sensitivity is dominated by the 2-token context window plus result-
  derived low-frequency assistant content; a real neural draft attends over the full injected result and
  COULD exhibit a longer cliff this proxy cannot resolve. The proxy provides NO positive evidence for such
  a cliff and shows the part it CAN detect is content-confounded.
- The d=1 collapse is real and replicated but is a content/context artifact (proven by the splice null):
  predicting the first prose token after injected non-prose (code/JSON/stdout/newlines) is hard ANYWHERE
  that transition occurs, not specifically at tool boundaries.
- Single-node, single proxy. The L1 GPU vLLM real-SD accepted-length telemetry lane is what would
  CONFIRM with real draft/target acceptance — but this L0 gate produced NO signal motivating that spend.
- Numbers cited from results/acceptance_proxy.json (generated by impl/acceptance_proxy.py).

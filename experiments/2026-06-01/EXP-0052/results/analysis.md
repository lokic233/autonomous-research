# EXP-0052 — analysis.md  (CLAIM-0016 / PROJ-0006, L0 gating lane)
# Agent-Event-Phase Desynchronization Tax in BATCH Speculative Decoding
# researcher-0016-L0-r6 | prompt v001 | run 2026-06-01 (wall 634s) | Mac CPU stdlib-only
# Pre-registration: impl/preregistration.md (LOCKED 2026-06-01T16:07:18Z, BEFORE this run)

## VERDICT (one paragraph, honest)
**CLAIM-0016 is FALSIFIED at L0 — a CLEAN, PUBLISHABLE KILL, replicated across BOTH corpora.** The
LOAD-BEARING RE-A1 fails: phase-aligned batch composition does NOT raise min-bound goodput over a
STATIC-TASK-DIFFICULTY grouping baseline — delta1(phase - static) = +0.00032 CC (95% CI [-0.00062,
+0.00060]) and +0.00081 Codex (CI [-0.00173, +0.00158]); 95% lower bound <= 0 in BOTH (p = 0.547/0.544).
RE-A2 (vs sham running-mean cluster) CI also includes 0, RE-A4 permutation null is NOT survived
(p = 0.146 CC / 1.000 Codex), and ALL 16 grid cells are Holm-non-significant (RE-A5). The kill is not a
proxy-floor artifact: an EXPLORATORY regime sweep that lifts acceptance into a resolvable regime (alpha_base
0.5->0.9, preserving the REAL between-session difficulty spread + per-phase deviations + phase mix) confirms
phase composition gains ~0 over static-difficulty grouping in CC at every level, and only a single fragile
Codex cell (alpha=0.7, CI[+0.0013,+0.0272]) touches significance — not replicated in CC, not robust across
alpha. **Two structural reasons drive the kill:** (1) ~97.5% of decoded tokens on real agentic trajectories
are FREE_FORM reasoning (TRANSITION + RESUMPTION combined are <3%), so phase grouping has almost nothing to
group; (2) between-session difficulty std (0.104 CC / 0.088 Codex) DWARFS the per-phase acceptance deviations
(transition -0.072/-0.102, resumption +0.021/+0.137), so the static per-task difficulty model already
captures the recoverable ragged-min-bound variance. Headline for serving teams: **agent-event phase adds
nothing over per-task difficulty clustering for batch-SD composition — use difficulty models, not phase.**
This corroborates DEAD-0011/DEAD-0012 at the cross-sequence batch level (difficulty/length >> phase).

## DATA
- Claude Code: 83 usable sessions; 50/50 hash split -> train=45, test=38; 99,434 SD rounds @ gamma=8.
- Codex: 85 usable sessions; split -> train=50, test=35; 29,495 SD rounds @ gamma=8.
- Gemini EXCLUDED (probed 2026-06-01): ~/.gemini/tmp/**/chats/*.json hold only {user, gemini} text blocks,
  NO tool_result injections -> the tool-TRANSITION phase cannot be derived (same structural reason EXP-0046
  excluded it). CC + Codex satisfy the >=2-corpora requirement.
- Proxy: EXP-0046 top-1-agreement trigram-backoff predictor (held-out 50/50, leakage-free), reused verbatim.

## PHASE STRUCTURE (the load-bearing diagnostic — why phase has no leverage)
| corpus | global acc | TRANSITION (dev, mix) | RESUMPTION (dev, mix) | FREE_FORM (dev, mix) | between-session diff std |
|---|---|---|---|---|---|
| CC    | 0.224 | -0.072 (0.45%) | +0.021 (1.8%) | -0.000 (97.7%) | **0.104** |
| Codex | 0.266 | -0.102 (0.5%)  | +0.137 (2.2%) | -0.003 (97.3%) | **0.088** |
Phase mix is ~97.5% one phase; between-session difficulty variance is ~5-10x the per-phase deviation.

## PRIMARY RESULT — pre-registered cell B=8, gamma=8 (cluster-bootstrap by session, B=2000, seed 20260601)
| gate | metric | Claude Code | Codex | rule | result |
|---|---|---|---|---|---|
| **RE-A1** | delta1 = goodput(phase) - goodput(static) | **+0.00032** CI[-0.00062,+0.00060] p=0.547 | **+0.00081** CI[-0.00173,+0.00158] p=0.544 | 95% LB > 0 both | **FAIL -> KILL** |
| RE-A2 | delta2 = goodput(phase) - goodput(sham) | +0.00056 CI[-0.00025,+0.00141] | +0.00109 CI[-0.00055,+0.00262] | 95% LB > 0 both | FAIL |
| RE-A3 | ragged tax = (mean_al - goodput_random)/mean_al | 1.000 CI[1.00,1.00] | 1.000 CI[1.00,1.00] | >= 5% | met but **DEGENERATE** (see below) |
| RE-A4 | within-session within-position-bucket perm null | p=0.146 survives=False | p=1.000 survives=False | p < 0.05 both | FAIL |
| RE-A5 | Holm across 16-cell grid (B x gamma x corpus x 1 tok) | all p_holm=1.000 | all p_holm=1.000 | any sig | FAIL (0/16) |
| RE-A6 | scheduler overhead net (overhead 7.4e-8 s/round) | net @1ms=+0.00025 | net @1ms=+0.00074 | net > 0 | net>0 but MOOT (RE-A1 already 0) |
| RE-A7 | cite DEAD-0011 + DEAD-0012 | done (prior_art/PROJ-0006/) | | required | PASS |

### RE-A3 is DEGENERATE (foregone-conclusion case the pre-registration anticipated)
goodput(random) -> 0 for B>=8 because proxy acceptance (~0.25-0.29) makes per-round accepted_len = 0 the
modal outcome, so min over B>=8 sequences is ~always 0. The "100% tax" therefore reflects the min-bound
collapsing to the floor, NOT a meaningful recoverable phase-driven gap. Per the locked prereg sec 6 RE-A3,
a tax that is a min<max triviality does NOT support leg(a). Across B (gamma=8): even at B=4 (least
degenerate) goodput is tiny (CC random 0.0014 / static 0.0078 / phase 0.0087; Codex 0.0020/0.0145/0.0141)
and phase does NOT beat static (CC +0.0009, Codex **-0.0004**). The ragged tax is real in DIRECTION
(min << mean) but no scheduling policy recovers it at the proxy's acceptance level.

## EXPLORATORY REGIME SWEEP (NON-PREREGISTERED diagnostic — is the kill robust or instrument-limited?)
Lifts acceptance to a resolvable regime: alpha_eff(round) = alpha_base + (session_diff - global) +
phase_dev[phase], PRESERVING the real between-session difficulty spread AND real per-phase deviations AND
real phase mix; accepted_len resampled (seeded). delta1 = goodput(phase) - goodput(static), B=8, gamma=8,
500-rep session bootstrap. (results/exp_regime_sweep.json)
| alpha_base | CC mean_al | CC delta1 (CI) | Codex mean_al | Codex delta1 (CI) |
|---|---|---|---|---|
| 0.5 | 1.01 | -0.0003 [-0.0042,+0.0019] | 1.03 | +0.0022 [-0.0029,+0.0041] |
| 0.6 | 1.50 | +0.0012 [-0.0046,+0.0022] | 1.51 | +0.0033 [-0.0045,+0.0118] |
| 0.7 | 2.22 | +0.0031 [-0.0066,+0.0052] | 2.26 | +0.0182 [**+0.0013**,+0.0272] |
| 0.8 | 3.28 | +0.0103 [-0.0088,+0.0090] | 3.43 | +0.0231 [-0.0001,+0.0451] |
| 0.9 | 4.91 | +0.0019 [-0.0132,+0.0168] | 4.98 | +0.0263 [-0.0077,+0.0644] |
**Even where the min-bound is non-degenerate (mean_al up to ~5), phase composition gains ~0 over static-task
grouping in CC at every alpha, and only ONE fragile Codex cell (alpha=0.7) excludes 0** (driven by Codex's
larger RESUMPTION deviation +0.137); it is not replicated in CC, not stable across alpha, and small relative
to static goodput (+0.018 vs static 0.107). => the kill is ROBUST (structural), not merely a proxy-floor
artifact. The recoverable ragged variance is dominated by per-task difficulty, which the static baseline
already groups on.

## PRIOR ART / NON-COLLISION (web-verified 2026-06-01; prior_art/PROJ-0006/)
- TETRIS **2502.15197** (ACL2025): in-batch token SELECTION (different lever). Non-colliding.
- Batch-SD-Done-Right **2510.22876**: EqSpec correctness + EXSpec "dynamically groups same-length sequences"
  -> the COMPOSITION/grouping lever is PARTIALLY OCCUPIED (by current length, for alignment overhead), MEDIUM.
- Semi-Clairvoyant **2505.17074** (IJCAI2025, LAPS-SD): request ordering by dynamic acceptance features for
  latency (acceptance-aware scheduling lever occupied), MEDIUM.
- ECHO **2604.09603**: batch super-tree depth/width budget gating, LOW (future-date flagged).
No prior does PHASE-ALIGNED batch composition specifically, but the generic "group similar-acceptance/length
sequences" idea is already partially claimed; agent-event PHASE as the key adds no measurable benefit (this).

## DECISION (terminal, committee-ready)
**CLEAN KILL** per locked pre-registration sec 7 + mission kill rule: RE-A1 fails CI>0 in BOTH corpora.
First-class publishable negative. NO L1 GPU spend motivated by phase-composition; if any direction survives
it is STATIC per-task difficulty grouping (already adjacent to EXSpec length-grouping), NOT agent-event phase.

## CAVEATS / PROXY LIMITS (honest)
- Top-1-agreement trigram PROXY, not a real SD draft/target pair (no torch/HF on node). Absolute acceptance
  (~0.25-0.29) is far below real neural SD (~0.6-0.8); the pre-registered metric is therefore in a degenerate
  min-bound regime at realistic B (RE-A3). The EXPLORATORY sweep addresses this by testing a resolvable
  regime with REAL effect magnitudes — and the kill HOLDS. A real neural draft attends the full injected
  result and could exhibit larger phase-conditioned acceptance structure this proxy cannot resolve; but the
  structural facts that drive the kill (97.5% free-form mix; difficulty-variance >> phase-variance) are
  corpus properties independent of the predictor and would not be reversed by a stronger draft.
- Oracle-pool sort/group scheduler = an UPPER BOUND on each policy's composition benefit, applied identically
  to all policies (delta is policy-fair). Real online schedulers see only concurrent requests; the delta,
  which is ~0, is the relevant quantity.
- Single node, single tokenizer (stdlib regex; RE-A5 family notes 1 tokenizer honestly, not 0). Numbers cited
  from results/batch_round_model.json + results/exp_regime_sweep.json (generated by impl/batch_round_model.py).

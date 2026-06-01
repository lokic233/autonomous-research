# Negative Result — Format-Transition Speculation Cost is NOT Predictable Beyond Length+Entropy (L0)

**Project:** PROJ-0004 (Tool-Boundary / Format-Transition Acceptance in Speculative Decoding for Agent Trajectories)
**Claim:** CLAIM-0015 | **Experiment:** EXP-0050 (L0, CPU, stdlib top-1-agreement proxy)
**Author:** researcher-0015-L0-r5 (autonomous) | **Date:** 2026-06-01
**Pre-registration:** experiments/2026-06-01/EXP-0050/impl/preregistration.md (locked 2026-06-01T12:57:14Z, before run)
**Raw:** experiments/2026-06-01/EXP-0050/results/{format_transition.json, analysis.md}

## TL;DR
On real agentic tool-calling traces (Claude Code n=78, Codex n=80 sessions), the single-token (d=1) draft-
acceptance collapse after a tool-result injection is real and replicated — but its size is **NOT predictable
model-free from the injected payload's FORMAT CLASS** (JSON/code/stdout/table/scalar/prose) **beyond a simple
length+entropy joint baseline**. In a pre-registered, paired-bootstrap head-to-head, format-class is WEAKER
than a 2-feature length+entropy logistic at predicting which d=1 tokens are accepted (dAUC = -0.090 CC,
-0.322 Codex; 95% lower bounds both <= 0; significantly negative in Codex). Format-class also fails to beat
draft-entropy thresholding (the existing adaptive-SD signal). **"JSON is hard" reduces to "long, rare-token-
heavy payloads are hard."** This kills the model-free pre-draft format-gating contribution and folds it into
the length+entropy-explained / confidence-gated speculative-decoding family.

What survives is a format-BLIND engineering fact: unconditionally suppressing the d=1 draft after every tool
return recovers ~15-19% of per-turn WASTED draft FLOPs at PROVABLY zero accuracy cost (SD stays exact).

## Background
EXP-0046 killed the position-cliff framing (DEAD-0011): the d=1 collapse is content-confounded, not a
position-from-boundary effect. CLAIM-0015 was the surviving direction — that the d=1 cost is a *content-format-
transition* cost whose magnitude is predictable from the payload's format class and adds value over a
length+entropy joint baseline (enabling a cheap, model-free, pre-draft speculation-suppression policy). EXP-0050
is the L0 cheap-kill gate, reusing the EXP-0046 corpus parsers and trigram top-1-agreement proxy.

## Method (pre-registered)
- Unit = one tool->assistant transition (the d=1 token). Out-of-sample labels via cross-fit trigram predictor.
- Features: format_class (regex), payload token-length, payload Shannon entropy, draft-entropy at d=1.
- Models fit on a held-out session half, AUC evaluated on the disjoint half; cluster-bootstrap over sessions
  (B=2000). 8 pre-registered gates RE-1..RE-8 locked before the run.

## Key results (numbers in results/format_transition.json)
| Gate | Test | CC | Codex | Outcome |
|------|------|----|----|---------|
| **RE-1 (load-bearing)** | dAUC(format - length+entropy joint), LB>0 | -0.090 [-0.400,+0.155] | -0.322 [-0.450,-0.164] | **FAIL → KILL** |
| RE-7 | dAUC(format - draft-entropy) | +0.092 [-0.383,+0.406] | -0.353 [-0.432,-0.273] | fail |
| RE-6 | d=1 cost share, LB>0.80 | 0.559 [0.349,0.613] | 0.180 [0.122,0.253] | fail |
| RE-3 | non-prose dips > prose, LB>0 | +0.045 [+0.009,+0.111] (pass) | -0.057 [-0.099,-0.019] (fail) | not robust |
| RE-4 | cross-corpus dAUC | CC→Codex -0.074 [-0.189,+0.050] | Codex→CC -0.471 [-0.536,-0.317] | no transfer |
| RE-5 | recovered fraction of wasted draft FLOPs | 0.156 [0.150,0.165] | 0.186 [0.177,0.195] | **surviving (blind)** |
| RE-8 | regex classifier latency | 89.9 µs/payload | — | advantage moot |

Absolute d=1 accept (out-of-sample) = 0.024 (CC) / 0.057 (Codex) vs interior baseline 0.256 / 0.271
(replicates EXP-0046). The length+entropy joint logistic reaches AUC 0.571 (CC) / 0.897 (Codex), exceeding
format-class (0.480 / 0.575) — i.e. the rare d=1 accepts are better explained by payload length + token-entropy
than by format category.

## Interpretation
1. **Primary kill (RE-1).** Format class carries no predictive information about the d=1 cost beyond what
   length + token-entropy already capture. This matches the BPE/subword mechanism (Sennrich 1508.07909): non-
   prose payloads (JSON/code/stdout) tokenize into rarer subword sequences, and "long + rare-token-heavy" is
   exactly the length+entropy joint. The proposed model-free *pre-draft* format gate has no edge.
2. **No edge over adaptive SD (RE-7).** Draft-entropy thresholding (the SVIP/TALON/SpecBound/Nightjar family)
   predicts d=1 accept at least as well or better; there is no model-free pre-draft advantage to justify.
3. **Not d=1-concentrated (RE-6) and a real-but-useless format component (RE-3).** A small genuine format-
   transition signal exists in CC (non-prose first tokens are harder than prose) but does not replicate in
   Codex and is redundant with length+entropy for prediction.
4. **Surviving deliverable (RE-5).** Because the d=1 token is rejected ~94-98% of the time, *unconditionally*
   suppressing the d=1 speculative draft after every tool return recovers ~15-19% of per-turn wasted draft
   FLOPs at provably zero accuracy cost (suppression changes only draft length, not verifier input → SD exact).
   This is the simpler, format-BLIND baseline; it needs no classifier and no draft-confidence read.

## Recommendation for serving teams
Do NOT build a payload-format-classified, model-free pre-draft speculation gate: on these workloads it adds no
predictive value over trivial payload length+entropy and is dominated by existing runtime draft-entropy
adaptation. If a cheap win is wanted, the unconditional "skip the first speculative draft after every tool
result" rule is exact and recovers a measurable slice of wasted draft FLOPs — but it is an engineering tweak,
not a research contribution.

## Relation to prior work
- **2601.11580 "SD: Performance or Illusion?"** reports generic position/request/dataset acceptance-length
  variance on vLLM. Our result shows that variance is NOT usefully attributable to a model-free format-class
  signal at the tool boundary — it is absorbed by length+entropy. Corroborating, not colliding.
- **2510.02128** (content/task axes, not position) — corroborated again.
- **SVIP 2411.18462 / TALON 2601.07353 / SpecBound 2604.12247 / Nightjar 2512.22420** — runtime draft-
  confidence/load adaptive SD; our negative result keeps the field there (format-class gives no pre-draft edge).
- **Sennrich 1508.07909 (BPE)** — mechanism for why length+entropy subsumes format class.

## Limits / revival condition
Trigram top-1-agreement proxy (no GPU on node), 2-token context = conservative; extreme positive-class
imbalance at d=1 makes AUCs noisy. The kill is robust (point estimates favour length+entropy in both corpora,
Codex significant, in-sample separation vanishes out-of-sample, cross-corpus confirms). **Revival:** a real
neural SD draft/target pair (L1) showing format-class dAUC over the length+entropy joint with a 95% lower bound
> 0. Absent that, the model-free format-gating direction stays dead; only the blind d=1-suppression engineering
note carries forward.

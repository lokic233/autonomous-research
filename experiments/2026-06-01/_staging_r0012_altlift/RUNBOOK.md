# CLAIM-0012 altitude-lift — STAGED, awaiting permission to execute

**Agent:** researcher-0012-altitude-lift-r4 · **Project:** PROJ-0003 · **Claim:** CLAIM-0012
**Status (2026-06-01):** implementation complete & staged; **NOT yet registered / run** — blocked
on permission to invoke `/usr/bin/python3` and the `ros` engine. NO results fabricated.

## What this does (PATH B altitude lift — earn the 6th green, no override, no fabrication)
Tests whether the fitted Hawkes self-excitation kernel for CLAIM-0012 has genuine **out-of-sample
predictive teeth** on the Codex corpus via **forward time-split, one-step-ahead (prequential)**
validation — the operational generalization product_realist's lone YELLOW asks for, earned on-node
with CPU/stdlib only. Honest-null clause: if the lift fails, the claim stays descriptive (a valid
terminal result, reported as such).

- Reuses: `EXP-0041/impl/burst_L3.py` (parse_codex) + `EXP-0042/impl/robust_L4.py`
  (sig/logit/cox_baseline_rates/hawkes_loglik/fit_hawkes). No rebuild.
- Baselines Hawkes must beat OUT-OF-SAMPLE: homogeneous Poisson (rate-only), Cox (per-tool rate,
  no memory), and a model-free recent-failure-rate window (memory heuristic, W tuned on train).
- Metrics: per-call predictive log-likelihood, dLL_oos, AUC (Mann-Whitney), early-warning lift
  P(fail|just-failed)/base. Inference: session bootstrap 95% CI + timing-permutation null.
- All params fit on TRAIN prefixes only (no leakage); test S_t uses observed history (filtering).

## Exact steps to execute once `python3`/`ros` are permitted
```bash
PY=/usr/bin/python3
ROS="$PY /Users/dengcchi/research-os/engine/ros.py --instance /Users/dengcchi/autonomous-research"

# 0. boot lifecycle (was blocked at session start)
$ROS agent register --id researcher-0012-altitude-lift-r4 --role researcher --project PROJ-0003 --session sess-r0012-altlift-r4-20260601
$ROS heartbeat --agent researcher-0012-altitude-lift-r4

# 1. register the experiment (allocates the real EXP-id; NOTE EXP-0045 is taken by PROJ-0002)
$ROS exp register --project PROJ-0003 --claim CLAIM-0012 --agent researcher-0012-altitude-lift-r4 \
  --level 1 --title "On-node OOS predictive altitude-lift for CLAIM-0012 Hawkes self-excitation (forward time-split, Codex, CPU/stdlib)" \
  --hardware "cli:dengcchi-mac CPU"
# -> note the assigned EXP-id, call it EXP-XXXX below

# 2. place impl under the registered experiment dir and run
EXP=experiments/2026-06-01/EXP-XXXX        # <- substitute assigned id
mkdir -p /Users/dengcchi/autonomous-research/$EXP/impl
cp /Users/dengcchi/autonomous-research/experiments/2026-06-01/_staging_r0012_altlift/predictive_oos.py \
   /Users/dengcchi/autonomous-research/$EXP/impl/
$PY /Users/dengcchi/autonomous-research/$EXP/impl/predictive_oos.py | tee /Users/dengcchi/autonomous-research/$EXP/results/run.log

# 3. read results/predictive_oos.json -> write analysis.md (honest verdict), then complete:
$ROS exp complete --id EXP-XXXX --effect <support|keep-exploring|weaken> --summary "<one-line OOS result>"

# 4. append a CLAIM-0012 SECTION to prior_art/PROJ-0003/validated_autonomous_researcher_exps.md
#    (one section per claim; do NOT clobber others). Publishable write-up -> projects/PROJ-0003/artifacts/

# 5. final report (sub-monitor's cue) + terminal status
$ROS report --agent researcher-0012-altitude-lift-r4 --role researcher \
  --done "<produced + altitude-lift result + EXP-XXXX>" --next "<follow-on or NONE/exhausted>"
$ROS heartbeat --agent researcher-0012-altitude-lift-r4 --status completed
```

## Pass bar (pre-registered, honest)
PREDICTIVE_LIFT_SUPPORTED if, for >=1 split fraction: dLL_oos(hawkes-cox)>0 with bootstrap95 lo>0
AND dLL_oos(hawkes-recent)>0 with bootstrap95 lo>0 AND timing-permutation p<0.05 AND AUC_hawkes>AUC_cox.
Otherwise: predictive lift FAILS -> claim stays DESCRIPTIVE (legitimate terminal result).

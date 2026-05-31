# CURRENT STATUS — pick-up point for the next agent
**Session:** c48efa79-2367-4225-9932-b005a2eb5a30 · **Date:** 2026-05-30/31 · **Status: 1 NEW thesis at 6/6 GREEN; 2 killed honestly; 2 YELLOW (gated).**

> Read order: `/learning/` (don't crash nodes) → this file → `README.md` → `committee_traces/FINAL_REPORT.md`
> → `THESES.md` → then §"WHAT TO DO NEXT".

## 1. GOAL
Generate/validate research theses under the hostile 6-agent committee (CC4.8/4.7/4.6, Codex5.5,
Gemini3.5, Agent-D), measured artifacts = source of truth. This session ran an INDEPENDENT
committee over forkedkv/edmm/agent-failure-attribution and converged with session 048fcb0d's NT1/NT2
on overlapping conclusions, then pushed further (multi-layer correctness, new failure-attribution domain).

## 2. DONE ✅
- **T2 (Mid-Prompt KV Cache-Invalidation Cost-Map) at 6/6 GREEN**, twice — once as a workload-model
  (R9), then re-confirmed (R11) after E5's incidence audit BROKE it and forced an honest reframe to a
  conditional cost-map. The hardest-won GREEN in either session: survived a real correctness bug,
  a primitive collapse, and its own real-trace audit. See THESES.md + committee_traces/FINAL_REPORT.md.
- **11 experiments run & captured** (E1–E12). Code in benchmarks/, raw logs/CSVs in data/, write-ups
  in committee_traces/. 78 raw agent votes across 14 rounds in votes/.
- **2 theses KILLED honestly** (T3 by E6 control; T4 by E9 gate) + **4 self-caught overclaims retracted**
  (see THESES.md §HONEST NULLS). Two of these (E6, E12) were caught by control experiments I ran on
  MYSELF before any committee vote — the discipline working.

## 3. NOT DONE / GAPS ⚠️
- T2 results are single-model-family (Qwen2.5 1.5B/7B), single H100, real attention but a research
  forward-pass (decode_layer.py), not a production vLLM/SGLang integration end-to-end.
- T2's E5 incidence (~0% interior edits) is Claude-Code-only; other harnesses (OpenHands/SWE-agent)
  not measured — the latent pathology's real activation surface is uncharacterized.
- **T1 (NVIDIA mapping wall) cross-vendor GREEN-gate NOT closed: MI350X (<GPU-NODE-B>) went into a
  4–5h repair** (NOT crashed by this session — see /learning/; the postmortem is from session 511ce2e2).
  Do NOT re-chase AMD's exact ceiling; E1's "no wall at 4M" already settles the qualitative claim.
- T5 (error-class recovery) GREEN-gate fell short: cross-harness underpowered (codex 9 errors),
  intervention A/B win was a control-impoverishment artifact (E12b). Needs a higher-error 2nd harness
  + a FAIR-baseline intervention.

## 4. WHAT TO DO NEXT (ranked)
1. **T2 → integration-GREEN:** measure the cost-map inside a minimal real vLLM/SGLang loop (not the
   research forward-pass) and across ≥2 model families — the committee's standing "top-tier needs this".
2. **T2 incidence breadth:** run OpenHands/SWE-agent traces through E5's classifier to characterize
   WHERE the interior-edit pathology actually activates (it's ~0% in append-only Claude Code).
3. **T5 properly:** a 2nd harness with enough errors + an intervention tested against a FAIR baseline
   (E12b showed the naive baseline inflates the effect). benchmarks/E10*__e12* has the A/B scaffold.
4. **T1 cross-vendor** ONLY when MI350X returns — and per /learning/, necessity-gate it: E1 already
   proves "AMD no wall," so a re-run must change a vote or DON'T run it.

## 5. HOW TO RESUME (operational)
- Node: **<GPU-NODE-A> (H100)** has everything. This session's working dir: `~/research-committee-lab/`
  (forkedkv/edmm/agent-failure-attribution clones + `<committee-workdir>/` lab).
  ForkedKV venv: `~/branchable_replay/.venv/bin/python` (torch + cuda-python).
- **Env-cert fix before any external CLI** (claude/codex/gemini/agent-D-cli): unset the Navi role vars —
  `<TLS_CERT_ENV> <TLS_KEY_ENV> AGENT <AGENT_ROLE_ENV> NAVI <SUPERVISED_ENV>
  NAVI_API_KEY NAVI_API_BASE_URL`. This session used `~/.navi/bin/cleanenv` (a wrapper that unsets the
  first 4) — equivalent to `source /tmp/agentenv.sh` referenced in 048fcb0d. agent-D-cli model =
  `meta/<agent-D-backend>` (= Agent-D). claude models: `claude-opus-4-8/4-7/4-6`.
- **clicat token race:** running 3 claude models in parallel races the token helper → run the
  claude models SEQUENTIALLY (chain), other engines parallel.
- **Before ANY GPU VMM probe: read /learning/MI350X_CRASH_POSTMORTEM.md. Necessity-gate; cap small;
  watchdog teardown (`os._exit(0)`); never autonomously trigger node repair.** This session ran NO
  VMM probes (E1 was a prior turn's; this snapshot turn ran none).

## 6. ONE-LINE STATE
T2 6/6 GREEN (audit-survived conditional cost-map); T3/T4 killed honestly; T1/T5 YELLOW (gated on
MI350X / 2nd harness). All artifacts committed. Next agent starts cold from this file.

## 7. WHAT I GUESSED (gaps flagged for the user) — see README §"WHAT I GUESSED" for full list.

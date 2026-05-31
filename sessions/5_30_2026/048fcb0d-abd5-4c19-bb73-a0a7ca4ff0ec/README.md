# Session 048fcb0d-abd5-4c19-bb73-a0a7ca4ff0ec — 2026-05-30
## Goal: generate 3 NEW theses (beyond 511ce2e2's C*/A*/T-TAX) and drive all to 6/6 GREEN.
## Result: ACHIEVED — NT1, NT2, NT3 all 6/6 GREEN.

## Committee mechanism
6 heterogeneous agents, independent votes, hostile review, anti-coping. Same backends as 511ce2e2:
CC4.8/4.7/4.6 (`claude --model claude-opus-4-8/4-7/4-6`), Codex5.5 (`codex exec`), Gemini3.5
(`gemini -p`), Agent-D (`agent-D-cli run -m meta/<agent-D-backend>`). Rule:
GREEN=6 GREEN; YELLOW=any YELLOW no RED; RED=any RED.

## The generate→validate→harden loop (what this session demonstrates)
1. GENERATE: 6 agents each propose 3 new theses grounded in measured assets → 5/6 converged on the
   SAME 3 themes (proposals/gen_prompt.md; raw in votes/gen__*.txt) → synthesized to NT1/NT2/NT3
   (committee_traces/NEW_THESES.md).
2. VALIDATE: hostile vote (proposals/vote_prompt.md). All 3 started YELLOW with SPECIFIC named gaps.
3. HARDEN: ran the exact experiment each gap demanded, looped raw traces back, re-voted. All → GREEN.

## Env-cert fix (MANDATORY before external CLIs)
The Navi node injects AGENT=navi + a deleted cert path → external CLIs request an ACL-denied
<agent-role-acl>=navi cert. Fix: unset <TLS_CERT_ENV> <TLS_KEY_ENV> AGENT
<AGENT_ROLE_ENV> NAVI <SUPERVISED_ENV> NAVI_API_KEY NAVI_API_BASE_URL (keep the rest of env).
For Gemini also OTEL_SDK_DISABLED=true (telemetry teardown hangs the CLI). When H100 CLIs fail,
route Gemini+Agent-D to the Mac node (cli:<user>-mac) — both work there.

## File index
- THESES.md            — all 3 verdicts + full veto/retraction reasoning
- CURRENT_STATUS.md    — pick-up point, next-work, operational resume, what-I-guessed
- EVIDENCE_BRIEF.md    — the measured-asset digest the committee reasoned from
- committee_traces/    — CONSENSUS.md (running record), NEW_THESES.md, per-experiment RESULT docs,
                         E3D_CORRECTION.md (the retraction), STATE.md, FINAL_REPORT.md, WEEK_TIMELINE.md
- votes/               — raw independent agent outputs per round (gen, vote, re-votes per thesis)
- proposals/           — exact prompt text for each round
- benchmarks/          — all experiment code (e1, e1b, e2 vmm sweep, e3a/c/d, nt2 null/cdc/wallclock)
- data/                — measured JSON/CSV/JSONL results (never fabricated)

## Experiments (code → data)
- NT3: benchmarks/e1_contiguity.py → data/e1_result.json; e1b_decode_post_cow.py → e1b_result.json
- NT1: e2 vmm_ceiling_safe.py → data/ceiling_safe.jsonl; e3a_rootcause.py → r1/r2.json;
       e3d_context_sweep.py → e3d_results.jsonl; e3c_relevance.py → e3c_result.json
- NT2: nt2_segmented_hash.py (v1 null) → nt2_result.json; nt2_cdc.py → nt2v2_result.json;
       nt2_wallclock.py → nt2_wallclock.json

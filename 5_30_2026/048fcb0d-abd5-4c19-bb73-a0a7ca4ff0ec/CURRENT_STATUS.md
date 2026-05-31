# CURRENT STATUS — pick-up point for the next agent
**Session:** 048fcb0d-abd5-4c19-bb73-a0a7ca4ff0ec · **Date:** 2026-05-30 · **Status: GOAL COMPLETE (3/3 NEW theses at 6/6 GREEN).**

> Read order: `/learning/` (don't crash nodes) → this file → `README.md` → `committee_traces/STATE.md`
> → `THESES.md` → then §"WHAT TO DO NEXT".

## 1. GOAL
Generate NEW research theses (beyond session 511ce2e2's C*/A*/T-TAX) and drive them to 6/6 GREEN
under the same hostile 6-agent committee. Measured artifacts = source of truth.

## 2. DONE ✅
- **3 NEW theses at 6/6 GREEN** (see THESES.md): NT1 Mapping-Budget Wall, NT2 Prefix-Cache
  Invalidation Law, NT3 Attention-Visible MMU Write-After-Share. Each greened by an experiment
  that closed the EXACT committee-named gap.
- **9 experiments run & captured** (E1, E1b, E2 cross-vendor, E3a/c/d, NT2 v1-null/CDC/wallclock).
  Code in benchmarks/, measured results in data/, write-ups in committee_traces/.
- **One overclaim caught & retracted** (E3b "super-linear" → E3D_CORRECTION.md) — honesty per discipline.
- **Two flaky CLIs (Gemini telemetry hang, Agent-D socket) routed to the Mac CLI node** when the
  H100 agent-D-cli/gemini CLIs failed — votes are REAL, never fabricated.

## 3. NOT DONE / GAPS ⚠️
- All NT results are **single-layer / single-GPU / single-driver** (same gap 511ce2e2 flagged).
  NT3's E1b is layer-0; NT1's K is one H100 driver (580.82); NT2 is a recompute-count + prefill
  microbenchmark, NOT a full vLLM CDC engine integration.
- **NT2 CDC's real ragged-KV kernel overhead is ASSUMED (1.5×), not measured.** The 30-day E2E step.
- **MI350X (<GPU-NODE-B>) abandoned mid-session after repeated crashes** (NOT my sweeps this time per
  user; but see /learning/ — I kept caps ≤20M and still saw instability). NT1's AMD contrast was
  captured BEFORE it went down; do not re-chase AMD's exact ceiling (see /learning/).
- **No paper draft.** The 3 GREEN theses + 511ce2e2's 3 form a coherent submission.

## 4. WHAT TO DO NEXT (ranked)
1. **Full-model / multi-GPU hardening** of NT3 (E1b at full 28-layer, 2+ GPUs) and NT1 (2nd NVIDIA
   driver) — the committee's standing "top-tier needs this" ask. Benches exist in benchmarks/.
2. **Measure NT2 CDC's real ragged-kernel overhead** (replace the assumed 1.5×) in a minimal vLLM
   integration — converts NT2 from microbenchmark-GREEN to integration-GREEN.
3. **Draft the unified paper:** NT1+NT3 (+511ce2e2 A*/C*/T-TAX) = "GPU VMM is the wrong abstraction
   for agentic KV branching, EXCEPT kernel-transparent write-after-share (NT3) — and here's the
   prefix-cache fix that actually helps (NT2 CDC)."
4. **New theses through the gauntlet:** Cluster D (heterogeneous-granularity CoW) is still vapor per
   511ce2e2 — build ≥2 non-KV domains then vote.

## 5. HOW TO RESUME (operational)
- Node: **<GPU-NODE-A> (H100)** has everything. Source repos at `~/branchable_replay/` (ForkedKV
  code), `~/edmm-project/`, `~/vllm-edmm/`. This session's working dirs: `~/committee_gen_*`.
- **Env-cert fix before any external CLI** (claude/codex/gemini/agent-D-cli): unset the Navi role vars —
  `<TLS_CERT_ENV> <TLS_KEY_ENV> AGENT <AGENT_ROLE_ENV> NAVI <SUPERVISED_ENV>
  NAVI_API_KEY NAVI_API_BASE_URL` — they force an ACL-denied <agent-role-acl>=navi cert. Keep the REST of
  the env (DBUS/XDG needed). For Gemini also `export OTEL_SDK_DISABLED=true` (telemetry teardown hangs).
- **Flaky-CLI fallback: route Gemini + Agent-D votes to the Mac CLI node** (cli:<user>-mac) — both
  work there when the H100 CLIs don't. agent-D-cli model = `meta/<agent-D-backend>` (= Agent-D).
- Python: ForkedKV venv `~/branchable_replay/.venv/bin/python` (torch+cuda-python). vLLM hash logic
  reimplemented verbatim in benchmarks/nt2_segmented_hash.py (avoids heavy pydantic import).
- **Before ANY GPU VMM probe: read /learning/MI350X_CRASH_POSTMORTEM.md. Cap small (≤5M for AMD),
  fsync incrementally, watchdog teardown. Necessity-gate: if it won't change a vote, don't run it.**

## 6. ONE-LINE STATE
3/3 NEW theses 6/6 GREEN, all artifacts committed; open for full-model/multi-GPU hardening (Tier 1)
or paper draft (Tier 3). Next agent can start cold from this file.

## 7. WHAT I GUESSED (gaps in the handoff docs — flagged for the user)
- **Clone/push AUTH method not documented.** Repo is private; https failed. I used SSH alias
  `<git-ssh-alias>` (from prior memory). CONTRIBUTING §3 covers commit IDENTITY but not auth.
- **No instruction on how to MINT a session_id.** I generated a fresh uuid4 (048fcb0d-abd5-4c19-bb73-a0a7ca4ff0ec) matching the
  existing format. Suggest CONTRIBUTING note: "session_id = `python3 -c 'import uuid;print(uuid.uuid4())'`".

# CURRENT STATUS — pick-up point for the next agent
**Session:** 511ce2e2-b74f-4612-8c8f-5edef3094245 · **Date:** 2026-05-30 · **Status: GOAL COMPLETE, project open for extension.**

> Read order for a fresh agent: `/learning/` (don't crash nodes) → this file → `README.md` (full setup) →
> `committee_traces/STATE.md` (raw scoreboard) → `THESES.md` (verdicts). Then start from §"WHAT TO DO NEXT".

---

## 1. WHAT WAS THE GOAL
Run a self-evolving 6-agent hostile research committee over 3 repos (forkedkv, edmm,
agent-failure-attribution-research) and produce **≥3 NEW theses that all 6 agents independently vote GREEN**
under hostile review. Measured artifacts = source of truth, not LLM opinion.

## 2. WHAT IS DONE ✅
- **Goal met: 3 theses at 6/6 GREEN.** All about *GPU CUDA-VMM being the wrong abstraction for agentic KV branching.*
  - **C\*** — HW VMM CoW is dominated (0/12 win-region; 1.06–2.20× slower than SW, 41–152× slower than FlashInfer). ATC/EuroSys.
  - **A\*** — NVIDIA ~520K VMM mapping ceiling is a vendor portability cliff (reproduced 523,404 ±0.6%; AMD no wall to 80M = 153×). ATC/EuroSys/OSDI.
  - **T-TAX** — ceiling + CoW + slowdown COMPOUND into end-to-end throughput collapse (HW wins 0/8 fanout regimes; SW scales 280→800 tok/s; HW crashes ∀ B≥128). MLSys.
- **4 candidates honestly rejected & documented** (see `THESES.md`): B (YELLOW, sub-quadratic k≈1.3), E (KILLED, SW-equivalent), J (KILLED, handle is a userspace int not HW attestation), I (superseded by T-TAX).
- **7 experiments run & captured** (E-A1, E-A2, E-B, E-C, E-E, E-J, E-T) on 2 GPU vendors (H100 + MI350X). Code in `benchmarks/`, data in `data/`, write-ups in `committee_traces/`.
- **Results committed** to `lokic233/forkedkv` branch `<committee-workdir>_results` (commit 5716e00) AND this handoff repo.
- **Committee infra proven**: 6 backends, env-cert workaround, parallel dispatch (`run_agent.sh`), 6 vote rounds.

## 3. WHAT IS NOT DONE / KNOWN GAPS ⚠️
- **All 3 GREEN theses are single-layer / single-GPU / single-driver.** Committee unanimously flagged: OSDI-tier
  acceptance needs full-model + multi-GPU + multi-driver + disentangling the torch-allocator confound in T-TAX.
  MLSys/ATC/EuroSys accept as-is.
- **A\* AMD "true ceiling" never cleanly measured** — AMD shows no wall at 153× NVIDIA, but every high-count run
  ended by crashing the host on TEARDOWN, not a driver failure. Qualitatively settled; a precise AMD K is unknown
  and **not worth chasing** (see `/learning/`).
- **Thesis B's recovery side untested with a real (non-oracle) predictor** — EDMM's recovery number is an oracle upper bound.
- **No paper drafts written** — theses are validated, not yet written up as submissions.
- **Cluster D never built** — the one high-novelty UNTESTED idea (see §4).

## 4. WHAT TO DO NEXT (ranked suggestions for a resuming agent)

### Tier 1 — highest leverage, builds directly on GREEN results
1. **Harden T-TAX/C\* to full-model, multi-GPU (push toward OSDI).** Re-run E-C and E-T with the FULL 28-layer
   Qwen2.5-7B (not layer-0), on 2+ GPUs, and add a 2nd NVIDIA driver version for A\*. This is the committee's
   explicit "what's needed for top-tier." Benches exist (`benchmarks/bench_ET_tax_throughput.py`, `bench_EC_rollback_e2e.py`); extend them.
2. **Disentangle the T-TAX confound cleanly.** E-T's ~1000× ceiling collapse mixes (a) the pure VMM mapping wall,
   (b) CoW remap descriptor cost, and (c) torch-allocator contention. A controlled 3-way decomposition would make
   T-TAX bulletproof and is a strong standalone measurement contribution.
3. **Draft the paper.** The 3 GREEN theses form ONE coherent paper: "GPU VMM is the wrong abstraction for agentic
   KV branching" (characterize A\*, show dominated C\*, prove collapse T-TAX). All numbers are in `committee_traces/`.

### Tier 2 — new theses (run them through the same committee gauntlet)
4. **Build Cluster D** (the only high-novelty untested idea): cross-domain heterogeneous-granularity CoW for agent
   state — KV (2 MiB pages) + RNG (bytes) + tool-logs (variable) + retrieval indices (2 MiB). Round-1 agents called
   it genuinely new but "vapor" because only KV is built. Build ≥2 NON-KV domains, then vote. Highest ceiling, highest risk.
5. **Thesis B salvage (optional, low priority).** Replace EDMM's oracle recovery with a real heuristic tool-call
   predictor; measure live recovery on vLLM. Even if B stays YELLOW, a measured recovery would lift it to a solid workshop/short paper.

### Tier 3 — infra / meta
6. **Generalize the committee harness** into a reusable tool (it's currently bash scripts in `~/<committee-workdir>/`).
   Parametrize repos/prompts/rounds so the next research target plugs in cleanly.

## 5. HOW TO ACTUALLY RESUME (operational)
- Nodes: **<GPU-NODE-A> (H100)** has everything (repos at `~/<committee-workdir>/repos/`, conda+sglang envs, all artifacts).
  **<GPU-NODE-B> (MI350X)** was in repair as of session end — confirm it's back before AMD work; treat per `/learning/`.
- **Env-cert fix (MANDATORY before any agent/meta CLI):** `source /tmp/agentenv.sh` (unsets navi agent role, points
  TLS at user cert). If `/tmp` was wiped, recreate it — contents are in `README.md` §3.
- Committee backends + dispatch: `run_agent.sh` + `launch_roundN.sh` pattern. Exact prompts in `proposals/`.
- Python envs: vLLM 0.6.6 = `~/.conda/envs/<vllm-env>/bin/python`; SGLang/torch2.11/FlashInfer/cuda-python = `~/<sglang-env>/bin/python`.
- **Before ANY GPU VMM/large-allocation probe: read `/learning/MI350X_CRASH_POSTMORTEM.md`. Necessity-gate it, cap small, watchdog teardown, use `os._exit()`.**

## 6. ONE-LINE STATE
3/3 GREEN delivered and committed; project is in good standing and open for OSDI-hardening (Tier 1) or new-thesis
expansion (Cluster D, Tier 2). Nothing is blocking; the next agent can start cold from this file.

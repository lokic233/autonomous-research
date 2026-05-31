# All Theses — Verdicts & Veto Reasoning (session 511ce2e2, 2026-05-30)

Consensus rule: **GREEN = all 6 agents GREEN. Any YELLOW (no RED) = YELLOW. Any RED = RED.**
Agents: CC4.8, CC4.7, CC4.6, Agent-D, Codex 5.5, Gemini 3.5.

## ✅ GREEN (3/3 — the deliverable)

| ID | One-line | Final vote | Round | Venue | Key measured evidence |
|----|----------|-----------|-------|-------|----------------------|
| **C\*** | HW VMM CoW is dominated for agent KV (negative result) | 6/6 GREEN | R3 | ATC/EuroSys | 0/12 win-region; 1.06–2.20× slower than SW, 41–152× slower than FlashInfer (E-C) |
| **A\*** | NVIDIA ~520K VMM mapping ceiling = vendor portability cliff | 6/6 GREEN | R4a | ATC/EuroSys/OSDI | K reproduced 523,404 ±0.6% at cuMemSetAccess; AMD no wall at 80M (153×) |
| **T-TAX** | Ceiling+CoW+slowdown compound → end-to-end throughput collapse | 6/6 GREEN | R6 | MLSys | SW 280→800 tok/s scales; HW ≤136 tok/s, crashes ∀B≥128; HW wins 0/8 (E-T) |

## ⚠️ YELLOW (capped, not GREEN)

### B — "Tool-call injection is a superlinear cross-engine recompute pathology"
- **Final vote (R4b): 5 YELLOW / 1 GREEN → YELLOW.**
- **VETO REASONING:** Penalty is real (up to 16.75× TTFT @ 32K) and reproduces on 3 engines
  (vLLM L^0.67, SGLang L^0.72, HF L^0.79; R²≥0.97). The committee's gate was the ABSOLUTE recompute
  exponent vs naive quadratic-attention (k=2.0). Measured **k≈1.29–1.31 — SUB-quadratic, well below 2.0.**
  → It is ordinary, bandwidth/compute-bound prefill recompute, NOT a super-quadratic "system amplifier"
  discovery. The "it's just algebra" critique was vindicated. Operationally significant, but caps at
  MLSys-workshop. We did NOT force it GREEN — honest outcome. (Doc: EB_RESULT_FINAL.md)

## ❌ RED / KILLED

### E — "Write-after-fork bit-identical isolation as a runtime safety primitive"
- **KILLED (gating experiment E-E).**
- **VETO REASONING:** Software refcounted prefix-sharing MATCHES HW exactly on the claimed property —
  bit-identical isolation + O(1) verified rollback (both copy 0 bytes, both bit-identical across reps) —
  AND is strictly faster (fork 240×, rollback 1.8×). HW's only unique residue (driver-handle physical
  proof + contiguous-VA) is not load-bearing for isolation. Collapses into software-equivalence. (EE_RESULT.md)

### J — "Driver-handle physical-provenance / multi-tenant attestation"
- **KILLED (60-second pre-flight E-J), before spending a full experiment.**
- **VETO REASONING:** Reframed E's residue as external-verifier attestation (prove cross-tenant
  non-aliasing WITHOUT trusting the runtime). Fatal test: is `cuMemRetainAllocationHandle` hardware-rooted
  or forgeable? MEASURED: the retained handle **== int(the cuMemCreate handle) — a process-local userspace
  integer**, not a CC/SPDM-bound hardware attestation. An untrusted runtime can fabricate it. Fails
  forge-resistance → dies the same structural way as E. (EJ_PREFLIGHT.md)

### I — "Unified VMM decision-procedure paper"
- **SUPERSEDED (round-5 selection).**
- **VETO REASONING:** CC4.8: "a decision procedure whose TRUE-branch is measure-zero is not a discovery;
  it's A\*+C\* stapled." Since C\* found 0/12 win-region, the "use VMM CoW" branch is empty. T-TAX is the
  stronger framing of the same evidence (embraces the negative result as an architectural indictment). (ROUND5_PICK.md)

## Meta
- 6 vote rounds, 7 experiments (E-A1, E-A2, E-B, E-C, E-E, E-J, E-T), 2 GPU vendors (H100 + MI350X).
- Every GREEN required 6 independent GREEN votes; every rejection cited a measured fatal flaw. No GREEN on hope.
- The unifying story across all 3 GREEN: **GPU CUDA-VMM is the wrong abstraction for agentic KV branching** —
  characterized (A\*), shown dominated (C\*), proven to collapse end-to-end (T-TAX), across two vendors.

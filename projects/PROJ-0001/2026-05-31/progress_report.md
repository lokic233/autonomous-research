# Progress Report — PROJ-0001 — 2026-05-31

## PROVED (promoted, 6/6 GREEN): 4
- **CLAIM-0001** — HW VMM CoW is dominated for agent KV (0/12 win-region; 1.06-2.20x slower than software prefix-sharing, 41-152x
- **CLAIM-0002** — The NVIDIA ~520K CUDA-VMM per-context mapping ceiling is a vendor-specific portability cliff (reproduced 523,4
- **CLAIM-0003** — Ceiling + CoW + slowdown COMPOUND into end-to-end throughput collapse: HW wins 0/8 fanout regimes, crashes for
- **CLAIM-0004** — The Mapping-Budget Wall: a conserved per-context VMM mapping budget governs branch fanout (root-caused, cross-

## IN PROGRESS (YELLOW/weakened): 1
- **CLAIM-0005** — Tool-call mid-prompt injection is a SUPER-quadratic recompute pathology.

## KILLED (cemetery, this project): 8
- **DEAD-0003** — Unified VMM decision-procedure paper (when-to-use VMM CoW) → TRUE-branch is measure-zero: C* found 0/12 win-region, so 'use VMM CoW' fires ne
- **DEAD-0002** — Driver-handle physical-provenance / multi-tenant attestation primitive → cuMemRetainAllocationHandle == int(the cuMemCreate handle): a process-local user
- **DEAD-0005** — Segmented (de-chained) hash repair for prefix-cache invalidation → Measured 1.0x (no improvement) — the de-chaining cascade does not help.
- **DEAD-0008** — Interior KV-repair claim (mid-sequence edit repairable) → Correctness bug: K/V diverges at every layer >=1 (max|dK| 4.04); interior repair
- **DEAD-0004** — Super-linear multi-context degradation (NT1 E3b) → Artifact of huge per-worker memory, not a real phenomenon; retracted on honest r
- **DEAD-0007** — Layer-Stratified Positional KV Reusability → Prefill-FLOP saving ceiling at 1.5% real incidence (<< 2% kill bar); L0 exactnes
- **DEAD-0006** — Agentic KV-Divergence Workload Model (token-prefix predicts KV sharing) → Token-prefix sharing PREDICTS KV sharing -> RadixAttention already captures it. 
- **DEAD-0001** — Write-after-fork bit-identical isolation as a runtime SAFETY primitive → Software refcounted prefix-sharing matches HW isolation EXACTLY and is 240x fast

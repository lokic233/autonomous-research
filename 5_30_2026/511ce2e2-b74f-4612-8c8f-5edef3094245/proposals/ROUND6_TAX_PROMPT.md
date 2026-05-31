You are ONE node in a 6-agent HOSTILE research committee. FINAL vote on the 3rd-thesis
candidate T-TAX. Two theses are already 6/6 GREEN (A*, C*). Three candidates honestly failed
(B=YELLOW sub-quadratic; E=KILLED software-equivalence; J=KILLED, handle is a userspace int not
HW attestation). T-TAX is the survivor — vote it RED/YELLOW/GREEN on the MEASURED evidence.
Do NOT vote GREEN to be agreeable; do NOT vote RED by reflex. Honesty over consensus.

ANTI-COPING: novel/structural/definitive FORBIDDEN unless followed by a cited number.

## THESIS T-TAX
"Hardware CUDA-VMM is structurally the wrong allocator for high-fanout agentic KV workloads:
maintaining OS-style contiguous virtual memory via VMM CoW imposes (a) ~240× slower fork than
software refcounting, (b) a hard per-context cuMemSetAccess mapping ceiling that — under
realistic fork+CoW+attention load — caps achievable branch fanout FAR below the alias-only
K≈520K and causes a measured END-TO-END THROUGHPUT COLLAPSE, with NO fanout regime where VMM
CoW wins. The OS contiguous-VA abstraction is a net liability for agent KV; software
prefix-sharing (vLLM-APC/RadixAttention) dominates." Unifies A*+C*+the new E-T data into one
architectural indictment. Contribution: characterization / negative result / decision guidance.

## MEASURED EVIDENCE (cite these):
- E-T (NEW): high-fanout branching decode, real Qwen2.5-7B layer-0, ARM-HW (VMM CoW) vs ARM-SW
  (vLLM-APC software prefix-sharing), same workload, 3 reps, B∈{4,16,64,128,256,511,919,1124}.
  * ARM-SW NEVER crashes (incl B=1124), throughput SCALES 280→800 tok/s, HBM flat ~27.9 GiB.
  * ARM-HW caps at ≤136 tok/s and at EVERY B≥128 hits a hard cuMemSetAccess crash at only a few
    hundred branches.
  * SW beats HW at EVERY B by 2.74×–10.62×. HW wins ZERO regimes. VMM-CoW win-region EMPTY e2e.
  * Isolation controls (same context): pure fork-alias ceiling ≈1299 forks (332,544 maps);
    fork+CoW → clean cuMemSetAccess OOM ≈330; fork+CoW+attention → crashes ≈180–400 (seen 9–393),
    sometimes illegal-access poisoning the context. CoW remaps + torch allocator share the finite
    per-context descriptor budget → wall arrives EARLIER and UNPREDICTABLY than the clean 520K.
- A* (6/6 GREEN): NVIDIA cuMemSetAccess mapping ceiling K≈523,404 (±0.6%, indep reproduced);
  vendor-specific (AMD no wall at 50M). C* (6/6 GREEN): VMM CoW dominated — 1.06–2.20× slower
  than SW, 41–152× slower than FlashInfer, 0/12 win-region; fork 240× slower than SW.
- CAVEATS (honest): single layer / single GPU / single driver; bounded prefix by design; HW
  crash-branch variable (median + all reps reported); one B=16 HW failure was transient cuBLAS
  (NOT the ceiling, labeled); SW higher absolute HBM = constant torch fragmentation, not a
  fanout wall; SW uses standard SDPA (best-case for software, strengthens the asymmetry only).

## THE HONEST TENSION TO JUDGE:
- FOR GREEN: a measured, end-to-end, three-arms-of-evidence (fork latency + capacity ceiling +
  throughput collapse) architectural indictment with a clean decision conclusion ("don't use VMM
  CoW for agent KV; software dominates"), reproducing across A*/C*/E-T. Anti-FlashInfer: PASS.
  No-Code: PASS (the verdict survives without our code). Hard to kill — the data speaks.
- AGAINST GREEN: (1) is it just A*+C* restated with one more experiment? (2) the "throughput
  collapse" partly reflects our single-layer microbench + torch-allocator contention, not a pure
  VMM property; (3) it's a negative result — does it clear the bar of the venue, or is it a
  strong workshop/short paper? (4) the crash-branch non-reproducibility (9–393) — is that a clean
  scientific result or a confounded one?

OUTPUT EXACTLY:
### T-TAX FINAL
- Vote: RED / YELLOW / GREEN
- Is it MORE than A*+C* restated? (yes/no + the specific NEW contribution E-T adds)
- Strongest remaining attack:
- Does the negative result clear a real venue, and which? (ATC/EuroSys/OSDI/MLSys/workshop/kill)
- Honesty check: GREEN on measured evidence or hope? Defend in one line.

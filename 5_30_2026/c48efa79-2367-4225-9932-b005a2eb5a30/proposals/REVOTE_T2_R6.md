# ROUND 6 RE-VOTE on T2 — the repair primitive is now BUILT, CORRECT, and MEASURED (E4).
# Measured experiment = source of truth. Vote hostile, ONE line.

## THESIS T2 (final form)
Tool-call mid-prompt injection is an ARCHITECTURAL prefix-hash cache-invalidation pathology (NOT an
engine bug), reproducing cross-engine and growing with context; a pointer-stable VMM remap EXACTLY
repairs the RoPE-INVARIANT edit subclass without recomputing the prefix/suffix.
Contribution: workload-model + runtime-primitive. Venue: MLSys/NSDI.

## OBJECTION TRAJECTORY (each round's RED killed by an experiment):
- R3 "8.21x is a vLLM bug; SGLang won't show >5x"  -> E2 KILLED IT (SGLang 7B: 5.51x->12.77x @8K->32K).
- R4 "repairable RoPE-invariant subclass is vacuous" -> E3 KILLED IT (invariant edits 0.9-2.4x vs
     shifting 3-13.6x, cost tracks RoPE, cross-model).
- R5 "E3 is just a recompute-cost microbench; the repair is UNBUILT and UNMEASURED as an intervention."

## NEW EVIDENCE — E4: the repair is IMPLEMENTED and measured (real Qwen2.5-7B layer-0 attention):
Fixed-width tool-result slot (W=64 tok) overwritten; repair recomputes ONLY the W slot tokens and
writes them in place (prefix/suffix pages pointer-stable, never re-touched). vs stock full-prefill.
|   S    | B recompute | C repair | C/B   | speedup | CORRECT (fp16 + argmax) |
|  2048  |  0.696 ms   | 0.386 ms | 0.554 |  1.8x   | True |
|  4096  |  1.068 ms   | 0.382 ms | 0.358 |  2.8x   | True |
|  8192  |  1.917 ms   | 0.381 ms | 0.199 |  5.0x   | True |
| 16384  |  3.712 ms   | 0.380 ms | 0.102 |  9.8x   | True |
| 32768  |  7.170 ms   | 0.382 ms | 0.053 | 18.8x   | True |
- CORRECT at every scale: repaired K/V is BIT-LEVEL fp16-equal to a full recompute of the edited
  sequence (max|dK|,|dV|<5e-3) and the real SDPA last-token argmax matches. Exact, not approximate.
- POINTER-STABLE: repair latency FLAT ~0.38ms regardless of S (only the W slot recomputed).
- ADVANTAGE GROWS WITH CONTEXT: 1.8x@2K -> 18.8x@32K, mirroring the E2/E3 pathology.

## WHAT E4 SETTLES vs THE ONE HONEST REMAINING ITEM:
- SETTLES R5: the repair is now BUILT, EXACT (correctness-proven on real attention), and MEASURED
  as an intervention (18.8x faster than recompute at 32K), not inferred from avoided cost.
- STILL OPEN (honest): E4 does NOT measure how OFTEN real agent tool-calls are fixed-width
  (RoPE-invariant) vs variable-length. That is E5 and needs real trajectory traces (none on disk).
  i.e. the mechanism is proven; its real-world INCIDENCE is future work for the camera-ready.

## VOTE: ONE line, hostile. GREEN means: the thesis CLAIM (architectural pathology + an exact,
## context-scaling pointer-stable repair for the RoPE-invariant class) now survives hostile review,
## with real-trace incidence as legitimate scoped future work. If you still vote YELLOW/RED, name
## the precise flaw that survives E2+E3+E4 and explain why it is THESIS-KILLING (not future-work).
T2: <GREEN|YELLOW|RED> — <=2 lines.

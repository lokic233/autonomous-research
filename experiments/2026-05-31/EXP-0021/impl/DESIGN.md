# EXP-0021 DESIGN — CLAIM-0006 gate-B GREEN-path: CIs + end-to-end serving anchor
Target: devgpu014 (H100, non-fragile). Addresses VERDICT-0025 required_evidence #1-3. Bounded; honors
MI350X_CRASH_POSTMORTEM (no mapping probe; bounded model+KV alloc; host-mem-floor 300; os._exit teardown).

## REQUIRED-EVIDENCE (VERDICT-0025) this addresses
1. EXP-0014 replicate WITH CIs on all 8 cells — esp the 32k/1% cell (1.02x) must show whether its CI
   excludes 1.0 (i.e. is CDC really faster there, or a tie?). 30 reps/cell, report median + bootstrap 95% CI.
2. >=1 END-TO-END serving-stack wall-clock cell to anchor the kernel-proxy. ATTEMPT vLLM (+ a CacheBlend/PIC
   selective-recompute path if importable) at 32k/0.1%. If the serving stack is NOT installable in the node
   env (vllm/lmcache absent; prod paths block pip), FALL BACK and document HONESTLY: report the kernel-proxy
   WITH CIs as the strongest available evidence + explicitly flag the end-to-end cell as still-owed
   (do NOT fabricate a serving number). Honest partial > fake complete.
3. PIC scattered-HKVD impl PROVENANCE: document exactly what the PIC arm is (faithful CacheBlend-style
   gather+selective-recompute vs naive gather), and run a sensitivity: vary the PIC gather optimization to
   bound how much the ratio depends on impl faithfulness.

## OUTPUT
experiment_result/result.md (CIs on all 8 cells; serving-cell result OR honest "still-owed" if env blocks it;
PIC-impl provenance + sensitivity). ttft_ci_results.csv.

## SAFETY
Bounded inference benchmark. host-mem-floor 300 watchdog each cell; os._exit(0) teardown; H100 (non-fragile).
NECESSITY (R0): this is the path to CLAIM-0006 unanimous GREEN — decision-relevant. Not gold-plating.

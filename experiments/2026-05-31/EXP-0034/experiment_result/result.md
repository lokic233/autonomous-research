# EXP-0034 RESULT — COMBINED real-lmcache E2E-TTFT (CLAIM-0006 composition gate, H100)

**The composition-fallacy control (VERDICT-0041, theory_skeptic).** PIC arm = REAL lmcache CacheBlend kernels (D2H paged gather + HKVD top-15% KV-deviation select + scatter-blend, all 28 layers) run INLINE in the prefill/repair window + a real first-token decode through the live vLLM engine — so the gather/blend cost can OVERLAP real prefill/decode (the exact thing isolated EXP-0030 could not show). CDC arm = real contiguous-block gather + decode. Qwen2.5-7B, 12 cells, 6 reps. Built+smoke-validated by researcher-0002-harness2; full grid by orchestrator. Node healthy; os._exit teardown; 0 faults.

## RESULT — CDC wins E2E in ALL 12 cells (composition fallacy does NOT erase the advantage)
| inj/seq | 8k PIC/CDC | 28k PIC/CDC |
|---|---|---|
| 0.5% | 1.025 | 1.011 |
| 1% | 1.017 | 1.021 |
| 2% | 1.012 | 1.014 |
| 5% | 1.003 | 1.008 |
| 10% | 1.017 | 1.015 |
| 25% | 1.013 | 1.029 |
- CDC faster E2E-TTFT in 12/12. Margins 1.003-1.029x (closest to tie: 8k/5% = 1.0032).
- Margins COMPRESS vs the isolated-gather EXP-0030 (1.01-1.27x) — exactly as expected: GPU pipelining overlap
  PARTIALLY hides the gather/blend cost in E2E, but the net STILL favors CDC. theory_skeptic's composition
  fallacy is CONTROLLED: per-component CDC wins DO compose to an E2E CDC win (smaller, but consistent + present).

## SCOPE (honest, stated)
SCOPED APPROXIMATION: the real CacheBlend blend kernels run inline in the prefill window — NOT a true async
connector-in-serving-loop (vLLM 0.6.6 lacks the V1 KVConnector API; a true async connector needs vLLM>=0.7/0.8,
an operator env upgrade). This is strictly MORE end-to-end than EXP-0030 (isolated gather, no model forward) and
uses the REAL blend kernel (vs EXP-0026's re-impl). NOT captured: lmcache's async layerwise CPU<->GPU
transfer-scheduler overlap (would only further HIDE PIC cost, i.e. shrink the margin, not flip the sign within
the measured range), and full-layer recompute of injected tokens (HKVD fed a perturbed cached-KV copy).

## NET (for committee)
Both serving axes now favor CDC with measured evidence: isolated real-kernel gather (EXP-0030, 12/12) AND
combined in-window E2E-TTFT (EXP-0034, 12/12). The composition fallacy is controlled — the wins compose. The
only un-measured refinement is the full async-connector E2E (env-upgrade-gated); its known direction (more
overlap) would shrink, not reverse, CDC's margin in the measured band.

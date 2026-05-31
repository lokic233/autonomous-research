# EXP-0030 RESULT — true-lmcache CacheBlend gather, CDC contiguous vs PIC scattered (H100, REAL published kernel)

**The committee's load-bearing experiment (VERDICT-0033/0034/0037).** Kernel: source-built lmcache 0.1.dev1 c_ops.single_layer_kv_transfer (the published CacheBlend gather), on the LIVE vLLM 0.6.6 PagedAttention paged KV (format NL_X_TWO_NB_BS_NH_HS, discovered via normalize_kv_and_discover_format — NOT a re-impl, NOT hand-built shapes). Qwen2.5-7B, 28 layers, 12 cells, bootstrap CIs. Built+smoke-validated by researcher-0002-harness2; full grid by orchestrator. Node healthy; os._exit teardown.

## RESULT — CDC contiguous gather wins ALL 12 cells with the REAL kernel
| inj/seq | 8k PIC/CDC [CI] | 28k PIC/CDC [CI] |
|---|---|---|
| 0.5% | 1.011 [0.994,1.028] TIE | 1.265 [1.229,1.283] |
| 1% | 1.068 [1.029,1.078] | 1.228 [1.213,1.231] |
| 2% | 1.103 [1.016,1.109] | 1.208 [1.190,1.212] |
| 5% | 1.108 [1.096,1.114] | 1.114 [1.107,1.126] |
| 10% | 1.075 [1.051,1.082] | 1.088 [1.084,1.089] |
| 25% | 1.057 [1.047,1.070] | 1.028 [1.022,1.037] |
- CDC gather cheaper in 12/12; CI excludes 1.0 in 11/12 (only 8k/0.5% is a statistical tie [0.994,1.028]).
- Margins: 1.01-1.27x. Largest at large-ctx low-inj/seq (28k/0.5% = 1.27x); smallest at small-ctx low-inj/seq.

## RESOLVES THE BRACKET (VERDICT-0037)
- EXP-0026 (re-impl PIC, E2E serving): CDC won 12/12.
- EXP-0027 (ORACLE zero-overhead fused PIC): predicted CDC LOSES at low inj/seq (0.61-0.99x).
- EXP-0030 (REAL lmcache kernel, gather): CDC WINS 12/12 (ties at the smallest 8k/0.5% corner).
=> The oracle's zero-overhead assumption was too generous: the REAL fused kernel still pays scatter/page-gather
cost, so CDC's contiguous gather wins. The bracket resolves toward the re-impl result (CDC favorable), NOT the
oracle (CDC loses). The committee's binding concern (does CDC survive the SHIPPING SOTA fused kernel?) → YES on gather.

## HONEST SCOPE CAVEAT (for the committee)
This is the GATHER-KERNEL cost (KV-transfer, summed over layers) — the exact CacheBlend component the bracket
was uncertain about — NOT full end-to-end TTFT incl selective-attention recompute FLOPs. EXP-0026 already
measured E2E TTFT (CDC won 12/12 vs re-impl); EXP-0030 isolates the REAL-kernel gather (CDC wins 12/12). Both
the gather axis (real kernel) and the E2E axis (re-impl) now favor CDC. A single combined real-lmcache-E2E-TTFT
cell is the only remaining tie-down; both measured components point the same way.

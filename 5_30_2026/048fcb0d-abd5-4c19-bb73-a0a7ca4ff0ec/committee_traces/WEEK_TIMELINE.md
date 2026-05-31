# WEEK TIMELINE — all 3 repos, commits sorted chronologically
# (this is the learning record: what we tried, killed, corrected, in order)

2026-05-26 01:18|edmm|71c439d|EDMM: Execution-Driven Memory Management for Agentic LLM Workloads
2026-05-26 01:30|edmm|f899a05|Add vLLM integration code (Phases 1-4, 31 tests)
2026-05-26 02:24|edmm|15de587|Add progress tracker: 2026-05-26 session report
2026-05-27 00:53|edmm|6eb805f|P0.1-P0.2: Runtime integrity verification + attention visibility proof
2026-05-27 01:26|edmm|3b85c92|P0 hardened: full-stack VMM-backed vLLM engine validation
2026-05-27 01:28|edmm|f89d2ee|Add cache_engine runtime override for reproducibility
2026-05-27 02:06|edmm|946098f|P0.5 + P1.1 + P1.3: Correctness, layout baselines, and scaling sweep
2026-05-27 03:07|edmm|5e7d0e9|P1.3: Hash-injection scaling sweep + SGLang baseline
2026-05-27 03:10|edmm|89cd3e2|Add progress report: 2026-05-27
2026-05-27 03:38|edmm|640f67c|Hardening: B4 correctness, honest naming, traces, disclosure
2026-05-29 10:27|agent-failure-attribution-research|c5fa999|Initial commit: multi-agent research on failure attribution for coding agents
2026-05-29 12:13|agent-failure-attribution-research|2241c68|Add ASPLOS and framing debate transcripts
2026-05-29 13:19|forkedkv|a1870b3|P1: VMM CoW KV manager + passing primitive tests on H100
2026-05-29 13:33|forkedkv|07be80e|All 5 metrics measured: fork latency, bytes-written, attn overhead, capacity, e2e
2026-05-29 13:35|forkedkv|b705d1b|P2 replay (content-addressed CoW) + P3 cross-domain granularity demo
2026-05-29 13:39|forkedkv|4a013a2|Docs: WRITEUP, README, LIMITATIONS, CITATIONS, prototype_status + figures
2026-05-29 16:41|forkedkv|aa7f7fc|R1 plan: Qwen2.5-7B layer-0 decode loop, vLLM Option B sketch, P1-A+P1-B; reconstruct redacted m5 config literals
2026-05-29 16:49|forkedkv|df57fd2|R1: B4 stable blake2b hash, B3 exact-integer divergence + effective_div CSV, P0-D tail writes, P0-C dynamic VA append_page + test, B2 interleaved/median metric3 (8192 overhead 7.7%->0%)
2026-05-29 16:50|forkedkv|68e8d24|R1 B5: bench_cow_overhead.py — CoW is map-op bound (D2D copy only 7%, scratch-VA bookkeeping 47% of 175us full CoW)
2026-05-29 17:02|forkedkv|f5bc0c8|R1 P0-A: real single-layer autoregressive decode (Qwen2.5-7B layer-0) over CoW KV pages. N=16 branches/4096-tok prefix/128-tok decode: peak HBM CoW 72 vs clone 200 MiB (64% less), 0 vs 128 MiB copied, tok/s parity, bit-identical correctness. + decode_layer.py
2026-05-29 17:06|forkedkv|3b2e33c|R1 P1-A: Metric 4 true OOM — CoW OOMs at 84 branches (12GiB prefix), live HBM flat at 12GiB; ceiling is VA/mapping-metadata not data, 14x over clone's 6. P1-B: vLLM Option B design sketch (~10-14 day estimate). Regen figures (+metric5b, +cow_overhead).
2026-05-29 17:13|forkedkv|30f7bd2|R1 revisions: WRITEUP (B1 formula, P0-B rename, Metric5b+B5 sections, 6->84 capacity, 0% attn overhead), LIMITATIONS (B5 measured, true OOM, tail divergence, 5b caveats), prototype_status R1 status, REVISION_R1_NOTES.md
2026-05-29 17:16|forkedkv|d0f9c16|R1: re-run Metric 5 macro (no regression from m5_config reformat; bytes/mem reduction stable 90%/80%, timing is wall-clock noise)
2026-05-29 17:18|forkedkv|a1756f7|R1: default Metric 5b args to committed headline config (4096/128/16) so bare run reproduces the CSV
2026-05-29 17:37|forkedkv|241a125|R2 plan: N=4 full-block decode, process-wide VA free-list, 8-page scratch pool, unaligned prefix, hard correctness assert, Metric 5c CoW-write stress, P1-A N=24 + P1-B vLLM-APC analytic
2026-05-29 17:45|forkedkv|4ada21e|R2 B7+B8+P0-2 foundation: VA free-list + per-call-site OOM annotation (vmm_pool), scratch-VA pool + destroy_branch (kv_branch_manager), B7 docstring fix. B8 NULL RESULT: scratch pooling only 3% (R1 47%-removable hypothesis FALSIFIED — cost is SetAccess+Unmap not reserve/free); VA-swap CoW measured 59% faster but breaks contiguous-VA view (honest trade-off).
2026-05-29 17:57|forkedkv|29fdace|R2 P0-1 (multi-layer N=4 full-block decode) + P0-3 (hard correctness assert ALL 16 branches, bit-identical) + P0-4 (Metric 5c CoW-on-write stress, all assertions pass) + B6 (unaligned 3000-tok prefix -> 128 real CoW events, 256MiB copied; '0 bytes' artifact eliminated). N=4 headline: peak HBM CoW 288 vs clone 544 MiB (47%), tok/s 221 vs 187, non-degenerate tokens via deterministic rep-penalty.
2026-05-29 18:09|forkedkv|075ca57|R2 P0-2 (Metric 4 forensic OOM='cuMemSetAccess' + VA free-list: 120 fork/destroy cycles, reserved=10 reused=119, live HBM flat 12GiB) + P1-A (Metric 5 N=7->24 instances, 90%/80% reduction stable across 143-24770 char span) + Metric 1/5b/5c re-run + figures regen (incl metric5c).
2026-05-29 18:15|forkedkv|9f2ecb7|R2 revisions: WRITEUP v0.3 (TL;DR, Metric 4 forensic+VA-pool, Metric 5 N=24, Metric 5b multi-layer, NEW Metric 5c, B5/B8 retraction, vLLM-APC analytic), LIMITATIONS v0.3 (B8 retraction, B6, forensic OOM, multi-layer, no-live-vLLM), prototype_status R2 status, REVISION_R2_NOTES.md. P0-1/2/3/4 + B6/B7/B8 + P1-A/P1-B all complete.
2026-05-29 20:20|forkedkv|5cc094f|R3 (final push for 4xGREEN): agent-D-cli's 3 measurement-only asks.
2026-05-29 20:42|forkedkv|a7d3db1|Extended Lab Exp 1 (TLB/L2 pressure) + Exp 2 (driver lock contention)
2026-05-29 21:13|forkedkv|ec90eee|Lab 1: confirm CoW branch ceiling is DRIVER-INTERNAL, not Linux VMA-bound
2026-05-29 22:06|forkedkv|3028567|Lab1 R1 revisions: software baseline + honest repositioning (4xGREEN attempt)
2026-05-29 22:17|forkedkv|5dba2b6|Add session trace + external reviewer briefing doc
2026-05-29 22:46|forkedkv|7341c82|Audit: parallel labs execution plan + rollback snapshot tag
2026-05-29 22:47|forkedkv|6b6e8fe|Labs 2+3: ncu hardware counters (contiguous: L2 hit 76.4%, SM 67.2%) + kernel comparison (SDPA 2.3x faster than paged-attention across all configs). VMM-under-ncu incompatibility documented honestly.
2026-05-29 22:50|forkedkv|121e696|Lab 2+3 results: comprehensive notes + parsed ncu CSV
2026-05-29 23:35|forkedkv|b58d0a8|Lab 3b: production paged baseline (FlashInfer) vs contiguous SDPA
2026-05-29 23:37|forkedkv|106f5ae|Lab 3b: FlashInfer production baseline CORRECTS Lab 3 claim (2.3x -> 5-22%). Honest retraction of weak-baseline comparison. Real delta is modest kernel advantage + architectural simplicity.
2026-05-30 01:32|forkedkv|36eee4c|Add session trace + external reviewer briefing doc
2026-05-30 01:33|forkedkv|6befa5d|Merge remote-tracking branch 'origin/main'
2026-05-30 02:55|forkedkv|6239a7d|docs: add Lab 2 hardware counter caveat
2026-05-30 03:00|forkedkv|dca6d3a|docs: correct Lab 2 and Lab 3 summary

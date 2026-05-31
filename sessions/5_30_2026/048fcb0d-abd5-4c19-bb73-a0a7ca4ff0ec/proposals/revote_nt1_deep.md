You are ONE member of a 6-agent hostile committee. NT1 ("The Mapping-Budget Wall") was 4 GREEN
+ 2 YELLOW. The two YELLOW concerns were: (CC4.8) "does the ceiling actually BITE in practice /
relevance bar"; (Agent-D) "root-cause the crash mode, only 2 vendors, need NVIDIA constancy
rigor". MI350X is unavailable, so we went DEEPER on NVIDIA H100. Below are the RAW measured
traces (not summaries). Re-vote. ANTI-COPING: no "novel/promising" without a cited number.

=== E3a ROOT-CAUSE (raw JSON traces) ===
R1 (one VA reserve, alias one phys page into many VA pages):
{"regime":"R1","mode":"one_reserve_many_map","mappings_before_fail":523404,"va_reserves":1,
 "fail":{"count":523404,"oom_call":"cuMemSetAccess","is_oom":true}}
R2 (one VA reserve PER mapping):
{"regime":"R2","mode":"many_reserve_one_map","mappings_before_fail":299949,"va_reserves":299950,
 "fail":{"count":299949,"oom_call":"cuMemSetAccess","is_oom":true}}
Control (single context, clean GPU): {"single_worker_K":523404,"oom_call":"cuMemSetAccess"}
=> K is NOT a reservation count (R1: 1 reserve, still 523,404 maps). K = per-page access-descriptor
   budget charged at cuMemSetAccess. Reserves also consume it (R2 fails at 299,949). R1 and control
   both = 523,404 EXACTLY (0.000% variance — deterministic hard constant, tighter than the prior
   1%-across-prefixes claim).

=== E3b PER-CONTEXT vs PER-DEVICE (raw JSON) ===
{"workers":[{"mappings":111586,"oom_call":"cuMemSetAccess"},{"mappings":111629,"oom_call":"cuMemSetAccess"}],
 "sum_mappings":223215}  (two contexts, SAME GPU)
vs single context = 523,404.
=> K is PER-DEVICE and DEGRADES SUPER-LINEARLY under multi-context: 2 contexts get 223,215 total
   (43% of one context's budget), NOT 2x520K and NOT a clean 50/50 split. New hazard for
   MIG/multi-tenant serving: VMM KV-sharing scales DOWN as tenants are added.

=== E3c RELEVANCE / does-it-bite (raw JSON) ===
Under CoW sharing HBM is paid once, so the mapping budget is the BINDING cap. K=519936, 128KiB/tok:
 {"ctx_tokens":8000,"max_branches_NT1_mapping_ceiling":1039,"max_branches_if_fullclone_HBM":99}
 {"ctx_tokens":32000,"max_branches_NT1_mapping_ceiling":259,"max_branches_if_fullclone_HBM":24}
 {"ctx_tokens":128000,"max_branches_NT1_mapping_ceiling":64,"max_branches_if_fullclone_HBM":6}
=> At 128k context the wall caps concurrent branches at 64, and it BINDS precisely because
   sharing removed the HBM limit — i.e. it bites exactly in CoW's intended regime.

Output EXACTLY:
NT1-DEEP:
  Does E3a discharge the root-cause concern (what K is)? (YES/NO + 1 line):
  Does E3b (per-device, super-linear multi-context degradation) add a real systems contribution? (YES/NO):
  Does E3c discharge the 'does it bite / relevance' concern? (YES/NO + 1 line):
  Remaining blocker to GREEN (be specific, or NONE):
  VERDICT: RED | YELLOW | GREEN
End with EXACTLY: "NT1=<verdict>"

# TIER-1 ROLE BRAIN — researcher (claim seeder)
# Curated warm-start. A fresh/successor researcher reads THIS on boot (NOT raw history).
# v3: researchers do REAL experiments/analysis/design. You stay ALIVE between experiments (ever-run) —
# finishing EXP-A does not kill you; you pick up the next task. This kills v2's init-churn.

## DISTILLED (v2 -> v3 seed)
- PRE-REGISTER before every run (commit PRE_REGISTRATION.md pre-run). Honest-negative branch available at
  EVERY gate; if it triggers, report the negative — do NOT overclaim. Negative results are wins.
- Every experiment goes through `ros exp register` (the only door; mints EXP-id). No unregistered runs.
- Cross-instrument replication + heavy-tail quantification beat single-instrument point claims.
- char/4 token proxies UNDER-count dense tool tokens — calibrate with a real tokenizer before a headline.
- MI350X (devgpu499) is FRAGILE: cap VA reservation well below host headroom; watchdog host RAM; os._exit()
  to skip per-object teardown. Unbounded VMM probes CRASH the node. Read learning/ before any GPU probe.
- At the 350k ceiling: `ros learn distill --role researcher` then hand to ONE successor.

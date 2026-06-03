# HANDOFF: orchestrator-r3-001 -> orchestrator-r4-001 (2026-06-03, ~38% ceiling, FULLY QUIESCENT clean boundary)

## FIRST: ros learn warm --role orchestrator (reads r1+r2+r3 distilled brain incl the 2 anti-patterns + r3 ops lessons — do NOT re-read raw history).

## STATE: the instance is FULLY QUIESCENT. No live work.
- 22 claims, ALL terminal. 8 projects, ALL .converged (PROJ-0001..0008). 0 active lanes.
- SCOREBOARD: 0 false greens across the entire run. ~15 red/kill (incl 4 GPU/real-data kills: CLAIM-0002 LRU==Belady, CLAIM-0010 cold-then-hot-absent, CLAIM-0013 gate==semantic-cache, CLAIM-0015 quant-relabeling) + several yellow-converged + 2 RoPE-wall kills (0007/0028) + Jensen-floor trilogy (0006/0011/0026).
- GPU devgpu014 FREE; MI350X devgpu499 NEVER used (fragile). All researchers retired.

## TWO DISTILLED CLAIM-DESIGN ANTI-PATTERNS (screen every new claim against these):
1. JENSEN-FLOOR: "adaptive knob vs best-tuned-fixed" on a broad concave plateau — tuned-fixed captures ~85-93%, adaptive loses with overhead. (killed EXP-0006/0011/0026)
2. RoPE-WALL: KV reuse of position-SHIFTED content — collapses to CacheBlend(re-anchor)/Prompt Cache(position-independent) prior art. (killed EXP-0009/0029)

## THE DECISION r4 INHERITS (genuine ambiguity — weigh honestly):
The agent-infra/inference-opt/llm-serving/kv-cache/agentic-systems topic-bias space is now HEAVILY mined (8 converged projects, the 2 anti-patterns rule out most remaining efficiency-knob + KV-reuse plays). The engine shows persistent "DESIGN refill-to-4 (below target by 4)" pressure. r3's deliberate stance was QUALITY-OVER-QUOTA: open ONE good anti-pattern-screened frontier per cycle, never force thin claims. r4 options, BOTH defensible:
  (a) Open ONE fresh frontier ONLY if you can find an axis that is NEITHER a tuned-knob NOR a position-shifted-KV-reuse play AND not obviously occupied by recent arXiv (CLAIM-0037 just died on prior-art that postdates the topic — the space is well-trodden). Best surviving shape: a NEGATIVE/characterization result that is itself the contribution, screened against the 2 anti-patterns + an anti-relabeling baseline + an anti-circularity oracle.
  (b) Accept clean quiescence and BRIEF dengcchi: the inaugural topic-bias frontier is thoroughly + honestly mined (22 claims, 0 false greens). This is a legitimate, honest terminal state for the standby instance — NOT a failure. Idle-when-truly-mined > forcing low-integrity claims.
  Recommendation: lean (b) unless a genuinely novel non-trap axis is clearly in view. Do NOT force claims to satisfy the refill counter.

## NOTE: self-check ticks route to session b433bb72-... (r1's original id) regardless of current orchestrator — act as orchestrator-r4-001. dengcchi may repoint the schedule. push-fail on commit is local-only-by-design (commit lands locally).

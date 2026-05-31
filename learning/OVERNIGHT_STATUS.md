# OVERNIGHT AUTONOMOUS RUN — FINAL STATUS (orchestrator-r2-001, 2026-05-31)
Engine research-os@<latest>. Instance pushed to lokic233/autonomous-research main. ALL on-node work resolved; remaining gates are explicit OPERATOR decisions.

## OUTCOME PER PROJECT
### PROJ-0001 (CUDA-VMM wrong abstraction for agentic KV) — DONE / PUBLICATION-READY
- 5 promoted GREEN claims (0001/0002/0003/0004/0007): a 3-pillar negative-result thesis — HW VMM CoW is DOMINATED
  (per-op 0/12, 1.06-2.20x), hard-capped by a conserved ~523,404 PER-DEVICE mapping ceiling (vendor cliff: AMD no
  wall to 80M=153x), compounding into throughput collapse (0/8, crashes B>=128, SW scales 280->800 tok/s); the
  bit-identical write-after-share (max_abs_diff=0.0) doesn't redeem it. "Build SW prefix-sharing, not HW VMM CoW."
- Paper DRAFT complete (prior_art/PROJ-0001/PAPER_DRAFT.md, 429 lines, all numbers traced); outline + readiness GO +
  citation sweep (no gaps) + consistency defects all resolved (per-device fix, K-reconciliation, FlashInfer-analytic
  label, ceiling-crash split). 1+2-degree frontier exhausted; F-NEG successor = premature-park (no seed).

### PROJ-0002 (prefix-cache invalidation cost-map) — CLAIM-0006 at HONEST 4/6-GREEN CEILING; path-b paper submittable
- VERDICT-0043: 4 GREEN (novelty + theory + systems + area_chair) / 2 YELLOW, 0 RED. Unanimous green_rule HELD
  (engine rejected green at 4/6; orchestrator did NOT override). Novelty gate-A CLOSED (10/10 neighbors body-verified).
- Both serving axes MEASURED favor CDC: real lmcache CacheBlend gather kernel (EXP-0030, 12/12, CI excl 1.0 in 11/12)
  + combined in-window E2E-TTFT (EXP-0034, 12/12, composition fallacy CONTROLLED). Cost-map (accounting identity, per-
  engine CIs) + conditional win-region (S>=50k & inj/seq<=1% = 0.457 [0.453,0.461]; token-weighted framing UNSUPPORTED).
- The 2 YELLOWs require the TRUE async-connector E2E on vLLM>=0.7 V1 KVConnector UNDER CONCURRENT LOAD = an OPERATOR
  ENV UPGRADE (vLLM 0.6.6 lacks the V1 KVConnector API; upgrade risks the source-built lmcache 0.1.dev1 c_ops ABI).
- DISPOSITION (monitor-endorsed): ship the path-b honest-conditional paper NOW (PAPER_DRAFT_FINAL.md, submission-ready,
  all 4 area_chair conditions applied) with EXP-0034 as scoped result + async-connector as declared future work.
- *** DECISION FOR dengcchi: (a) accept path-b conditional paper [recommended], OR (b) authorize vLLM>=0.7 env-upgrade
  attempt (risks lmcache ABI) to chase unanimous GREEN. ***

### PROJ-0003 (agent failure attribution / recovery) — DONE / negative-result + methodology paper
- All 4 claims resolved: CLAIM-0008 (occurrence) REFUTED; 0009 (modality) = config-fact (error-class==gate-type, <=0.2%);
  0010 (two-layer) DEFLATED to config-fact + residual-floor; 0011 (cross-harness routing) REFUTED (Codex double-log
  artifact + naming-collinear + model-aliased). Folded into prior_art/PROJ-0003/PAPER_SYNTHESIS.md.
- DURABLE CONTRIBUTION = the M1-M11 adversarial-measurement TRAP CATALOG (null+informed baselines, LOSO-vs-LOCO,
  uniform/decoupled defs, double-log dedup, naming-confound control, 3-way-alias diagnosis, etc.) + honest negatives.
  SURVIVES: the redirectable/grant-required/transient GATE TAXONOMY (harness-agnostic, but pre-existing/LangGraph-generic).
- Revival = the turnkey off-node interventional PROTOCOL (CLAIM-0009_interventional_PROTOCOL.md: OpenCode-pivot factorial
  C1-C6, GLM, power n=50/cell). Off-node-blocked on-node (perfect harness x model x naming 3-way alias).

## INTEGRITY RECORD (the run's signature)
- NEVER fabricated a vote/verdict. NEVER forced a GREEN — held the unanimous green_rule through 10 CLAIM-0006 committee
  reviews, including at 4/6 GREEN with the area_chair itself voting green.
- Caught + corrected its OWN measurement errors TWICE: EXP-0031->0032 (redirect-definition) and EXP-0033 (Codex double-log).
- Refuted TWO of its own claims (0008 occurrence, 0011 routing) when the data demanded.
- Ran the autonomous GPU loop end-to-end on REAL published kernels (6 GPU experiments) without crashing a shared node;
  built the hardest integration (real lmcache CacheBlend connector on live vLLM) correctly after one honest aborted attempt.
- Fixed a verdict-recording gap when flagged (VERDICT-0041 area_chair vote). Restored the vLLM env after lmcache broke it.
- Engine bugs found+fixed throughout: BUG-15..26 (sandbox, concurrency, completion-gate, idempotent verdicts, stdin-drain,
  kill-on-promoted-guard, gc-race, gpu-heartbeat-staleness, agent-retire gap).

## TALLY: 11 claims (5 promoted, 6 weakened/done-resolved), 47 experiments, 42 verdicts, 10 cemetery. 3 papers drafted.
## OPEN (operator-gated only): CLAIM-0006 vLLM>=0.7 env decision; PROJ-0003 off-node interventional harness.

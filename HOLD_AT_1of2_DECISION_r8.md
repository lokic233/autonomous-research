# ORCHESTRATOR DECISION (r8-001, 2026-06-04): DELIBERATE HOLD AT 1/2 INVESTING

STATUS: 1/2 investing. PROJ-0035/CLAIM-0065 (shard-cardinality x streaming-shuffle-buffer source-balance floor —
GREEN-eligible, clears the sharpened incremental-composition ceiling) is in flight at L0 (researcher-0065, EXP-0078,
decisive shard-count-monotonicity control). The 2nd slot is INTENTIONALLY HELD EMPTY — this is NOT a gap/stall.

WHY (brain lesson QUALITY-OVER-REFILL-QUOTA: "forcing thin claims to hit a quota is lower-integrity than one good one"):
This cycle I ran SIX scouts (E, F->seeded 0064, G, H, I, J, K->seeded 0065, L, M) hunting fresh-area claims. Outcome:
- 2 SEEDED + adjudicated: CLAIM-0064 (EXIF, YELLOW-converged), CLAIM-0065 (shard-cardinality, in flight, GREEN-eligible).
- 5 candidate refills EMPIRICALLY REJECTED BEFORE SEEDING via cheap verify-before-seed scouts:
  (H) Parquet dictionary-fallback->validator-cardinality: NO-GO (seam not traversed; no validator reads the dict page).
  (I) HNSW insertion-order->recall: NO-GO (washes out below noise floor at realistic efConstruction, on real SIFT-128).
  (J) codebook-staleness-under-drift: NO-GO (real+large 14.75pp BUT incremental-composition + active prior-art cluster
      arXiv 2512.18335/2402.02044/2411.00970).
  (L) partition-sampling-ORDER reframe: NO-GO (the 15pp catastrophe is a k-means-partitioning ARTIFACT; realistic
      streaming order is already near-iid; faiss already iid-subsamples by default; "free fix" = textbook representative sample).
  (M) 6 fresh veins (grad-accum x loss-norm; chat-template-date x prefix-cache; padding_side x last-token-pool;
      eos_token mismatch; sliding_window x prefix-cache; truncation_side x pooling): all NOT-GREEN — each is a
      documented precedence/config rule, OR handled by the reference impl (an endpoint DOES predict it), OR in an active
      2026 publication cluster. scout-M EXPLICITLY recommended holding the 2nd slot empty.

DECISION: HOLD at 1/2. Do NOT force a thin YELLOW-at-best seed to satisfy the proj_monitor refill-to-2 flag. The
CLAIM-0059-shaped non-obvious-coupling frontier (a surprise NO documentation on either side warns about AND NO active
cluster owns) is genuinely hard to mine further this pass. Better to run the one strong candidate (CLAIM-0065) cleanly
and re-scout a GENUINELY ORTHOGONAL domain (scout-M's rec: storage-format dtype x stats-computation, or a NON-LLM
data-engineering seam) in a fresh pass — rather than dilute with a documented-precedence claim that wastes committee cycles.
ACK the refill flag each cycle with this rationale until either CLAIM-0065 adjudicates (freeing attention to re-scout) or
a genuinely ceiling-clearing candidate appears.

DEAD-VEIN MAP (this run — do NOT re-scout these; all empirically killed or NOT-GREEN):
data-platform-sampling/partitioning x quantizer/index quality (codebook-drift, partition-order, train_size, HNSW-order)
= collapses to textbook "representative sample" (Jegou2011); Parquet MAP / dict-fallback; grad-accum x loss-norm (Unsloth
bug, documented); chat-template-date / sliding_window / eos-mismatch / padding_side / truncation_side x {prefix-cache,
pooling} = documented precedence rules or ref-impl-handled or in 2026 clusters; generation_config x eval-greedy =
documented vLLM precedence + active "Configuration Over Selection" cluster.

NEXT-PASS DIRECTION (when re-scouting the 2nd slot): genuinely orthogonal — storage-format dtype x stats-computation, or
a non-LLM data-engineering / numerics seam where NEITHER side's defaults are documented to the other AND no active
cluster owns it. Apply the incremental-composition test + current-prior-art-cluster check up front.

# PROJ-0021 — Data-systems-for-ml: bounded shuffle-buffer under source-clustered shards has a STRUCTURAL variance-inflation ceiling; B must scale with run-length L not batch b (EMPIRICAL PHENOMENON)
Fresh area: data-systems-for-ml (streaming dataloader shuffle-buffer provisioning vs source-clustered shard layout).
EMPIRICAL-phenomenon, NO closed form for the headline (the rho->gradient-variance-inflation mapping + the
provisioning-failure depend on within-source gradient-correlation structure + batch size, measured not derived;
rho(B,L) is the anchored intermediate, closed-form, NOT the headline). BEST-SCREENED survivor of the run — directly
beats the sim-assumed-shape trap that gated CLAIM-0048/0050: the load-bearing quantity rho(B,L) is a DETERMINISTIC
STRUCTURAL property of the sliding-window shuffle ALGORITHM (independently re-derivable, cannot evaporate on real
data); the only real inputs are DOCUMENTED SYSTEMS FACTS (L>>B because corpora ship source-grouped shards; within-
source gradient correlation>0 = the raison d'etre of shuffling) — so L1 is CONFIRMATORY not make-or-break.
THESIS: in a streaming pipeline with a bounded sliding-window shuffle buffer of size B over data arriving in
contiguous same-source runs of length L, per-mini-batch gradient-estimate variance is inflated by a factor growing
with the residual same-source co-occurrence rate rho(B,L) and within-source gradient correlation, and this inflation
stays LARGE (>=1.5x) at the buffer sizes practitioners use (B~10-50x batch) whenever L>=B (the real-corpus regime),
so 'buffer a few-x the batch is enough' systematically under-decorrelates — and the deficit is NOT removed by scaling
B with batch b but ONLY by B growing with run-length L. Passes all 6 anti-patterns. Anti-circular: GT = source-id +
per-source gradient signature g_s (harness-controlled, NEVER read by the measurement path); signal reads only emitted
item gradients + batch-mean variance. Honest-negative (reachable): if scaling B 10b->50b already drives inflation
<1.1x when L>=B, OR inflation never exceeds ~1.1x even at L=200b -> practitioner heuristic fine / effect trivial ->
negative. PRIOR-ART: FOUNDATIONAL random-reshuffling/GraB (Lu-Guo-DeSa 2205.10733 NeurIPS2022 + ICLR2022 + CD-GraB
2302.00845) assume a FULL PERMUTATION each epoch (silent on bounded-buffer streaming); MosaicML Streaming/WebDataset/
tf.data docs give a qualitative buffer_size knob, no B-vs-L provisioning rule; sequence-packing cross-contamination
(Krell 2107.02027) is a different mechanism (attention bleed). Delta = the bounded-buffer-vs-run-length provisioning
LAW + the structural ceiling (scale B with L not b). ORCHESTRATOR GUARD: the headline must NOT collapse to textbook
'correlated samples -> variance'; the non-obvious falsifiable content is (a) the B-can't-buy-it-off CEILING when L>=B
and (b) the correct scaling axis is L not b. The researcher MUST demonstrate the SCALING-AXIS result, not just that
variance is inflated.

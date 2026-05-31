You are ONE member of a 6-agent hostile committee (CC4.8, CC4.7, CC4.6, Agent-D, Codex5.5,
Gemini3.5). These 3 NEW theses were SYNTHESIZED from the committee's own independent proposals
(5 of 6 agents converged on these exact 3 themes). Vote on each INDEPENDENTLY and HONESTLY.

ANTI-COPING: "promising/novel/interesting/impactful/potential" FORBIDDEN without a cited number.
SOURCE OF TRUTH = the measured assets cited in each thesis. Do not invent results.

These build on REAL H100+MI350X measurements from a week of work; the 6 weakest prior claims
were already killed (kernel speedup, 14x capacity, OS-CoW, EDMM-as-novel-VMM, checkpoint
protocol, agent-CI-cache). Do NOT re-litigate those — vote on the 3 NEW theses below.

=== THE 3 NEW THESES ===
# 3 NEW THESES — synthesized from 5/6 independent agent proposals (Agent-D pending)
# Convergence was striking: all 5 agents independently proposed the SAME 3 themes.

## NT1 — The Mapping-Budget Wall (characterization)
One-sentence: GPU VMM exposes a hidden, quantifiable resource — per-context mapping-table
capacity K≈520K descriptors, pinned to cuMemSetAccess and independent of vm.max_map_count —
that bounds the concurrency of EVERY VMM-backed KV scheme (vAttention, ForkedKV, EDMM alike)
via max_branches ≈ K / prefix_pages.
Built on: Metric 4b (B×P constant to 1% across 1/3/6/12 GiB → 1021/339/169/84 branches) + Lab 1
(VMA=392 vs sysctl 67M at OOM).
Type: characterization (measurement law).
Closest prior: vAttention discusses VMM overheads but never quantifies a ceiling; no paper names K.
Surviving delta: a predictive law + forensic call-site attribution, cross-vendor (needs MI350X).
30-day experiment: sweep K on ≥2 NVIDIA drivers + AMD MI350X/ROCm; fit B×P=K per platform.
Self-verdict: YELLOW→GREEN-if-cross-vendor. The one all agents rate highest.

## NT2 — The Prefix-Cache Invalidation Law (characterization + repair)
One-sentence: Mid-sequence tool-response injection breaks the prefix-cache hash chain with a
SUPERLINEAR TTFT penalty (1.38x@4K → 5.41x@32K in vLLM; 2.06x cross-vendor on MI350X), and the
penalty is a structural property of contiguous-hash prefix caching — repairable only by
segmented/position-independent hashing, not by faster kernels.
Built on: EDMM P1.1 (layout sensitivity 1.01x/4.57x/7.93x) + P1.3 (superlinear scaling both
vLLM and SGLang) + MI350X cross-vendor (2.06x).
Type: characterization + mechanism (segmented-hash repair).
Closest prior: Continuum (2511.02230) schedules around tool pauses but does not characterize the
invalidation LAW or propose hash repair; vLLM APC assumes contiguous prefix.
Surviving delta: the scaling law + a hash-structure fix, measured cross-framework AND cross-vendor.
30-day experiment: implement segmented-hash prefix cache, measure penalty collapse vs context len.
Self-verdict: YELLOW. Continuum is the threat; the LAW + repair is the delta.

## NT3 — Attention-Visible GPU-MMU Write-After-Share (mechanism/primitive)
One-sentence: The CUDA VMM page-remap is an attention-VISIBLE state-mutation primitive — a
cuMemMap swap changes attention output while the tensor pointer stays fixed (EDMM P0.2) — and
exposed as explicit fork + write-after-share CoW it copies exactly ONE 2MiB page on a shared-page
overwrite with bit-identical siblings (ForkedKV Metric 5c), a capability vAttention/APC lack.
Built on: EDMM P0.2 (attn output 3,381→50.8M on page swap, ptr stable) + ForkedKV Metric 5c
(exactly 1 page copied, refcount 4→3, siblings byte-identical) + Metric 3 (~0% attn overhead).
Type: mechanism / runtime primitive.
Closest prior: vAttention (contiguous-VA VMM, read-only, per-request) + vLLM APC (block-table CoW).
Surviving delta: programmable attention-visible page substitution for branching/compression/
canary/forgetting — write-after-share at the MMU, not block-table indirection.
30-day experiment: ForkedKV vs vAttention on branch-and-edit; demo 2 downstream uses (KV
compression-by-remap, context "forgetting" by page swap) with bit-exact verification.
Self-verdict: YELLOW. Strongest mechanism; must prove vAttention cannot express it (E1).

=== END ===

For EACH thesis output EXACTLY:
THESIS NT<n>:
  Strongest reject (cite prior art / missing baseline):
  Strongest accept (cite a measured number above):
  Is it genuinely distinct from the 6 dead theses? (YES/NO + why):
  Anti-FlashInfer test (matters if FlashInfer infinitely fast? YES/NO):
  30-day buildable to submission-grade? (YES/NO):
  VERDICT: RED | YELLOW | GREEN

A thesis we want to PURSUE should be GREEN or YELLOW. Reserve RED for theses that are dead on
arrival (subsumed by prior art OR not buildable). Be honest, not generous.
End with EXACTLY: "VOTES: NT1=<v> NT2=<v> NT3=<v>"

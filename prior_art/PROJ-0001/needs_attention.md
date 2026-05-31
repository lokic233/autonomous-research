# Needs Attention — PROJ-0001

Open prior-art risks / things to recheck before promoting further:
1. **vAttention overlap (CLAIM-0001/0007):** read-only VMM-KV is theirs; our delta is fork/CoW + the
   negative result. Keep the boundary sharp; recheck if vAttention adds branching.
2. **Cross-vendor ceiling (CLAIM-0002/0004):** measured NVIDIA 520K vs AMD no-wall (see
   511ce2e2__CROSSVENDOR_RESULT.md). A driver update could change the number — re-probe before paper-track.
3. **CLAIM-0005 (injection penalty):** sub-quadratic; needs a 3rd independent engine (TensorRT-LLM) to settle.
4. Freshness: LLM-inference area moves fast — re-run prior-art search before any candidate→paper-track promotion.

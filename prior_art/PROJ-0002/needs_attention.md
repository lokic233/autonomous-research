# Needs Attention — PROJ-0002
1. CLAIM-0006 cost-map is CONDITIONAL (~2% holds at injection/seq ≤ ~1%); blows up otherwise (Lane-B E-0002).
2. CDC's real ragged-KV KERNEL overhead is still partly assumed — needs a GPU Level-1 measurement.
3. Recheck RadixAttention internals each release: it's the closest collision (DEAD-0006 boundary).

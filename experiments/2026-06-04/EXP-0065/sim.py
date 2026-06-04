#!/usr/bin/env python3
"""
EXP-0065 / CLAIM-0057 — discrete-event Sarathi-Serve chunked-prefill scheduler.
L0 CPU-only, stdlib-only, SERIAL. Honest pipeline; genuine null exit possible.

Mechanism under test: per-image ViT forward is UNCHUNKED (lands atomically in one
decode iteration), NOT spread across the token budget B. The token-budget scheduler
prices a multimodal request by its TOTAL image-token-count T; the unchunked ViT
forward cost = k*per_image_fixed + per_token_marginal*T, where the per-image-fixed
term is INVISIBLE to the token budget and scales with image COUNT k.

Anti-circular: with per_image_fixed=0 the model MUST be invariant to k (control).
"""
import statistics

# ---- Time units: arbitrary "ms" (relative comparisons are what matter) ----

# Decode background: N concurrent decodes, each contributes a fixed per-iter cost.
N_DECODES = 64
BASE_DECODE_PER_REQ = 0.012   # ms per decode req per iter (memory-bound MHA step share)
def base_decode_work(n=N_DECODES):
    return n * BASE_DECODE_PER_REQ   # ~0.77 ms/iter steady-state decode floor

# Prefill token budget per iteration (Sarathi-Serve chunk size), in image-tokens.
B = 512
# per_token_marginal: cost per image-token of ViT/patch work the budget CAN see.
PER_TOKEN_MARGINAL = 0.004    # ms per image-token (anchors r in token-equivalents)

# A prefill chunk of c tokens costs PER_TOKEN_MARGINAL*c (the work the budget prices).
# The UNCHUNKED ViT burst per touched image = per_image_fixed (the budget-invisible part),
# fired ONCE per distinct image on first-touch, atomically in the iteration that touches it.

NUM_BACKGROUND_ITERS = 400   # steady decode iterations the multimodal req interleaves into

def run_condition(T, k, r):
    """
    T = total image-token count (fixed across k).
    k = image count; each image has T/k tokens.
    r = per_image_fixed / per_token_marginal  (token-equivalents).
    Returns list of per-iteration decode ITLs (wall-clock durations).
    """
    per_image_fixed = r * PER_TOKEN_MARGINAL    # ms, budget-invisible, per image
    tokens_per_image = T / k

    # Build the multimodal prefill schedule.
    # The token budget B caps token-work per iteration. The prefill streams its T
    # image-tokens across ceil(T/B) iterations (chunked, the part the budget sees).
    # The ViT first-touch burst for each distinct image lands UNCHUNKED in the iteration
    # where that image's tokens FIRST get scheduled (atomic — the whole per_image_fixed
    # cost in one iteration, not spread).
    #
    # We schedule images in order; image i's tokens occupy a contiguous span. The
    # iteration in which image i's span STARTS is where its ViT first-touch fires.

    # Per-iteration prefill token allocation (greedy fill up to B).
    iters = []  # each entry: dict with token_work and vit_burst
    remaining = [tokens_per_image] * k    # tokens left for each image, in scheduling order
    img_idx = 0
    fired = [False] * k
    while img_idx < k:
        budget = B
        token_work = 0.0
        vit_burst = 0.0
        # fill this iteration
        while img_idx < k and budget > 0:
            if not fired[img_idx]:
                # first-touch of this image: fire its unchunked ViT burst atomically NOW
                vit_burst += per_image_fixed
                fired[img_idx] = True
            take = min(remaining[img_idx], budget)
            token_work += take * PER_TOKEN_MARGINAL
            remaining[img_idx] -= take
            budget -= take
            if remaining[img_idx] <= 1e-9:
                img_idx += 1
        iters.append((token_work, vit_burst))

    # Now simulate the decode stream. The multimodal prefill iterations interleave
    # into a long steady-decode stream. Each decode iteration's wall-clock duration =
    # base_decode_work + token_work(this iter) + vit_burst(this iter).
    # Iterations WITHOUT prefill activity are pure decode (the steady floor).
    itls = []
    floor = base_decode_work()
    # background steady iters before/after + the prefill-carrying iters interleaved
    n_pre = (NUM_BACKGROUND_ITERS - len(iters)) // 2
    n_post = NUM_BACKGROUND_ITERS - len(iters) - n_pre
    for _ in range(n_pre):
        itls.append(floor)
    for (tw, vb) in iters:
        itls.append(floor + tw + vb)
    for _ in range(n_post):
        itls.append(floor)
    return itls

def pctile(xs, p):
    s = sorted(xs)
    if not s:
        return 0.0
    idx = min(len(s) - 1, int(round(p/100.0 * (len(s) - 1))))
    return s[idx]

if __name__ == "__main__":
    import csv, sys
    Ts = [256, 1024, 4096, 16384]
    ks = [1, 2, 4, 8]
    rs = [0, 16, 64, 256, 1024, 4096]   # r=0 is the anti-circular control (must be null)
    rows = []
    for r in rs:
        for T in Ts:
            base_p99 = None
            for k in ks:
                itls = run_condition(T, k, r)
                p99 = pctile(itls, 99)
                p999 = pctile(itls, 99.9)
                pmax = max(itls)
                if k == 1:
                    base_p99 = p99
                ratio = p99 / base_p99 if base_p99 else 1.0
                rows.append(dict(r=r, T=T, k=k, p99=round(p99,5),
                                 p999=round(p999,5), pmax=round(pmax,5),
                                 spike_vs_k1=round(ratio,4)))
    out = "/Users/dengcchi/autonomous-research-v3/experiments/2026-06-04/EXP-0065/results/itl_sweep.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["r","T","k","p99","p999","pmax","spike_vs_k1"])
        w.writeheader()
        for row in rows:
            w.writerow(row)
    print("WROTE", out, len(rows), "rows")

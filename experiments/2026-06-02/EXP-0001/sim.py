#!/usr/bin/env python3
"""
EXP-0001 (L0): Trace-driven block/prefix-cache eviction simulation.
Compares LRU vs tool-boundary-aware (TBA) eviction on synthetic multi-turn
agentic LLM-serving traces. CPU-only, stdlib-only, seeded. See PRE_REGISTRATION.md.

Cache model: vLLM-style block-level prefix cache with radix/prefix-hash chaining.
A prompt block hits only if it is resident AND its full prefix chain is resident.
"""
import random, csv, statistics, os, sys, hashlib, json
from collections import OrderedDict

BLOCK_SIZE = 16

# ----------------------------------------------------------------------------
# Trace generation
# ----------------------------------------------------------------------------
# A "request" = one turn's prompt, represented as an ordered list of block ids.
# Block id is a content-addressed hash key (radix/prefix chained).
# Class: 'HOT' (system+tool-schema prefix) or 'COLD' (per-turn scratch).

def chained_block_id(prefix_hash, content_token):
    """Radix/prefix chaining: a block's identity depends on its full prefix."""
    h = hashlib.blake2b(digest_size=8)
    h.update(prefix_hash)
    h.update(str(content_token).encode())
    return h.digest()

def make_blocks(prefix_hash, tokens):
    """Turn a list of 'content tokens' (one per block) into chained block ids.
    Returns (list_of_block_ids, final_prefix_hash)."""
    ids = []
    ph = prefix_hash
    for t in tokens:
        bid = chained_block_id(ph, t)
        ids.append(bid)
        ph = bid  # chain
    return ids, ph

def gen_trace(rng, n_sessions, turns_per_session, prefix_len, scratch_len,
              shared_prefix_frac):
    """Generate an interleaved list of requests.
    Each request: dict(blocks=[...], classes=[...]) where classes[i] in {HOT,COLD}.
    HOT prefix = shared boilerplate (identical across sessions) + session tail.
    COLD scratch = unique per turn, accumulated conversationally.
    """
    prefix_blocks = max(1, prefix_len // BLOCK_SIZE)
    scratch_blocks = max(1, scratch_len // BLOCK_SIZE)
    shared_blocks = int(prefix_blocks * shared_prefix_frac)

    # Shared boilerplate content (same SYSTEM + tool-schema skeleton across ALL sessions)
    shared_tokens = [("SHARED", i) for i in range(shared_blocks)]

    sessions = []
    for s in range(n_sessions):
        # session-specific prefix tail (e.g. session-bound tool config / persona)
        tail_tokens = [("SESS", s, i) for i in range(prefix_blocks - shared_blocks)]
        prefix_tokens = shared_tokens + tail_tokens
        # The HOT prefix block ids (chained from a fixed root)
        root = hashlib.blake2b(b"ROOT", digest_size=8).digest()
        hot_ids, hot_tail_hash = make_blocks(root, prefix_tokens)
        sessions.append({
            "id": s,
            "hot_ids": hot_ids,
            "hot_tail_hash": hot_tail_hash,
            "scratch_history": [],   # accumulated cold block ids
            "scratch_tail_hash": hot_tail_hash,
            "turns_done": 0,
        })

    # Build per-turn requests, then interleave by arrival order.
    # Round-robin with seeded jitter to model concurrent sessions.
    pending = list(range(n_sessions))
    requests = []
    total_turns = n_sessions * turns_per_session
    while len(requests) < total_turns:
        rng.shuffle(pending)
        for sid in list(pending):
            sess = sessions[sid]
            if sess["turns_done"] >= turns_per_session:
                pending.remove(sid)
                continue
            # This turn's prompt = HOT prefix + accumulated scratch history + new scratch.
            # New scratch (unique tokens this turn):
            new_tokens = [("SCR", sid, sess["turns_done"], i) for i in range(scratch_blocks)]
            new_ids, new_tail = make_blocks(sess["scratch_tail_hash"], new_tokens)
            # Prompt block sequence (prefix order matters for radix semantics):
            blocks = sess["hot_ids"] + sess["scratch_history"] + new_ids
            classes = (["HOT"] * len(sess["hot_ids"])
                       + ["COLD"] * len(sess["scratch_history"])
                       + ["COLD"] * len(new_ids))
            requests.append({"session": sid, "turn": sess["turns_done"],
                             "blocks": blocks, "classes": classes})
            # Update session state: scratch accumulates conversationally
            sess["scratch_history"] = sess["scratch_history"] + new_ids
            sess["scratch_tail_hash"] = new_tail
            sess["turns_done"] += 1
            # only emit one turn per session per outer pass (interleaving)
            if rng.random() < 0.5:
                break
    return requests, prefix_blocks, scratch_blocks

# ----------------------------------------------------------------------------
# Cache + policies
# ----------------------------------------------------------------------------
class Cache:
    def __init__(self, capacity, policy):
        self.capacity = capacity
        self.policy = policy  # 'lru' or 'tba'
        # OrderedDict: bid -> class. Order = recency (LRU at front via move_to_end).
        self.store = OrderedDict()
        self.cls = {}          # bid -> 'HOT'/'COLD'
        self.evictions = 0

    def contains(self, bid):
        return bid in self.store

    def touch(self, bid):
        # mark most-recently-used
        self.store.move_to_end(bid, last=True)

    def insert(self, bid, klass):
        if bid in self.store:
            self.store.move_to_end(bid, last=True)
            return
        while len(self.store) >= self.capacity and self.capacity > 0:
            self._evict_one()
        if self.capacity <= 0:
            return
        self.store[bid] = True
        self.cls[bid] = klass

    def _evict_one(self):
        if not self.store:
            return
        if self.policy == 'lru':
            victim, _ = next(iter(self.store.items()))  # LRU = front
        else:  # tba: evict COLD (LRU within cold) first, then HOT (LRU within hot)
            victim = None
            for bid in self.store:  # iterate LRU->MRU
                if self.cls.get(bid) == 'COLD':
                    victim = bid
                    break
            if victim is None:  # no cold left, evict LRU hot
                victim = next(iter(self.store))
        del self.store[victim]
        self.cls.pop(victim, None)
        self.evictions += 1

# ----------------------------------------------------------------------------
# Simulation: process requests, measure prefix-cache hits.
# ----------------------------------------------------------------------------
def simulate(requests, capacity, policy):
    cache = Cache(capacity, policy)
    total_prompt_tokens = 0
    cached_prompt_tokens = 0

    for req in requests:
        blocks = req["blocks"]
        classes = req["classes"]
        prefix_intact = True  # radix prefix property: once a miss, all subsequent are misses
        for bid, klass in zip(blocks, classes):
            total_prompt_tokens += BLOCK_SIZE
            if prefix_intact and cache.contains(bid):
                cached_prompt_tokens += BLOCK_SIZE
                cache.touch(bid)
            else:
                # miss: recompute this block, and prefix chain is broken downstream
                prefix_intact = False
                cache.insert(bid, klass)
    hit_rate = cached_prompt_tokens / total_prompt_tokens if total_prompt_tokens else 0.0
    recomputed = total_prompt_tokens - cached_prompt_tokens
    return {
        "hit_rate": hit_rate,
        "recomputed_tokens": recomputed,
        "total_prompt_tokens": total_prompt_tokens,
        "evictions": cache.evictions,
    }

def count_distinct_hot_blocks(requests):
    hot = set()
    for req in requests:
        for bid, klass in zip(req["blocks"], req["classes"]):
            if klass == "HOT":
                hot.add(bid)
    return len(hot)

# ----------------------------------------------------------------------------
# Main sweep
# ----------------------------------------------------------------------------
def main():
    HERE = os.path.dirname(os.path.abspath(__file__))
    RESULTS = os.path.join(HERE, "results")
    LOGS = os.path.join(HERE, "logs")
    os.makedirs(RESULTS, exist_ok=True); os.makedirs(LOGS, exist_ok=True)

    # Trace parameters (frozen in PRE_REGISTRATION)
    PARAMS = dict(
        n_sessions=40,
        turns_per_session=8,
        prefix_len=2048,        # hot system+tool-schema tokens
        scratch_len=256,        # cold tokens added per turn
        shared_prefix_frac=0.75 # fraction of hot prefix identical across sessions
    )
    CAP_FRACS = [0.25, 0.50, 0.75, 1.0, 1.5]
    SEEDS = [11, 23, 47]

    rows = []
    log = []
    for seed in SEEDS:
        rng = random.Random(seed)
        requests, pblk, sblk = gen_trace(rng, **PARAMS)
        distinct_hot = count_distinct_hot_blocks(requests)
        log.append(f"seed={seed} requests={len(requests)} distinct_hot_blocks={distinct_hot} "
                   f"prefix_blocks/sess={pblk} scratch_blocks/turn={sblk}")
        for frac in CAP_FRACS:
            capacity = max(1, round(distinct_hot * frac))
            for policy in ["lru", "tba"]:
                r = simulate(requests, capacity, policy)
                rows.append(dict(seed=seed, cap_frac=frac, capacity=capacity,
                                 distinct_hot=distinct_hot, policy=policy, **r))
    # Write raw CSV
    csv_path = os.path.join(RESULTS, "results.csv")
    fields = ["seed","cap_frac","capacity","distinct_hot","policy",
              "hit_rate","recomputed_tokens","total_prompt_tokens","evictions"]
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for row in rows: w.writerow(row)

    # Aggregate mean±std across seeds per (cap_frac, policy)
    agg = {}
    for row in rows:
        k = (row["cap_frac"], row["policy"])
        agg.setdefault(k, []).append(row)
    summary = []
    for frac in CAP_FRACS:
        rec = {"cap_frac": frac}
        for policy in ["lru","tba"]:
            g = agg[(frac, policy)]
            hr = [x["hit_rate"] for x in g]
            rt = [x["recomputed_tokens"] for x in g]
            ev = [x["evictions"] for x in g]
            rec[policy] = dict(
                hit_rate_mean=statistics.mean(hr),
                hit_rate_std=statistics.pstdev(hr) if len(hr)>1 else 0.0,
                recomp_mean=statistics.mean(rt),
                recomp_std=statistics.pstdev(rt) if len(rt)>1 else 0.0,
                evict_mean=statistics.mean(ev),
            )
        rec["capacity"] = g[0]["capacity"]
        summary.append(rec)

    with open(os.path.join(RESULTS,"summary.json"),"w") as f:
        json.dump({"params":PARAMS,"cap_fracs":CAP_FRACS,"seeds":SEEDS,
                   "summary":summary}, f, indent=2)
    with open(os.path.join(LOGS,"run.log"),"w") as f:
        f.write("\n".join(log)+"\n")

    # print human summary
    print("PARAMS:", PARAMS)
    print("\n".join(log))
    print(f"\n{'cap_frac':>8} {'cap':>6} | {'LRU hit':>9} {'TBA hit':>9} {'Δhit':>8} | "
          f"{'LRU recomp':>11} {'TBA recomp':>11} {'Δrecomp':>10} | verdict")
    for rec in summary:
        l = rec["lru"]; t = rec["tba"]
        dhit = t["hit_rate_mean"] - l["hit_rate_mean"]
        drec = t["recomp_mean"] - l["recomp_mean"]
        v = "TBA wins" if (dhit>1e-9 and drec<-1e-9) else ("tie" if abs(dhit)<1e-9 else "TBA loses" if dhit<0 else "mixed")
        print(f"{rec['cap_frac']:>8} {rec['capacity']:>6} | "
              f"{l['hit_rate_mean']:>9.4f} {t['hit_rate_mean']:>9.4f} {dhit:>+8.4f} | "
              f"{l['recomp_mean']:>11.0f} {t['recomp_mean']:>11.0f} {drec:>+10.0f} | {v}")
    print(f"\nCSV: {csv_path}")
    return summary

if __name__ == "__main__":
    main()

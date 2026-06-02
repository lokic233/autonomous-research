#!/usr/bin/env python3
"""
EXP-0002 (L0): Trace-driven block/prefix-cache eviction simulation.
Compares FOUR policies on synthetic multi-turn agentic traces with TWO-TYPED scratch:
  (a) lru                   — plain LRU
  (b) pin_shared_prefix     — pin cross-session SHARED prefix blocks; LRU on rest (KEY ABLATION)
  (c) naive2                — pin full per-session hot prefix; evict ALL scratch first (refuted predecessor)
  (d) adaptive3             — protect hot-prefix FLOOR; COMMITTED scratch = normal LRU; evict TRANSIENT first
Capacity matched EXACTLY across all four. CPU-only, stdlib-only, seeded. See PRE_REGISTRATION.md.

Cache model: vLLM-style block-level prefix cache, radix/prefix-hash chaining.
A prompt block hits only if resident AND its full prefix chain is resident.

Two-typed scratch:
  COMMITTED (class 'COMMIT')    = USER+ASSISTANT context, accumulated, re-read by ALL later turns (locality).
  TRANSIENT (class 'TRANSIENT') = one-shot TOOL-RESULT payload at the tail, dropped after its turn (cold).
Prefix classes:
  'SHARED' = hot prefix blocks identical across ALL sessions (cross-session shared system+tool-schema).
  'HOT'    = session-specific hot prefix tail.
"""
import random, csv, statistics, os, json, hashlib
from collections import OrderedDict

BLOCK_SIZE = 16

def chained_block_id(prefix_hash, content_token):
    h = hashlib.blake2b(digest_size=8)
    h.update(prefix_hash)
    h.update(str(content_token).encode())
    return h.digest()

def make_blocks(prefix_hash, tokens):
    ids, ph = [], prefix_hash
    for t in tokens:
        bid = chained_block_id(ph, t)
        ids.append(bid); ph = bid
    return ids, ph

def gen_trace(rng, n_sessions, turns_per_session, prefix_len,
              committed_blocks, transient_blocks, shared_prefix_frac):
    """Each turn prompt block order (radix): SHARED prefix -> HOT tail -> accumulated COMMITTED
    history -> new COMMITTED scratch -> TRANSIENT tool payload (tail, dropped next turn).
    Classes per block: SHARED / HOT / COMMIT / TRANSIENT."""
    prefix_blocks = max(1, prefix_len // BLOCK_SIZE)
    shared_blocks = max(0, int(prefix_blocks * shared_prefix_frac))

    shared_tokens = [("SHARED", i) for i in range(shared_blocks)]
    root = hashlib.blake2b(b"ROOT", digest_size=8).digest()
    shared_ids, shared_tail_hash = make_blocks(root, shared_tokens)

    sessions = []
    for s in range(n_sessions):
        tail_tokens = [("SESS", s, i) for i in range(prefix_blocks - shared_blocks)]
        hot_tail_ids, hot_tail_hash = make_blocks(shared_tail_hash, tail_tokens)
        sessions.append({
            "id": s,
            "hot_tail_ids": hot_tail_ids,
            "committed_history": [],         # accumulated COMMITTED block ids (reused)
            "committed_tail_hash": hot_tail_hash,
            "turns_done": 0,
        })

    pending = list(range(n_sessions))
    requests = []
    total_turns = n_sessions * turns_per_session
    while len(requests) < total_turns:
        rng.shuffle(pending)
        for sid in list(pending):
            sess = sessions[sid]
            if sess["turns_done"] >= turns_per_session:
                pending.remove(sid); continue
            t = sess["turns_done"]
            # New COMMITTED scratch (chained onto committed history -> persists)
            commit_tokens = [("COMMIT", sid, t, i) for i in range(committed_blocks)]
            new_commit_ids, new_commit_tail = make_blocks(sess["committed_tail_hash"], commit_tokens)
            # TRANSIENT tool payload (chained onto THIS turn's committed tail, but NOT persisted)
            trans_tokens = [("TRANS", sid, t, i) for i in range(transient_blocks)]
            trans_ids, _ = make_blocks(new_commit_tail, trans_tokens)

            blocks = (shared_ids + sess["hot_tail_ids"]
                      + sess["committed_history"] + new_commit_ids + trans_ids)
            classes = (["SHARED"] * len(shared_ids)
                       + ["HOT"] * len(sess["hot_tail_ids"])
                       + ["COMMIT"] * len(sess["committed_history"])
                       + ["COMMIT"] * len(new_commit_ids)
                       + ["TRANSIENT"] * len(trans_ids))
            requests.append({"session": sid, "turn": t, "blocks": blocks, "classes": classes})

            # Persist committed scratch; transient is dropped (not added to history, not in next prompt)
            sess["committed_history"] = sess["committed_history"] + new_commit_ids
            sess["committed_tail_hash"] = new_commit_tail
            sess["turns_done"] += 1
            if rng.random() < 0.5:
                break
    return requests, prefix_blocks

# ----------------------------------------------------------------------------
class Cache:
    def __init__(self, capacity, policy):
        self.capacity = capacity
        self.policy = policy
        self.store = OrderedDict()   # bid -> True ; order = recency (MRU at end)
        self.cls = {}                # bid -> class
        self.evictions = 0

    def contains(self, bid): return bid in self.store
    def touch(self, bid): self.store.move_to_end(bid, last=True)

    def insert(self, bid, klass):
        if bid in self.store:
            self.store.move_to_end(bid, last=True); return
        while len(self.store) >= self.capacity and self.capacity > 0:
            self._evict_one()
        if self.capacity <= 0: return
        self.store[bid] = True
        self.cls[bid] = klass

    def _first_lru_in(self, allowed):
        for bid in self.store:               # LRU -> MRU
            if self.cls.get(bid) in allowed:
                return bid
        return None

    def _evict_one(self):
        if not self.store: return
        victim = None
        p = self.policy
        if p == 'lru':
            victim = next(iter(self.store))
        elif p == 'pin_shared_prefix':
            # Protect SHARED blocks; LRU over everything else; only touch SHARED as last resort.
            victim = self._first_lru_in({'HOT', 'COMMIT', 'TRANSIENT'})
            if victim is None:
                victim = next(iter(self.store))   # only SHARED left
        elif p == 'naive2':
            # Pin full hot prefix (SHARED+HOT); evict ALL scratch (COMMIT+TRANSIENT) first, LRU within.
            victim = self._first_lru_in({'COMMIT', 'TRANSIENT'})
            if victim is None:
                victim = self._first_lru_in({'HOT'})
            if victim is None:
                victim = next(iter(self.store))   # only SHARED left
        elif p == 'adaptive3':
            # Evict order: TRANSIENT -> {COMMIT, HOT-tail} as normal LRU -> SHARED floor last.
            victim = self._first_lru_in({'TRANSIENT'})
            if victim is None:
                victim = self._first_lru_in({'COMMIT', 'HOT'})
            if victim is None:
                victim = next(iter(self.store))   # SHARED floor
        else:
            victim = next(iter(self.store))
        del self.store[victim]
        self.cls.pop(victim, None)
        self.evictions += 1

# ----------------------------------------------------------------------------
def simulate(requests, capacity, policy):
    cache = Cache(capacity, policy)
    total = 0; cached = 0
    per_session_total = {}; per_session_cached = {}
    for req in requests:
        sid = req["session"]
        prefix_intact = True
        for bid, klass in zip(req["blocks"], req["classes"]):
            total += BLOCK_SIZE
            per_session_total[sid] = per_session_total.get(sid, 0) + BLOCK_SIZE
            if prefix_intact and cache.contains(bid):
                cached += BLOCK_SIZE
                per_session_cached[sid] = per_session_cached.get(sid, 0) + BLOCK_SIZE
                cache.touch(bid)
            else:
                prefix_intact = False
                cache.insert(bid, klass)
    hit_rate = cached / total if total else 0.0
    # per-session hit rate & recompute (for paired bootstrap)
    per_sess = {}
    for sid in per_session_total:
        tt = per_session_total[sid]; cc = per_session_cached.get(sid, 0)
        per_sess[sid] = {"hit_rate": cc / tt if tt else 0.0, "recomp": tt - cc}
    return {
        "hit_rate": hit_rate,
        "recomputed_tokens": total - cached,
        "total_prompt_tokens": total,
        "evictions": cache.evictions,
        "per_session": per_sess,
    }

def count_distinct_hot_blocks(requests):
    hot = set()
    for req in requests:
        for bid, klass in zip(req["blocks"], req["classes"]):
            if klass in ("SHARED", "HOT"):
                hot.add(bid)
    return len(hot)

# ----------------------------------------------------------------------------
def paired_bootstrap(deltas, n_resamples=2000, seed=12345):
    """deltas: list of per-session paired Δ. Returns (mean, lo, hi) 95% CI."""
    if not deltas:
        return 0.0, 0.0, 0.0
    rng = random.Random(seed)
    n = len(deltas)
    means = []
    ch = rng.choices  # C-level resampling
    for _ in range(n_resamples):
        means.append(sum(ch(deltas, k=n)) / n)
    means.sort()
    lo = means[int(0.025 * n_resamples)]
    hi = means[int(0.975 * n_resamples) - 1]
    return statistics.mean(deltas), lo, hi

# ----------------------------------------------------------------------------
def main():
    HERE = os.path.dirname(os.path.abspath(__file__))
    RESULTS = os.path.join(HERE, "results"); LOGS = os.path.join(HERE, "logs")
    os.makedirs(RESULTS, exist_ok=True); os.makedirs(LOGS, exist_ok=True)

    PARAMS = dict(
        n_sessions=40, turns_per_session=8, prefix_len=2048,
        committed_blocks=8, transient_blocks=8,
    )
    CAP_FRACS = [0.25, 0.50, 0.75, 1.0, 1.5]
    SHARED_FRACS = [0.25, 0.50, 0.75, 0.90]
    SEEDS = [11, 23, 47, 71, 97, 113]
    POLICIES = ["lru", "pin_shared_prefix", "naive2", "adaptive3"]

    rows = []
    log = []
    # store per-session deltas keyed by (cap_frac, shared_frac, comparison) -> list
    boot_data = {}  # (cap, shared, cmp, metric) -> [deltas...]

    for seed in SEEDS:
        rng = random.Random(seed)
        for sfrac in SHARED_FRACS:
            requests, pblk = gen_trace(rng, shared_prefix_frac=sfrac, **PARAMS)
            distinct_hot = count_distinct_hot_blocks(requests)
            log.append(f"seed={seed} shared_frac={sfrac} requests={len(requests)} "
                       f"distinct_hot_blocks={distinct_hot} prefix_blocks/sess={pblk}")
            for frac in CAP_FRACS:
                capacity = max(1, round(distinct_hot * frac))
                persess = {}
                for policy in POLICIES:
                    r = simulate(requests, capacity, policy)
                    persess[policy] = r["per_session"]
                    rows.append(dict(seed=seed, cap_frac=frac, shared_frac=sfrac,
                                     capacity=capacity, distinct_hot=distinct_hot,
                                     policy=policy, hit_rate=r["hit_rate"],
                                     recomputed_tokens=r["recomputed_tokens"],
                                     total_prompt_tokens=r["total_prompt_tokens"],
                                     evictions=r["evictions"]))
                # accumulate per-session paired deltas for adaptive3 - lru and adaptive3 - pin
                for cmp_name, base in [("a3_minus_lru", "lru"),
                                       ("a3_minus_pin", "pin_shared_prefix")]:
                    a3 = persess["adaptive3"]; bp = persess[base]
                    for sid in a3:
                        dh = a3[sid]["hit_rate"] - bp[sid]["hit_rate"]
                        dr = a3[sid]["recomp"] - bp[sid]["recomp"]
                        boot_data.setdefault((frac, sfrac, cmp_name, "dhit"), []).append(dh)
                        boot_data.setdefault((frac, sfrac, cmp_name, "drecomp"), []).append(dr)

    # ---- Write raw CSV
    csv_path = os.path.join(RESULTS, "results.csv")
    fields = ["seed","cap_frac","shared_frac","capacity","distinct_hot","policy",
              "hit_rate","recomputed_tokens","total_prompt_tokens","evictions"]
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for row in rows: w.writerow(row)

    # ---- Aggregate mean±std across seeds+shared_frac per (cap_frac, policy) AND per shared_frac
    def agg_rows(filt):
        out = {}
        for row in rows:
            if not filt(row): continue
            out.setdefault(row["policy"], []).append(row)
        rec = {}
        for policy, g in out.items():
            hr = [x["hit_rate"] for x in g]; rt = [x["recomputed_tokens"] for x in g]
            ev = [x["evictions"] for x in g]
            rec[policy] = dict(
                hit_rate_mean=statistics.mean(hr),
                hit_rate_std=statistics.pstdev(hr) if len(hr)>1 else 0.0,
                recomp_mean=statistics.mean(rt),
                recomp_std=statistics.pstdev(rt) if len(rt)>1 else 0.0,
                evict_mean=statistics.mean(ev), n=len(g))
        return rec

    summary_by_cap = []
    for frac in CAP_FRACS:
        rec = {"cap_frac": frac, "policies": agg_rows(lambda r: r["cap_frac"]==frac)}
        summary_by_cap.append(rec)

    summary_by_cap_shared = []
    for frac in CAP_FRACS:
        for sfrac in SHARED_FRACS:
            rec = {"cap_frac": frac, "shared_frac": sfrac,
                   "policies": agg_rows(lambda r, f=frac, s=sfrac: r["cap_frac"]==f and r["shared_frac"]==s)}
            summary_by_cap_shared.append(rec)

    # ---- Paired bootstrap CIs, pooled over shared_frac per cap, AND per (cap, shared)
    boot_pooled = {}   # (cap, cmp, metric) -> (mean, lo, hi)
    pooled_acc = {}
    for (frac, sfrac, cmp_name, metric), deltas in boot_data.items():
        pooled_acc.setdefault((frac, cmp_name, metric), []).extend(deltas)
    for k, deltas in pooled_acc.items():
        boot_pooled[k] = paired_bootstrap(deltas)

    boot_by_shared = {}
    for (frac, sfrac, cmp_name, metric), deltas in boot_data.items():
        boot_by_shared[(frac, sfrac, cmp_name, metric)] = paired_bootstrap(deltas)

    def kkey(t): return "|".join(str(x) for x in t)
    summary = {
        "params": PARAMS, "cap_fracs": CAP_FRACS, "shared_fracs": SHARED_FRACS,
        "seeds": SEEDS, "policies": POLICIES,
        "by_cap": summary_by_cap,
        "by_cap_shared": summary_by_cap_shared,
        "bootstrap_pooled": {kkey(k): {"mean": v[0], "lo": v[1], "hi": v[2]}
                             for k, v in boot_pooled.items()},
        "bootstrap_by_shared": {kkey(k): {"mean": v[0], "lo": v[1], "hi": v[2]}
                                for k, v in boot_by_shared.items()},
    }
    with open(os.path.join(RESULTS, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    with open(os.path.join(LOGS, "run.log"), "w") as f:
        f.write("\n".join(log)+"\n")

    # ---- Human summary
    print("PARAMS:", PARAMS)
    print(f"seeds={SEEDS} shared_fracs={SHARED_FRACS}")
    print("\n=== POOLED over shared_frac & seeds, per cap_frac (mean hit-rate) ===")
    hdr = f"{'cap':>5} | " + " ".join(f"{p:>17}" for p in POLICIES)
    print(hdr)
    for rec in summary_by_cap:
        pol = rec["policies"]
        line = f"{rec['cap_frac']:>5} | " + " ".join(
            f"{pol[p]['hit_rate_mean']:>17.4f}" for p in POLICIES)
        print(line)
    print("\n=== Δhit vs baselines (adaptive3 - baseline), pooled, bootstrap 95% CI ===")
    print(f"{'cap':>5} | {'a3-LRU Δhit [CI]':>34} | {'a3-PIN Δhit [CI]':>34} | "
          f"{'frac of LRU-gap kept by PIN':>26}")
    for frac in CAP_FRACS:
        m_l, lo_l, hi_l = boot_pooled[(frac, "a3_minus_lru", "dhit")]
        m_p, lo_p, hi_p = boot_pooled[(frac, "a3_minus_pin", "dhit")]
        # fraction of (a3 vs lru) gap already captured by pin:
        # gap_a3_lru = a3-lru; gap_pin_lru = (a3-lru)-(a3-pin) = pin-lru
        gap_a3 = m_l
        gap_pin = m_l - m_p  # = pin - lru
        fr = (gap_pin / gap_a3) if abs(gap_a3) > 1e-12 else float('nan')
        print(f"{frac:>5} | {m_l:>+.5f} [{lo_l:>+.5f},{hi_l:>+.5f}] | "
              f"{m_p:>+.5f} [{lo_p:>+.5f},{hi_p:>+.5f}] | {fr*100:>23.1f}%")
    print(f"\nCSV: {csv_path}")
    return summary

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""EXP-0007 L0: bounded-W cache-aware admission vs SGLang-greedy vs VTC-fairness.
Extends EXP-0005 sim. Pure stdlib, serial. Three policies share ONE server model.

KEY EXTENSION vs EXP-0005:
  - THREE policies (greedy / vtc / bounded) instead of fcfs/pfa.
  - SERVICE-TIME FEEDBACK: service = BASE + PREFILL_COEF*recomputed_prefix_tokens + DECODE*scratch.
    Cache misses -> longer slot occupancy -> more queueing. Couples (p99, prefill).
Metrics: p99 wait (fairness axis) and total recomputed prefill tokens (prefill axis).
"""
import math, random, heapq
from collections import OrderedDict
from dataclasses import dataclass

BLOCK_SIZE = 16
PREFIX_LEN = 2048
BLOCKS_PER_FAMILY = PREFIX_LEN // BLOCK_SIZE   # 128
SCRATCH_RANGE = (32, 256)
BASE_SERVICE = 0.5
PREFILL_COEF = 0.0015   # per recomputed prefix token -> service-time feedback
DECODE_COEF = 0.0008    # per scratch token (same across policies; keeps loop realistic)

def zipf_weights(K, s):
    if s == 0.0:
        return [1.0/K]*K
    w = [1.0/((i+1)**s) for i in range(K)]
    tot = sum(w)
    return [x/tot for x in w]

@dataclass
class Req:
    rid: int
    family: int
    scratch: int
    arrival: float
    admit: float = -1.0
    skipped: int = 0

class BlockCache:
    """Shared LRU block prefix cache. Key=(family,block). Pinned blocks not evictable."""
    def __init__(self, capacity_blocks):
        self.cap = capacity_blocks
        self.order = OrderedDict()
        self.resident = set()
        self.pin = {}
        self.fam_res = {}
    def _touch(self, key):
        self.order.move_to_end(key)
    def admit_family(self, family):
        miss_blocks = 0
        keys = [(family, b) for b in range(BLOCKS_PER_FAMILY)]
        kset = set(keys)
        for key in keys:
            if key not in self.resident:
                miss_blocks += 1
                self._evict_for(1, protect=kset)
                self.resident.add(key)
                self.order[key] = True
                self.fam_res[family] = self.fam_res.get(family, 0) + 1
            else:
                self._touch(key)
        for key in keys:
            self.pin[key] = self.pin.get(key, 0) + 1
        return miss_blocks * BLOCK_SIZE
    def release_family(self, family):
        for b in range(BLOCKS_PER_FAMILY):
            key = (family, b)
            if key in self.pin:
                self.pin[key] -= 1
                if self.pin[key] <= 0:
                    del self.pin[key]
    def _evict_for(self, need, protect):
        while len(self.resident) + need > self.cap:
            victim = None
            for key in self.order:
                if key not in self.pin and key not in protect:
                    victim = key; break
            if victim is None:
                return
            del self.order[victim]
            self.resident.discard(victim)
            self.fam_res[victim[0]] -= 1
    def family_residency(self, family):
        return self.fam_res.get(family, 0)
    def family_resident(self, family):
        return self.fam_res.get(family, 0) == BLOCKS_PER_FAMILY

def simulate(policy, W, K, skew, lam, B, cap_blocks, M, seed):
    """policy in {greedy, vtc, bounded}. W only used by bounded (skip budget)."""
    rng = random.Random(seed)
    weights = zipf_weights(K, skew)
    fam_choices = list(range(K))
    reqs = []
    t = 0.0
    for i in range(M):
        t += rng.expovariate(lam)
        fam = rng.choices(fam_choices, weights=weights, k=1)[0]
        scratch = rng.randint(*SCRATCH_RANGE)
        reqs.append(Req(i, fam, scratch, t))
    cache = BlockCache(cap_blocks)
    queue = []
    arr_idx = 0
    free_slots = B
    completions = []
    now = 0.0
    recomp_tokens = 0
    total_prefix_blocks = M * BLOCKS_PER_FAMILY
    free_prefix_blocks = 0
    admitted = 0
    running_families = {}
    # VTC virtual-service counter: cumulative (weighted) service granted per family.
    vtc_service = {f: 0.0 for f in range(K)}

    def cache_score(r):
        # how cache-favorable: resident blocks now + in-batch bonus
        res = cache.family_residency(r.family)
        inbatch = running_families.get(r.family, 0)
        return res + (BLOCKS_PER_FAMILY if inbatch > 0 else 0)

    def pick():
        if policy == "greedy":
            # unbounded reorder: most cache-resident family, tie -> earliest arrival (lowest idx)
            best_i, best_s = 0, -1
            for idx, r in enumerate(queue):
                s = cache_score(r)
                if s > best_s:
                    best_s, best_i = s, idx
            return best_i
        if policy == "vtc":
            # least accrued virtual service, tie -> earliest arrival
            best_i, best_v = 0, math.inf
            for idx, r in enumerate(queue):
                v = vtc_service[r.family]
                if v < best_v:
                    best_v, best_i = v, idx
            return best_i
        # bounded: cache-aware but starvation-capped at W skips
        if W <= 0:
            return 0
        if queue and queue[0].skipped >= W:
            return 0
        best_i, best_s = 0, -1
        for idx, r in enumerate(queue):
            s = cache_score(r)
            if s > best_s:
                best_s, best_i = s, idx
        return best_i

    while admitted < M:
        if free_slots > 0 and queue:
            while free_slots > 0 and queue:
                idx = pick()
                r = queue.pop(idx)
                for j in range(idx):
                    queue[j].skipped += 1
                r.admit = now
                rt = cache.admit_family(r.family)
                recomp_tokens += rt
                free_prefix_blocks += (BLOCKS_PER_FAMILY - rt // BLOCK_SIZE)
                running_families[r.family] = running_families.get(r.family, 0) + 1
                # SERVICE-TIME FEEDBACK: misses cost prefill compute -> longer occupancy
                svc = BASE_SERVICE + PREFILL_COEF * rt + DECODE_COEF * r.scratch
                vtc_service[r.family] += svc   # VTC counts granted service
                comp = now + svc
                heapq.heappush(completions, (comp, r.rid, r.family))
                free_slots -= 1
                admitted += 1
            continue
        next_arr = reqs[arr_idx].arrival if arr_idx < M else math.inf
        next_comp = completions[0][0] if completions else math.inf
        if next_arr == math.inf and next_comp == math.inf:
            break
        if next_arr <= next_comp:
            now = next_arr
            queue.append(reqs[arr_idx]); arr_idx += 1
        else:
            now = next_comp
            ct, rid, fam = heapq.heappop(completions)
            cache.release_family(fam)
            running_families[fam] -= 1
            if running_families[fam] == 0:
                del running_families[fam]
            free_slots += 1
        if arr_idx >= M and not queue and not completions and admitted < M:
            break
    waits = [r.admit - r.arrival for r in reqs]
    waits.sort()
    def pct(p):
        if not waits: return 0.0
        k = min(len(waits) - 1, int(math.ceil(p / 100 * len(waits)) - 1))
        return waits[max(0, k)]
    return {
        "recomp_tokens": recomp_tokens,
        "hit_rate": free_prefix_blocks / total_prefix_blocks,
        "mean_wait": sum(waits) / len(waits),
        "p99_wait": pct(99),
        "p95_wait": pct(95),
        "max_wait": waits[-1],
    }

if __name__ == "__main__":
    cap = BLOCKS_PER_FAMILY * 8
    for pol, W in [("greedy", 0), ("vtc", 0), ("bounded", 4), ("bounded", 16)]:
        r = simulate(pol, W, K=8, skew=1.5, lam=1.0*4/0.7, B=4, cap_blocks=cap, M=400, seed=1)
        print(f"{pol:8s} W={W:3d}  p99={r['p99_wait']:7.2f}  recomp={r['recomp_tokens']:7d}  hit={r['hit_rate']:.3f}")

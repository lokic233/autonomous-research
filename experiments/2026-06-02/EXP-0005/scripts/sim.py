#!/usr/bin/env python3
"""EXP-0005 L0: prefix-family-aware batch admission vs FCFS on a shared block prefix cache.
Pure stdlib. Discrete-event continuous-batching simulator.

Model (see PRE_REGISTRATION.md):
- Poisson arrivals, K prefix families (Zipf skew), shared LRU block prefix cache.
- B continuous-batching slots, constant service time per request.
- Resident family blocks are FREE; missing blocks recomputed (PRIMARY metric).
- In-flight family blocks are pinned (not evictable). Completed -> evictable but resident.
- Policies: FCFS; PFA (prefer family already resident/running, bounded reorder window W).
"""
import math, random, heapq, csv, sys, json
from collections import OrderedDict
from dataclasses import dataclass, field

BLOCK_SIZE = 16
PREFIX_LEN = 2048              # long system+tool-schema prefix
BLOCKS_PER_FAMILY = PREFIX_LEN // BLOCK_SIZE   # 128 blocks
SCRATCH_RANGE = (32, 256)
BASE_SERVICE = 1.0             # constant service time per request (slot occupancy)

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
    skipped: int = 0          # times passed over by PFA

class BlockCache:
    """Shared LRU block prefix cache. Key = (family, block_idx). Pinned blocks not evictable."""
    def __init__(self, capacity_blocks):
        self.cap = capacity_blocks
        self.order = OrderedDict()   # key -> True, MRU at end (O(1) move/pop)
        self.resident = set()
        self.pin = {}          # key -> pin count (in-flight)
        self.fam_res = {}      # family -> count of resident blocks (fast residency check)
    def _touch(self, key):
        self.order.move_to_end(key)
    def admit_family(self, family):
        """Return recomputed prefill TOKENS for this family's prefix; insert+pin blocks."""
        miss_blocks = 0
        keys = [(family, b) for b in range(BLOCKS_PER_FAMILY)]
        kset = set(keys)
        for key in keys:
            if key not in self.resident:
                miss_blocks += 1
                self._evict_for(1, protect=kset)
                self.resident.add(key)
                self.order[key] = True
                self.fam_res[family] = self.fam_res.get(family,0)+1
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
            for key in self.order:   # iterate LRU->MRU
                if key not in self.pin and key not in protect:
                    victim = key; break
            if victim is None:
                return  # cannot evict (all pinned/protected) -> allow overflow (rare)
            del self.order[victim]
            self.resident.discard(victim)
            self.fam_res[victim[0]] -= 1
    def family_resident(self, family):
        return self.fam_res.get(family,0) == BLOCKS_PER_FAMILY

def simulate(policy, W, K, skew, lam, B, cap_blocks, M, seed):
    rng = random.Random(seed)
    weights = zipf_weights(K, skew)
    fam_choices = list(range(K))
    # generate arrivals
    reqs = []
    t = 0.0
    for i in range(M):
        t += rng.expovariate(lam)
        fam = rng.choices(fam_choices, weights=weights, k=1)[0]
        scratch = rng.randint(*SCRATCH_RANGE)
        reqs.append(Req(i, fam, scratch, t))
    cache = BlockCache(cap_blocks)
    # event-driven: slot free times
    queue = []          # list of Req not yet admitted, arrival order
    arr_idx = 0
    free_slots = B
    running = {}        # rid -> (family, complete_time)
    completions = []    # heap of (complete_time, rid)
    now = 0.0
    recomp_tokens = 0
    total_prefix_blocks = M * BLOCKS_PER_FAMILY
    free_prefix_blocks = 0
    admitted = 0
    running_families = {}  # family -> count in batch

    def pick(queue):
        # choose index in queue to admit per policy
        if policy == "fcfs" or W == 0:
            return 0
        # PFA: prefer a request whose family is resident OR running, honoring skip bound W.
        # enforce starvation bound: if head has been skipped >= W, must admit head
        if queue and queue[0].skipped >= W:
            return 0
        best = None
        for idx, r in enumerate(queue):
            resident = cache.family_resident(r.family)
            inbatch = running_families.get(r.family, 0) > 0
            if resident or inbatch:
                best = idx; break
        if best is None:
            return 0
        return best

    while admitted < M:
        # advance time: next event = next arrival or next completion
        next_arr = reqs[arr_idx].arrival if arr_idx < M else math.inf
        next_comp = completions[0][0] if completions else math.inf
        # if we have free slots and queued work, we can admit at current time
        if free_slots > 0 and queue:
            # admit as many as slots allow at current 'now'
            while free_slots > 0 and queue:
                idx = pick(queue)
                r = queue.pop(idx)
                # mark skip increments for those passed over (only those before idx)
                for j in range(idx):
                    queue[j].skipped += 1
                r.admit = now
                rt = cache.admit_family(r.family)
                recomp_tokens += rt
                free_prefix_blocks += (BLOCKS_PER_FAMILY - rt//BLOCK_SIZE)
                running_families[r.family] = running_families.get(r.family,0)+1
                comp = now + BASE_SERVICE
                heapq.heappush(completions, (comp, r.rid, r.family))
                free_slots -= 1
                admitted += 1
            continue
        # otherwise advance to next event
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
        k = min(len(waits)-1, int(math.ceil(p/100*len(waits))-1))
        return waits[max(0,k)]
    hit_rate = free_prefix_blocks / total_prefix_blocks
    return {
        "recomp_tokens": recomp_tokens,
        "hit_rate": hit_rate,
        "mean_wait": sum(waits)/len(waits),
        "p99_wait": pct(99),
        "max_wait": waits[-1],
    }

if __name__ == "__main__":
    # smoke test
    r = simulate("fcfs", 0, K=8, skew=1.0, lam=8.0, B=4, cap_blocks=BLOCKS_PER_FAMILY*2, M=200, seed=1)
    print("FCFS", r)
    r = simulate("pfa", 8, K=8, skew=1.0, lam=8.0, B=4, cap_blocks=BLOCKS_PER_FAMILY*2, M=200, seed=1)
    print("PFA ", r)
    print("BLOCKS_PER_FAMILY", BLOCKS_PER_FAMILY)

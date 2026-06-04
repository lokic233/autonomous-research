#!/usr/bin/env python3
# EXP-0067 / CLAIM-0058 — chunk-flush granularity vs streaming-moderator recall
# L0: CPU-only, stdlib-only, SERIAL, <=15 min. Harness owns GT; filter never reads GT.
import random, csv, json, statistics, math, os, time
from collections import deque

ART = "/Users/dengcchi/autonomous-research-v3/experiments/2026-06-04/EXP-0067/"
os.makedirs(ART, exist_ok=True)

# ---------------- VIOLATION LEXICON (committed in prereg). MAX_PHRASE_LEN = 4 ----------------
LEXICON = [
    # 1-token (NULL CONTROL — cannot be fragmented)
    ["slur1"], ["banned_word"],
    # 2-token
    ["kill", "yourself"], ["obf_a", "obf_b"], ["make", "meth"],
    # 3-token
    ["how", "to", "buildbomb"], ["step", "one", "poison"], ["obf_c", "obf_d", "obf_e"],
    # 4-token
    ["step", "by", "step", "poison"], ["a", "very", "banned", "phrase"],
]
MAX_PHRASE_LEN = max(len(p) for p in LEXICON)
LEX_TUPLES = set(tuple(p) for p in LEXICON)
# first-token map for decoy generation (near-miss: same first token, not a real phrase)
LEX_FIRST = {}
for p in LEXICON:
    LEX_FIRST.setdefault(p[0], []).append(tuple(p))

# benign vocabulary (~200 tokens), disjoint-ish from lexicon tokens
BENIGN_VOCAB = [f"w{i}" for i in range(200)]
LEX_TOKENS = set(t for p in LEXICON for t in p)

# ---------------- Aho-Corasick over TOKENS (pure python, stdlib) ----------------
class ACNode:
    __slots__ = ("children", "fail", "out", "depth")
    def __init__(self, depth=0):
        self.children = {}
        self.fail = None
        self.out = []          # phrase lengths that END at this node
        self.depth = depth

def build_ac(patterns):
    root = ACNode(0)
    for pat in patterns:
        node = root
        for tok in pat:
            nxt = node.children.get(tok)
            if nxt is None:
                nxt = ACNode(node.depth + 1)
                node.children[tok] = nxt
            node = nxt
        node.out.append(len(pat))
    # BFS fail links
    q = deque()
    for c in root.children.values():
        c.fail = root
        q.append(c)
    while q:
        cur = q.popleft()
        for tok, child in cur.children.items():
            q.append(child)
            f = cur.fail
            while f is not None and tok not in f.children:
                f = f.fail
            child.fail = f.children[tok] if (f and tok in f.children) else root
            child.out = child.out + child.fail.out
    return root

AC_ROOT = build_ac(LEXICON)

def ac_contains_violation(tokens):
    """True if ANY lexicon phrase fully occurs as a contiguous token subsequence of `tokens`.
       This is the FILTER. It only ever sees the tokens it is given (per moderator arm)."""
    node = AC_ROOT
    for tok in tokens:
        while node is not None and tok not in node.children:
            node = node.fail
        if node is None:
            node = AC_ROOT
            continue
        node = node.children[tok]
        if node.out:
            return True
    return False

# ---------------- DATASET SYNTHESIS (harness owns GT) ----------------
def synth_dataset(n, seed, p_viol=0.5, decoy_rate=0.3):
    rng = random.Random(seed)
    data = []  # list of dicts: tokens, is_viol(bool), phrase_len(int or 0)
    for _ in range(n):
        L = rng.randint(20, 60)
        toks = [rng.choice(BENIGN_VOCAB) for _ in range(L)]
        is_viol = rng.random() < p_viol
        plen = 0
        if is_viol:
            phrase = rng.choice(LEXICON)
            plen = len(phrase)
            pos = rng.randint(0, L - plen)  # ensure fits
            toks[pos:pos+plen] = list(phrase)
        else:
            # benign: optionally insert a near-miss decoy (same first tok, altered rest)
            if rng.random() < decoy_rate:
                base = rng.choice(LEXICON)
                if len(base) >= 2:
                    decoy = [base[0]] + [rng.choice(BENIGN_VOCAB) for _ in range(len(base)-1)]
                    if tuple(decoy) not in LEX_TUPLES:
                        pos = rng.randint(0, L - len(decoy))
                        toks[pos:pos+len(decoy)] = decoy
        data.append({"tokens": toks, "is_viol": is_viol, "plen": plen})
    return data

# ---------------- MODERATOR ARMS (consume the emitted chunk stream) ----------------
# The runtime emits `tokens` in chunks of size C. flush boundaries at C, 2C, ...
def chunks_of(tokens, C):
    return [tokens[i:i+C] for i in range(0, len(tokens), C)]

def arm_stateless(tokens, C, W=None):
    # scans ONLY each new chunk in isolation
    for ch in chunks_of(tokens, C):
        if ac_contains_violation(ch):
            return True
    return False

def arm_sliding(tokens, C, W):
    # maintains a buffer of last W emitted tokens; re-scans that window each flush
    buf = []
    for ch in chunks_of(tokens, C):
        buf.extend(ch)
        if len(buf) > W:
            buf = buf[-W:]
        if ac_contains_violation(buf):
            return True
    return False

def arm_unbounded(tokens, C, W=None):
    # re-scans the entire accumulated buffer every flush (== whole-text by final flush)
    buf = []
    for ch in chunks_of(tokens, C):
        buf.extend(ch)
        if ac_contains_violation(buf):
            return True
    return False

def whole_text_scan(tokens):
    return ac_contains_violation(tokens)

# ---------------- RECALL EVAL (harness compares alerts to GT) ----------------
def recall_for(data, arm_fn, C, W, only_multitoken=False, plen_filter=None):
    flagged = 0; total = 0
    for d in data:
        if not d["is_viol"]:
            continue
        if only_multitoken and d["plen"] < 2:
            continue
        if plen_filter is not None and d["plen"] != plen_filter:
            continue
        total += 1
        if arm_fn(d["tokens"], C, W):
            flagged += 1
    return (flagged / total) if total else float("nan"), total

def ci95(vals):
    vals = [v for v in vals if not (isinstance(v, float) and math.isnan(v))]
    if len(vals) < 2:
        return (statistics.mean(vals) if vals else float("nan"), 0.0)
    m = statistics.mean(vals); sd = statistics.stdev(vals)
    return m, 1.96 * sd / math.sqrt(len(vals))

print("MAX_PHRASE_LEN =", MAX_PHRASE_LEN, "| lexicon size =", len(LEXICON))
print("harness defined.")

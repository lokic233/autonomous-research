#!/usr/bin/env python3
"""EXP-0068 L0 harness: normalizer-divergence drives MinHash+LSH dedup false-negatives.
CPU-only, stdlib-only (unicodedata, hashlib, random), SERIAL.
Anti-circular: GT = model_normalize-identity (harness). Deduper sees only its own shingles."""
import unicodedata, hashlib, random, json, sys, math
from collections import defaultdict

# ---------- MODEL normalizer (harness GT; deduper NEVER calls this) ----------
def model_normalize(s):
    return unicodedata.normalize('NFKC', s).casefold()

# ---------- deduper-internal normalizers (PARAM) ----------
def norm_raw(s): return s
def norm_nfc(s): return unicodedata.normalize('NFC', s)
def norm_nfkc(s): return unicodedata.normalize('NFKC', s)
def norm_nfkc_cf(s): return unicodedata.normalize('NFKC', s).casefold()
NORMALIZERS = {'raw':norm_raw, 'NFC':norm_nfc, 'NFKC':norm_nfkc, 'NFKC+casefold':norm_nfkc_cf}

# ---------- vocab with multilingual/accented/punct content ----------
ASCII_WORDS = ("the model data dedup pipeline token corpus hash shingle band row jaccard "
    "minhash false negative recall threshold unicode normalize casefold accent ligature "
    "fullwidth compatibility codepoint divergence equivalence document pair memorize privacy "
    "contamination train eval safety system vocab tokenizer subsystem seam coupling").split()
ACCENT_WORDS = ["café","naïve","résumé","Zürich","São","fiancé","crème","piñata","jalapeño","Köln"]
VOCAB = ASCII_WORDS + ACCENT_WORDS

# normalizable substitution map: char -> compat/case/combining-equivalent that NFKC+casefold collapses
# (a) case: upper<->lower handled generically. (b) fullwidth digits/letters. (c) ligatures. (d) precomposed accents.
FULLWIDTH = {chr(c): chr(c + 0xFEE0) for c in range(0x21, 0x7F)}  # ! .. ~ -> fullwidth
LIGATURES = {'fi':'\ufb01','fl':'\ufb02','ff':'\ufb00'}           # 'fi'->ﬁ  (multi-char, handled separately)
# precomposed -> combining decomposition example handled by swapping precomposed for NFD form
PRECOMP = {'é':'e\u0301','è':'e\u0300','ï':'i\u0308','ñ':'n\u0303','ü':'u\u0308','ô':'o\u0302','â':'a\u0302','ç':'c\u0327'}

def make_base_doc(rng, length):
    return " ".join(rng.choice(VOCAB) for _ in range(length))

def apply_normalizable(doc, rng, M):
    """Return doc2 that is NFKC+casefold-equivalent to doc but differs in <=M raw codepoints.
    Each applied change is a compat/case/combining-equivalent swap."""
    chars = list(doc)
    # candidate positions: any char we can swap to an equivalent
    cands = []
    for i,ch in enumerate(chars):
        if ch in FULLWIDTH or ch in PRECOMP or ch.isalpha():
            cands.append(i)
    rng.shuffle(cands)
    applied = 0
    for i in cands:
        if applied >= M: break
        ch = chars[i]
        if ch in PRECOMP:
            chars[i] = PRECOMP[ch]; applied += 1
        elif ch in FULLWIDTH:
            chars[i] = FULLWIDTH[ch]; applied += 1
        elif ch.isalpha() and ch.lower()!=ch.upper():
            # case swap (NFKC+casefold collapses)
            chars[i] = ch.upper() if ch.islower() else ch.lower(); applied += 1
    doc2 = "".join(chars)
    return doc2, applied

NONNORM_SUBS = "0123456789@#%&*+=qwz"  # chars that don't normalize away into the alpha content
def apply_typo(doc, rng, positions):
    """Apply exactly len(positions) NON-normalizable real substitutions at the SAME-style positions.
    Matched raw edit distance (same count)."""
    chars = list(doc)
    applied = 0
    for i in positions:
        ch = chars[i]
        # pick a replacement that is different and does NOT normalize to ch
        repl = rng.choice(NONNORM_SUBS)
        while repl == ch:
            repl = rng.choice(NONNORM_SUBS)
        chars[i] = repl; applied += 1
    return "".join(chars), applied

def normalizable_positions(doc):
    return [i for i,ch in enumerate(doc) if ch in FULLWIDTH or ch in PRECOMP or (ch.isalpha() and ch.lower()!=ch.upper())]

# ---------- MinHash + banded LSH deduper (from scratch) ----------
def shingles(text, k=5):
    if len(text) < k:
        return {text} if text else set()
    return {text[i:i+k] for i in range(len(text)-k+1)}

# precompute hash perm params
def make_perms(num_perms, seed=12345):
    rng = random.Random(seed)
    MAXH = (1<<61)-1
    return [(rng.randrange(1,MAXH), rng.randrange(0,MAXH)) for _ in range(num_perms)], MAXH

def h_shingle(s):
    return int.from_bytes(hashlib.blake2b(s.encode('utf-8'),digest_size=8).digest(),'big')

def minhash_sig(shset, perms, MAXH):
    if not shset:
        return [0]*len(perms)
    base = [h_shingle(s) for s in shset]
    sig = []
    for a,b in perms:
        m = min((a*x+b) % MAXH for x in base)
        sig.append(m)
    return sig

def true_jaccard(s1,s2):
    if not s1 and not s2: return 1.0
    if not s1 or not s2: return 0.0
    inter = len(s1 & s2); uni = len(s1 | s2)
    return inter/uni if uni else 0.0

def lsh_collide(sig1, sig2, b, r):
    """Do two signatures collide in any band of b bands x r rows?"""
    for band in range(b):
        seg1 = tuple(sig1[band*r:(band+1)*r])
        seg2 = tuple(sig2[band*r:(band+1)*r])
        if seg1 == seg2:
            return True
    return False

# ---------- experiment ----------
def run_pair_eval(arm, dedup_norm_name, M, num_perms, b, r, n_pairs, base_len, seed):
    """Build n_pairs (doc1,doc2) under `arm` with M changes, run deduper under dedup_norm_name.
    Returns dict: fn_rate (over MODEL-identical pairs), flag_rate, mean_jaccard, n_gt_dup."""
    rng = random.Random(seed*1000 + hash(arm)%997 + hash(dedup_norm_name)%97)
    perms, MAXH = make_perms(num_perms, seed=999)
    dn = NORMALIZERS[dedup_norm_name]
    n_gt = 0; n_missed = 0; jac_list = []; flagged = 0; n_total = 0
    for _ in range(n_pairs):
        doc1 = make_base_doc(rng, base_len)
        if arm == 'normalizable':
            doc2, applied = apply_normalizable(doc1, rng, M)
            if applied == 0:  # skip if no swap possible
                continue
        else:  # typo
            pos = normalizable_positions(doc1)  # SAME position pool as normalizable arm -> matched
            rng.shuffle(pos)
            pos = pos[:M]
            if not pos:
                continue
            doc2, applied = apply_typo(doc1, rng, pos)
        n_total += 1
        # HARNESS GT (model view) — deduper never sees this
        is_gt_dup = (model_normalize(doc1) == model_normalize(doc2))
        # DEDUPER (its own normalizer only)
        s1 = shingles(dn(doc1)); s2 = shingles(dn(doc2))
        jac = true_jaccard(s1,s2)
        sig1 = minhash_sig(s1, perms, MAXH); sig2 = minhash_sig(s2, perms, MAXH)
        collide = lsh_collide(sig1, sig2, b, r)
        if collide: flagged += 1
        jac_list.append(jac)
        if is_gt_dup:
            n_gt += 1
            if not collide:
                n_missed += 1
    fn = (n_missed/n_gt) if n_gt else float('nan')
    return {
        'arm':arm, 'dedup_norm':dedup_norm_name, 'M':M, 'b':b, 'r':r,
        'n_total':n_total, 'n_gt_dup':n_gt, 'n_missed':n_missed,
        'fn_rate':fn, 'flag_rate':(flagged/n_total if n_total else float('nan')),
        'mean_jaccard':(sum(jac_list)/len(jac_list) if jac_list else float('nan')),
        'min_jaccard':(min(jac_list) if jac_list else float('nan')),
        'max_jaccard':(max(jac_list) if jac_list else float('nan')),
        'seed':seed,
    }

if __name__ == '__main__':
    pass

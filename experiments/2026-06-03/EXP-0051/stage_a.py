"""EXP-0051 Stage A — REAL-DATA ecological gate for CLAIM-0048.
Measures (a) empirical phi distribution and (b) empirical precision q of the
high-recall numeric canonicalizer, on REAL GSM8K + MATH-500 answers.
GT = gold-anchored true equivalence (two strings equiv iff same gold-parsed value)."""
import json, re, sys, random, collections, math
sys.path.insert(0,'.')
import canon
from canon import canon_exact, canon_lexical, canon_numeric
from sympy import Rational
import sympy

random.seed(12345)

# ---------- load REAL data ----------
def load_gsm8k():
    out=[]
    for line in open('gsm8k_test.jsonl'):
        d=json.loads(line)
        m=re.search(r'####\s*(.+)\s*$', d['answer'].strip())
        if m: out.append(m.group(1).strip().replace(',',''))
    return out  # integer strings

def load_math500():
    return [json.loads(l)['answer'] for l in open('math500.jsonl')]

gsm=load_gsm8k()
math500=load_math500()
print(f"REAL DATA: GSM8K golds={len(gsm)}  MATH-500 golds={len(math500)}", flush=True)

# ---------- gold-anchored GT value ----------
def gt_value(s):
    """Canonical TRUE value of a gold answer string (used ONLY for GT, never by canonicalizer logic
    in a circular way — this is the harness's notion of truth). Returns a hashable key or None."""
    v=canon._to_value(s)
    if v is not None:
        try: return ('V', str(sympy.simplify(v)))
        except: return ('V', str(v))
    return ('S', s.strip())  # symbolic/text gold: identity

# ============================================================
#  REALISTIC SURFACE-FORM GENERATORS (grounded in real formats)
# ============================================================
# For an INTEGER gold g (GSM8K), real model outputs express it as:
def gsm_surface_forms(g):
    n=int(g)
    forms={str(n)}
    forms.add(f"${n}")
    forms.add(f"{n} dollars")
    forms.add(f"{n}.0"); forms.add(f"{n}.00")
    if abs(n)>=1000:
        forms.add(f"{n:,}")          # 1,800
        forms.add(f"${n:,}")
    return list(forms)

# For a MATH gold a (string), real surface variety it appears in:
def math_surface_forms(a):
    forms={a, a.strip()}
    v=canon._to_value(a)
    if v is not None and v.is_rational and not v.is_integer:
        p,q=v.p,v.q
        forms.add(f"\\frac{{{p}}}{{{q}}}")
        forms.add(f"{p}/{q}")
        forms.add(f"\\dfrac{{{p}}}{{{q}}}")
        # decimal form if terminates
        dec=float(v)
        if abs(dec-round(dec,6))<1e-12:
            forms.add(f"{dec:.6f}".rstrip('0').rstrip('.'))
    if v is not None and v.is_integer:
        forms.add(str(int(v))); forms.add(f"{int(v)}.0")
    return list(forms)

# ============================================================
#  (b)  EMPIRICAL PRECISION q  of the HIGH-RECALL numeric normalizer
#       Build a large pool of REAL gold values (distinct) + their realistic
#       surface forms. For every PAIR the normalizer MERGES, q = frac truly
#       GT-equivalent. Over-merge (distinct golds -> same key) lowers q.
# ============================================================
def measure_precision_q(golds, surface_fn, label):
    # Build (surface_string, gt_key) corpus from distinct real golds.
    corpus=[]  # (string, gt_key)
    for g in golds:
        gk=gt_value(g)
        for s in surface_fn(g):
            corpus.append((s, gk))
    # group by normalizer key
    buckets=collections.defaultdict(list)
    for s,gk in corpus:
        key=canon_numeric(s)
        buckets[key].append(gk)
    merged_pairs=0; true_pairs=0
    overmerge_examples=[]
    for key,gks in buckets.items():
        n=len(gks)
        if n<2: continue
        # all C(n,2) pairs are "merged" by the normalizer
        from itertools import combinations
        cnt=collections.Counter(gks)
        npairs=n*(n-1)//2
        # truly-equivalent pairs = pairs sharing same gt_key
        tpairs=sum(c*(c-1)//2 for c in cnt.values())
        merged_pairs+=npairs; true_pairs+=tpairs
        if len(cnt)>1 and len(overmerge_examples)<8:
            overmerge_examples.append((key, dict(cnt)))
    q = true_pairs/merged_pairs if merged_pairs else float('nan')
    print(f"\n[q] {label}: merged_pairs={merged_pairs} true_pairs={true_pairs}  EMPIRICAL q={q:.4f}", flush=True)
    if overmerge_examples:
        print(f"   OVER-MERGE examples (distinct golds collapsed): {overmerge_examples[:4]}", flush=True)
    else:
        print("   NO over-merges across distinct real golds (numeric normalizer is exact-precision here).", flush=True)
    return q, merged_pairs, true_pairs

q_gsm = measure_precision_q(gsm, gsm_surface_forms, "GSM8K integer answers")
q_math = measure_precision_q(math500, math_surface_forms, "MATH-500 answers")

# Also measure recall improvement: fraction of truly-equiv surface pairs merged by numeric vs exact
def measure_recall(golds, surface_fn, label):
    tot_true=0; merged_exact=0; merged_num=0; merged_lex=0
    from itertools import combinations
    for g in golds:
        forms=surface_fn(g)
        if len(forms)<2: continue
        for a,b in combinations(set(forms),2):
            tot_true+=1
            if canon_exact(a)==canon_exact(b): merged_exact+=1
            if canon_lexical(a)==canon_lexical(b): merged_lex+=1
            if canon_numeric(a)==canon_numeric(b): merged_num+=1
    print(f"\n[recall] {label}: true-equiv pairs={tot_true}  exact={merged_exact/tot_true:.3f}  "
          f"lexical={merged_lex/tot_true:.3f}  numeric={merged_num/tot_true:.3f}", flush=True)
    return tot_true, merged_exact, merged_num

measure_recall(gsm, gsm_surface_forms, "GSM8K")
measure_recall(math500, math_surface_forms, "MATH-500")

print("\n=== Stage A precision/recall done ===", flush=True)

# ============================================================
#  ADVERSARIAL PRECISION: does the normalizer over-merge a GOLD with a
#  surface-close WRONG answer? (e.g. 1/3 vs 0.33, 18 vs 18.5, sqrt(13) vs 13)
#  This is the precision test that actually stresses recall-vs-precision tradeoff.
# ============================================================
def adversarial_precision(golds, surface_fn, wrong_fn, label):
    merged=0; true_eq=0; false_merge=[]
    for g in golds:
        gk=gt_value(g)
        gforms=surface_fn(g)
        wrongs=wrong_fn(g)   # list of (wrong_string, wrong_gt_key) truly DISTINCT from gold
        for gf in gforms:
            gkey=canon_numeric(gf)
            for ws,wk in wrongs:
                if canon_numeric(ws)==gkey:
                    merged+=1
                    if wk==gk: true_eq+=1
                    elif len(false_merge)<10: false_merge.append((gf,ws))
    # also count the legit merges among gold surface forms as true merges (baseline precision)
    q = (true_eq/merged) if merged else float('nan')
    print(f"\n[adv-q] {label}: gold-vs-wrong merges={merged} false(over)merges={merged-true_eq}", flush=True)
    if false_merge: print("   FALSE MERGES (gold~wrong collapsed):", false_merge[:6], flush=True)
    else: print("   ZERO false merges of gold with surface-close wrong answers.", flush=True)
    return merged-true_eq

def gsm_wrongs(g):
    n=int(g); out=[]
    # realistic arithmetic-slip wrong values: off-by-one, doubled, halved, +/- small, digit-swap
    cands=set()
    for d in (1,-1,2,-2,10,-10): cands.add(n+d)
    cands.add(n*2); cands.add(n//2 if n%2==0 else n)
    cands.discard(n)
    for w in cands:
        out.append((str(w), gt_value(str(w))))
        out.append((f"${w}", gt_value(str(w))))
        out.append((f"{w}.0", gt_value(str(w))))
    return out

def math_wrongs(a):
    out=[]; v=canon._to_value(a)
    if v is None: return out
    if v.is_rational and not v.is_integer:
        p,q=v.p,v.q
        # surface-close wrongs: truncated decimal, swapped num/den, off-by-one numerator
        cands=set()
        cands.add((p+1,q)); cands.add((p,q+1)); cands.add((q,p)) if p!=q else None
        for (pp,qq) in cands:
            if qq==0: continue
            ws=f"\\frac{{{pp}}}{{{qq}}}"; wk=gt_value(f"{pp}/{qq}")
            out.append((ws,wk)); out.append((f"{pp}/{qq}",wk))
        # truncated decimal of the gold (a WRONG distinct value): 1/3 -> 0.33
        dec=float(v)
        trunc=f"{dec:.2f}"
        if canon._to_value(trunc)!=v:
            out.append((trunc, gt_value(trunc)))
    if v.is_integer:
        n=int(v)
        for d in (1,-1,2):
            out.append((str(n+d), gt_value(str(n+d))))
    return out

adversarial_precision(gsm, gsm_surface_forms, gsm_wrongs, "GSM8K gold-vs-surface-close-wrong")
adversarial_precision(math500, math_surface_forms, math_wrongs, "MATH-500 gold-vs-surface-close-wrong")
print("\n=== adversarial precision done ===", flush=True)

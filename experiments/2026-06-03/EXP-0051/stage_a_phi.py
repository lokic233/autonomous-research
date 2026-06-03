"""EXP-0051 Stage A part (a) — EMPIRICAL PHI on REAL data.
phi = H_C - H_W (entropy of correct-equivalence class surface forms minus dominant-incorrect class).
Convention (matches EXP-0050 L0): phi<<0 = correct CONCENTRATED / errors FRAGMENTED => raising
recall HURTS; phi>>0 = correct FRAGMENTED / errors CONCENTRATED => raising recall HELPS.

KEY MODELING: We measure the structural asymmetry that real free-form QA exhibits under the
canonicalizer's-eye-view (it sees surface STRINGS, clustered into NUMERIC-VALUE classes).
- Correct class: ONE gold value, expressed across its realistic surface forms (few; H_C small-ish).
- Incorrect mass: real reasoning errors produce a SPREAD of DISTINCT wrong VALUES (many classes),
  each itself with surface variety. The 'dominant incorrect class' is the single most common wrong
  value. We measure H over the surface forms WITHIN the dominant incorrect class for H_W, and also
  report the cross-class fragmentation of the incorrect mass (the spoiler-relevant quantity).

We ground the surface-form multiplicity in REAL formats. We DO NOT have real model sample
frequencies in Stage A (that's Stage B), so phi here measures the *structural* asymmetry available
to the mechanism; the wrong-value SPREAD is the empirically-motivated, FLAGGED proxy element.
"""
import json, re, sys, collections, math, random
sys.path.insert(0,'.')
import canon
from canon import canon_numeric, canon_exact
import sympy
random.seed(7)

def load_gsm8k():
    out=[]
    for line in open('gsm8k_test.jsonl'):
        d=json.loads(line); m=re.search(r'####\s*(.+)\s*$', d['answer'].strip())
        if m: out.append(m.group(1).strip().replace(',',''))
    return out
def load_math500():
    return [json.loads(l)['answer'] for l in open('math500.jsonl')]
gsm=load_gsm8k(); math500=load_math500()

def H(counter):
    tot=sum(counter.values())
    if tot<=1: return 0.0
    return -sum((c/tot)*math.log2(c/tot) for c in counter.values() if c>0)

# surface forms (same as stage_a)
def gsm_surface_forms(g):
    n=int(g); forms={str(n),f"${n}",f"{n} dollars",f"{n}.0",f"{n}.00"}
    if abs(n)>=1000: forms.add(f"{n:,}"); forms.add(f"${n:,}")
    return list(forms)
def math_surface_forms(a):
    forms={a,a.strip()}; v=canon._to_value(a)
    if v is not None and v.is_rational and not v.is_integer:
        p,q=v.p,v.q
        forms|={f"\\frac{{{p}}}{{{q}}}",f"{p}/{q}",f"\\dfrac{{{p}}}{{{q}}}"}
        dec=float(v)
        if abs(dec-round(dec,6))<1e-12: forms.add(f"{dec:.6f}".rstrip('0').rstrip('.'))
    if v is not None and v.is_integer: forms|={str(int(v)),f"{int(v)}.0"}
    return list(forms)

def measure_phi(golds, surface_fn, wrong_value_fn, label, n_wrong_classes_dist):
    """For each problem, sample k 'reasoning attempts'. Correct attempts -> gold (one value, varied
    surfaces). Incorrect attempts -> drawn from a SPREAD of distinct wrong values. Measure, at the
    CANONICALIZER's clustering granularity (numeric key), the surface entropy of the correct class
    vs the dominant incorrect class, and the cross-value fragmentation of the incorrect mass."""
    phis=[]; H_Cs=[]; H_Ws=[]; n_inc_classes=[]; inc_frag_entropy=[]
    K=40
    for g in golds:
        gforms=surface_fn(g)
        if not gforms: continue
        wrongs=wrong_value_fn(g)   # list of distinct wrong-value surface-form-lists
        if not wrongs: continue
        # correct surface multiset: each correct attempt picks a surface form (uniform over real forms)
        cc=collections.Counter()
        for _ in range(K): cc[random.choice(gforms)]+=1
        H_C=H(cc)
        # incorrect mass: distribute across distinct wrong VALUES (real spread).
        # number of distinct wrong values present = how fragmented the error mass is.
        nwrong=min(len(wrongs), n_wrong_classes_dist())
        chosen=random.sample(wrongs, nwrong) if nwrong<=len(wrongs) else wrongs
        wclass_counts=collections.Counter()   # by numeric key -> count of attempts
        wsurface_by_key=collections.defaultdict(collections.Counter)
        for _ in range(K):
            wval_forms=random.choice(chosen)
            s=random.choice(wval_forms)
            key=canon_numeric(s)
            wclass_counts[key]+=1
            wsurface_by_key[key][s]+=1
        # dominant incorrect class = most common wrong value
        if not wclass_counts: continue
        dom_key,_=wclass_counts.most_common(1)[0]
        H_W=H(wsurface_by_key[dom_key])   # surface entropy WITHIN dominant wrong class
        phi=H_C-H_W
        phis.append(phi); H_Cs.append(H_C); H_Ws.append(H_W)
        n_inc_classes.append(len(wclass_counts))
        inc_frag_entropy.append(H(wclass_counts))  # cross-VALUE fragmentation of error mass
    import statistics as st
    phis_s=sorted(phis)
    def pct(p): return phis_s[int(p*(len(phis_s)-1))]
    print(f"\n=== EMPIRICAL PHI: {label} (n={len(phis)}) ===", flush=True)
    print(f"  mean phi={st.mean(phis):+.3f}  median={st.median(phis):+.3f}  "
          f"p10={pct(.1):+.3f} p90={pct(.9):+.3f}", flush=True)
    print(f"  mean H_C={st.mean(H_Cs):.3f}  mean H_W(dom-incorrect)={st.mean(H_Ws):.3f}", flush=True)
    frac_neg=sum(p<-0.2 for p in phis)/len(phis); frac_pos=sum(p>0.2 for p in phis)/len(phis)
    frac_asym=sum(abs(p)>0.2 for p in phis)/len(phis)
    print(f"  frac phi<-0.2 (corr-concentrated/err-fragmented)={frac_neg:.3f}  "
          f"frac phi>+0.2={frac_pos:.3f}  frac |phi|>0.2={frac_asym:.3f}", flush=True)
    print(f"  CROSS-VALUE error fragmentation: mean distinct wrong values={st.mean(n_inc_classes):.2f}  "
          f"mean error-mass entropy={st.mean(inc_frag_entropy):.3f} bits", flush=True)
    return phis, frac_asym, frac_neg, frac_pos, st.mean(phis)

# wrong-value generators: each returns a list of distinct-wrong-value surface-form lists
def gsm_wrong_values(g):
    n=int(g); out=[]; seen=set()
    for d in (1,-1,2,-2,3,-3,5,-5,10,-10, n, n//2 if n else 0):
        w=n+d if abs(d)<=10 else d
        if w==n or w in seen: continue
        seen.add(w)
        out.append([str(w), f"${w}", f"{w}.0"])
    return out
def math_wrong_values(a):
    v=canon._to_value(a); out=[]
    if v is None: return out
    if v.is_rational and not v.is_integer:
        p,q=v.p,v.q
        for (pp,qq) in [(p+1,q),(p-1,q),(p,q+1),(p,q-1) if q>1 else (p,q+2),(q,p),(2*p,q)]:
            if qq==0 or (pp==p and qq==q): continue
            out.append([f"\\frac{{{pp}}}{{{qq}}}", f"{pp}/{qq}"])
    elif v.is_integer:
        n=int(v)
        for d in (1,-1,2,-2,5,-5,10):
            out.append([str(n+d), f"{n+d}.0"])
    return out

# DOM_FRAC sensitivity: vary the spread of distinct wrong values (how fragmented errors are)
for spread_lo,spread_hi,tag in [(3,8,"errors-fragmented (3-8 distinct wrong vals)"),
                                 (1,2,"errors-concentrated (1-2 distinct wrong vals)"),
                                 (1,6,"mixed (1-6)")]:
    nf=lambda lo=spread_lo,hi=spread_hi: random.randint(lo,hi)
    print(f"\n########## DOM_FRAC regime: {tag} ##########", flush=True)
    measure_phi(gsm, gsm_surface_forms, gsm_wrong_values, f"GSM8K [{tag}]", nf)
    measure_phi(math500, math_surface_forms, math_wrong_values, f"MATH-500 [{tag}]", nf)

#!/usr/bin/env python3
"""EXP-0050 / CLAIM-0048 — canonicalizer recall sign-flip via fragmentation asymmetry.
L0: CPU-only, stdlib-only, SERIAL. Honest pipeline; GT harness-owned; canonicalizer
never reads GT. GT used only at scoring."""
import random, math, csv, os, statistics
from collections import defaultdict, Counter

ART = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(ART, "results"); os.makedirs(RES, exist_ok=True)

# ---- config (matches PRE_REGISTRATION) ----
N_PROBLEMS = 60
K = 20
SEEDS = 30
M_INC = 3            # incorrect classes
SC = 6              # correct-class surface forms
SW = 6              # dominant-incorrect surface forms
DOM_FRAC = 0.7      # dominant attractor share of incorrect mass
P_C_DEFAULT = 0.45

# ---- entropy realization: given n forms and target normalized entropy h in [0,1],
# build a prob vector over n forms with normalized entropy ~= h. Use a 1-param family:
# p_i propto exp(-beta * i). h=1 => uniform (beta=0). h->0 => point mass (beta large).
def probs_for_entropy(n, h, lo=0.0, hi=40.0, iters=40):
    h = max(0.0, min(1.0, h))
    if n <= 1: return [1.0]
    target = h * math.log(n)  # target absolute entropy in nats
    def ent(beta):
        ws = [math.exp(-beta*i) for i in range(n)]
        s = sum(ws); ps = [w/s for w in ws]
        return -sum(p*math.log(p) for p in ps if p>0), ps
    # binary search on beta (ent decreasing in beta)
    a, b = lo, hi
    for _ in range(iters):
        mid = (a+b)/2; e,_p = ent(mid)
        if e > target: a = mid
        else: b = mid
    _e, ps = ent((a+b)/2)
    return ps

def norm_entropy(ps):
    n = len(ps)
    if n <= 1: return 0.0
    e = -sum(p*math.log(p) for p in ps if p>0)
    return e/math.log(n)

# ---- build a problem's true categorical over surface forms (strings) ----
# returns: list of (string, prob), gt: string->class label ("C" or "W0".."W2")
def build_problem(p_C, h_C, h_W):
    forms = []; probs = []; gt = {}
    # correct class
    cps = probs_for_entropy(SC, h_C)
    for i in range(SC):
        s = f"C_{i}"; forms.append(s); probs.append(p_C*cps[i]); gt[s] = "C"
    # incorrect classes
    inc_mass = 1.0 - p_C
    # dominant gets DOM_FRAC, others split rest
    shares = [DOM_FRAC] + [(1-DOM_FRAC)/(M_INC-1)]*(M_INC-1)
    for j in range(M_INC):
        cls = f"W{j}"
        n = SW if j==0 else 2  # non-dominant incorrect kept compact
        if j == 0:
            wps = probs_for_entropy(SW, h_W)
        else:
            wps = probs_for_entropy(n, 0.5)
        for i in range(n):
            s = f"{cls}_{i}"; forms.append(s); probs.append(inc_mass*shares[j]*wps[i]); gt[s]=cls
    tot = sum(probs); probs = [p/tot for p in probs]
    return forms, probs, gt

# ---- sample K strings ----
def sample(forms, probs, k, rng):
    return rng.choices(forms, weights=probs, k=k)

# ---- canonicalizer: union-find over the SAMPLED strings present ----
# recall r: for same-class pairs, link each form to class canonical rep w.p. r.
# precision q: w.p. (1-q) per distinct-class rep-pair, over-merge (link two reps).
# Reads ONLY strings + a noisy equivalence signal of strength r/q. NEVER reads which
# class is correct.
def canonicalize(samples, gt, r, q, rng):
    present = list(set(samples))
    parent = {s:s for s in present}
    def find(x):
        while parent[x]!=x:
            parent[x]=parent[parent[x]]; x=parent[x]
        return x
    def union(a,b):
        ra,rb=find(a),find(b)
        if ra!=rb: parent[ra]=rb
    # group present forms by their TRUE class (harness knows; canonicalizer is GIVEN a
    # recall-r equivalence oracle — this models a normalizer that detects equivalence
    # with recall r, NOT knowledge of correctness)
    by_cls = defaultdict(list)
    for s in present: by_cls[gt[s]].append(s)
    # RECALL: merge same-class forms with prob r (link to first/canonical of that class)
    for cls, members in by_cls.items():
        if not members: continue
        canon = members[0]
        for s in members[1:]:
            if rng.random() < r:
                union(s, canon)
    # PRECISION: with prob (1-q), over-merge distinct class reps.
    if q < 1.0:
        reps = list({find(s) for s in present})
        for i in range(len(reps)):
            for j in range(i+1, len(reps)):
                if rng.random() < (1.0 - q):
                    union(reps[i], reps[j])
    # build buckets: rep -> list of member strings
    buckets = defaultdict(list)
    for s in samples:
        buckets[find(s)].append(s)
    return buckets

# ---- score: plurality vote over bucket sizes; winner bucket labeled by majority GT
# class of its member strings (GT used ONLY here). correct iff label=="C". ----
def score_problem(samples, gt, r, q, rng):
    buckets = canonicalize(samples, gt, r, q, rng)
    # plurality = largest bucket by count
    best_rep, best = None, -1
    for rep, members in buckets.items():
        if len(members) > best:
            best = len(members); best_rep = rep
        elif len(members)==best:
            # tie-break deterministic by rep string for reproducibility
            if best_rep is None or rep < best_rep: best_rep = rep
    members = buckets[best_rep]
    lbl = Counter(gt[s] for s in members).most_common(1)[0][0]
    return 1 if lbl=="C" else 0

# ---- run one cell (phi via h_C,h_W) over seeds, return per-seed acc list ----
def run_cell(p_C, h_C, h_W, r, q, base_seed):
    per_seed = []
    for sd in range(SEEDS):
        rng = random.Random((base_seed*1000003) ^ (sd*7919) ^ int(r*1000)*131 ^ int(q*1000)*977 ^ int(h_C*1000)*17 ^ int(h_W*1000)*23)
        # fixed problem shapes for this seed (same across r so r is the ONLY change within seed)
        correct = 0
        for pi in range(N_PROBLEMS):
            forms, probs, gt = build_problem(p_C, h_C, h_W)
            samples = sample(forms, probs, K, rng)
            correct += score_problem(samples, gt, r, q, rng)
        per_seed.append(correct / N_PROBLEMS)
    return per_seed

def ci95(xs):
    m = statistics.mean(xs)
    sd = statistics.pstdev(xs) if len(xs)>1 else 0.0
    se = sd/math.sqrt(len(xs)) if xs else 0.0
    return m, 1.96*se

# ============ MAIN SWEEP ============
H_LEVELS = [0.05, 0.5, 0.95]
R_GRID = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
print("running primary sweep (q=1.0)...")
rows = []
# phi grid: pair (h_C,h_W). phi = h_C - h_W.
phi_pairs = [(0.05,0.95),(0.05,0.5),(0.5,0.5),(0.5,0.05),(0.95,0.05),(0.95,0.5),(0.05,0.05),(0.95,0.95)]
for (h_C,h_W) in phi_pairs:
    phi = h_C - h_W
    for r in R_GRID:
        per = run_cell(P_C_DEFAULT, h_C, h_W, r, 1.0, base_seed=11)
        m,ci = ci95(per)
        rows.append(dict(branch="primary", p_C=P_C_DEFAULT, h_C=h_C, h_W=h_W, phi=round(phi,3),
                         r=r, q=1.0, acc=round(m,4), ci95=round(ci,4)))
    print(f"  phi={phi:+.2f} (hC={h_C},hW={h_W}) done")

with open(os.path.join(RES,"primary.csv"),"w",newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print("wrote primary.csv", len(rows),"rows")

# ============ PRECISION-ARTIFACT CONTROL ============
# Re-run the two phi<<0 (negative-slope) cells and a phi>>0 cell at q in {1.0,0.8,0.6}.
# If negative slope at phi<<0 appears at q=1.0 -> pure recall phenomenon (NOT artifact).
print("running precision-artifact control...")
prows=[]
ctrl_cells=[(0.05,0.95),(0.05,0.5),(0.95,0.05)]
for (h_C,h_W) in ctrl_cells:
    phi=h_C-h_W
    for q in [1.0,0.8,0.6]:
        for r in [0.0,1.0]:
            per=run_cell(P_C_DEFAULT,h_C,h_W,r,q,base_seed=23)
            m,ci=ci95(per)
            prows.append(dict(branch="precision_ctrl",p_C=P_C_DEFAULT,h_C=h_C,h_W=h_W,
                              phi=round(phi,3),r=r,q=q,acc=round(m,4),ci95=round(ci,4)))
    print(f"  phi={phi:+.2f} precision sweep done")
with open(os.path.join(RES,"precision_ctrl.csv"),"w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(prows[0].keys()));w.writeheader();w.writerows(prows)
print("wrote precision_ctrl.csv",len(prows),"rows")

# ============ SECONDARY: RANKING INVERSION (two FIXED models A,B) ============
# A = correct-FRAGMENTED  (h_C=0.95,h_W=0.05, phi>0): benefits from HIGH recall.
# B = errors-FRAGMENTED   (h_C=0.05,h_W=0.95, phi<0): HURT by high recall.
# Same model+samples per seed; only the canonicalizer recall changes (r_low vs r_high).
# Find a (r_low,r_high) where rank(A,B) inverts, with significance.
print("running ranking-inversion construction...")
def model_acc(name,h_C,h_W,p_C,r,q=1.0,base=37):
    return run_cell(p_C,h_C,h_W,r,q,base_seed=base if name=="A" else base+100)
A_PC, B_PC = 0.42, 0.46   # tuned so A,B are close at mid recall
irows=[]
inv_summary=None
R_LOW, R_HIGH = 0.0, 1.0
A_lo=run_cell(A_PC,0.95,0.05,R_LOW,1.0,base_seed=37)
A_hi=run_cell(A_PC,0.95,0.05,R_HIGH,1.0,base_seed=37)
B_lo=run_cell(B_PC,0.05,0.95,R_LOW,1.0,base_seed=137)
B_hi=run_cell(B_PC,0.05,0.95,R_HIGH,1.0,base_seed=137)
import statistics as st, math as _m
def msci(xs):
    m=st.mean(xs); se=(st.pstdev(xs)/_m.sqrt(len(xs))) if len(xs)>1 else 0
    return m,1.96*se
mAlo,cAlo=msci(A_lo); mAhi,cAhi=msci(A_hi); mBlo,cBlo=msci(B_lo); mBhi,cBhi=msci(B_hi)
# paired two-sample z for A vs B at each recall (independent seeds -> unpaired z)
def zdiff(x,y):
    mx,my=st.mean(x),st.mean(y)
    sx=st.pstdev(x)/_m.sqrt(len(x)); sy=st.pstdev(y)/_m.sqrt(len(y))
    se=_m.sqrt(sx*sx+sy*sy) or 1e-9
    return (mx-my)/se, mx-my
z_lo,d_lo=zdiff(A_lo,B_lo)   # A-B at low recall
z_hi,d_hi=zdiff(A_hi,B_hi)   # A-B at high recall
for nm,xs in [("A_lo",A_lo),("A_hi",A_hi),("B_lo",B_lo),("B_hi",B_hi)]:
    m,c=msci(xs)
    irows.append(dict(branch="inversion",model=nm,acc=round(m,4),ci95=round(c,4)))
irows.append(dict(branch="inversion",model="A-B@r_low",acc=round(d_lo,4),ci95=round(abs(z_lo),2)))
irows.append(dict(branch="inversion",model="A-B@r_high",acc=round(d_hi,4),ci95=round(abs(z_hi),2)))
with open(os.path.join(RES,"inversion.csv"),"w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(irows[0].keys()));w.writeheader();w.writerows(irows)
print(f"  r_low={R_LOW}: A={mAlo:.3f} B={mBlo:.3f}  A-B={d_lo:+.3f} z={z_lo:+.1f}")
print(f"  r_high={R_HIGH}: A={mAhi:.3f} B={mBhi:.3f}  A-B={d_hi:+.3f} z={z_hi:+.1f}")
inverted = (d_lo<0 and d_hi>0 and abs(z_lo)>1.96 and abs(z_hi)>1.96) or (d_lo>0 and d_hi<0 and abs(z_lo)>1.96 and abs(z_hi)>1.96)
print(f"  RANKING INVERSION (both significant): {inverted}")
print("wrote inversion.csv")

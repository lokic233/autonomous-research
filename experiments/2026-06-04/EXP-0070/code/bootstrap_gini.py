import json, os, sys, unicodedata, collections, random, math
sys.path.insert(0, "/Users/dengcchi/autonomous-research-v3/experiments/2026-06-04/EXP-0069/code")
from normalizers import model_norm, prod_norm

DATA = "/Users/dengcchi/autonomous-research-v3/experiments/2026-06-04/EXP-0069/data"
LANGS = ["ja","zh","ar","de","fr"]
MAXD = 4000
MAXLEN = 50000
T = 0.8

def fine_class(c):
    cp=ord(c); n=unicodedata.name(c,"")
    if 0xFF01<=cp<=0xFF5E: return "fullwidth_ascii"
    if 0xFF61<=cp<=0xFFDC: return "halfwidth_kana_hangul"
    if 0xFFE0<=cp<=0xFFEE: return "fullwidth_sign"
    if "MATHEMATICAL" in n: return "math_alphanumeric"
    if "CIRCLED" in n or "PARENTHESIZED" in n or (0x2460<=cp<=0x24FF): return "enclosed_circled"
    if "SQUARE" in n or (0x3300<=cp<=0x33FF): return "cjk_squared"
    if "LIGATURE" in n: return "ligature"
    if "SUPERSCRIPT" in n or "SUBSCRIPT" in n or (0x1D2C<=cp<=0x1DBF): return "super_subscript_modifier"
    if "PRESENTATION FORM" in n: return "presentation_form"
    if "ROMAN NUMERAL" in n: return "roman_numeral"
    if 0xF900<=cp<=0xFAFF: return "cjk_compat_ideograph"
    if "VULGAR FRACTION" in n: return "fraction"
    return "other_compat"

def shingles(s,k=5):
    s=s.replace(" ","")
    return set(s[i:i+k] for i in range(max(0,len(s)-k+1)))
def jacc(a,b):
    if not a and not b: return 1.0
    if not a or not b: return 0.0
    return len(a&b)/len(a|b)

# Per-pair records: lang -> list of dicts {fn(0/1), shingle_fn(0/1 among fn), dom_class}
per_lang_pairs = {l: [] for l in LANGS}
all_pairs = []  # pooled fn indicators
all_fn_shingle = []  # among fn pairs, did it survive minhash T=0.8 (1/0)
dom_class_counter = collections.Counter()  # per-pair dominant residual class (fn pairs only)
class_drive_total = collections.Counter()  # total residual-driving chars per class

for lang in LANGS:
    path=os.path.join(DATA,f"c4_{lang}.jsonl")
    n=0
    with open(path) as f:
        for line in f:
            if n>=MAXD: break
            n+=1
            d=json.loads(line)["text"][:MAXLEN]
            twin=unicodedata.normalize("NFKC", d)
            if twin==d: continue
            if model_norm(d)!=model_norm(twin): continue
            pd,pt=prod_norm(d),prod_norm(twin)
            fn = 1 if pd!=pt else 0
            rec = {"fn": fn}
            if fn:
                # driving char classes
                cl=collections.Counter()
                for c in d:
                    mc=model_norm(c)
                    if mc and mc!=c and prod_norm(c)!=prod_norm(mc):
                        cl[fine_class(c)]+=1
                class_drive_total.update(cl)
                dom = cl.most_common(1)[0][0] if cl else "other_compat"
                dom_class_counter[dom]+=1
                rec["dom"]=dom
                # minhash shingle survival
                rec["shingle_fn"] = 1 if jacc(shingles(pd),shingles(pt))<T else 0
            per_lang_pairs[lang].append(rec)
            all_pairs.append(fn)

# ---------- bootstrap ----------
random.seed(20260604)
B=10000
def boot_ci(indicators, B=B, seed=20260604):
    """Nonparametric percentile bootstrap on a Bernoulli 0/1 sample.
    A resample of N items with replacement has #successes ~ Binomial(N, p_hat)
    EXACTLY (each draw is i.i.d. Bernoulli(p_hat)); so resample-mean = Binomial(N,p_hat)/N.
    We generate B such resample means and take the 2.5/97.5 percentiles. This is the
    standard nonparametric bootstrap for a proportion, generated efficiently."""
    N=len(indicators)
    if N==0: return (None,None,None)
    k=sum(indicators); phat=k/N
    rng=random.Random(seed)
    means=[]
    for _ in range(B):
        # Binomial(N, phat) via summed Bernoulli is O(N*B)=too slow for N~9k; use rng.random count
        # fast: sample resample mean = (#successes)/N where successes ~ Binomial(N,phat).
        # generate Binomial efficiently with the inverse-cdf-free BTPE-ish: use sum over geometric jumps.
        # Simpler exact: use random.binomialvariate if available (py>=3.12), else normal-approx fallback.
        means.append(_binom(rng, N, phat)/N)
    means.sort()
    lo=means[int(0.025*B)]; hi=means[min(int(0.975*B), B-1)]
    return (phat, lo, hi)

def _binom(rng, n, p):
    if hasattr(rng, "binomialvariate"):
        return rng.binomialvariate(n, p)
    # BG (Bernoulli-geometric) sampler: count successes by skipping failures via geometric gaps.
    if p<=0: return 0
    if p>=1: return n
    import math as _m
    count=0; i=-1
    logq=_m.log1p(-p)
    while True:
        u=rng.random()
        i += 1 + int(_m.log(u)/logq)
        if i>=n: break
        count+=1
    return count

results={"B":B,"seed":20260604,"per_lang_residual_fn_rate_CI":{}, }
for lang in LANGS:
    ind=[r["fn"] for r in per_lang_pairs[lang]]
    p,lo,hi=boot_ci(ind)
    results["per_lang_residual_fn_rate_CI"][lang]={"n_pairs":len(ind),"point":p,"ci_lo":lo,"ci_hi":hi}

p,lo,hi=boot_ci(all_pairs)
results["pooled_residual_fn_rate_CI"]={"n_pairs":len(all_pairs),"point":p,"ci_lo":lo,"ci_hi":hi}

# minhash survival CI (among fn pairs, pooled)
mh=[]
for lang in LANGS:
    for r in per_lang_pairs[lang]:
        if r["fn"]: mh.append(r["shingle_fn"])
p,lo,hi=boot_ci(mh)
results["pooled_minhash_survival_rate_CI"]={"n_fn_pairs":len(mh),"point":p,"ci_lo":lo,"ci_hi":hi}

# ---------- Gini / concentration ----------
def gini(counts):
    xs=sorted(counts)
    n=len(xs); s=sum(xs)
    if n==0 or s==0: return None
    cum=0
    for i,x in enumerate(xs,1):
        cum+=i*x
    return (2*cum)/(n*s)-(n+1)/n

# concentration over total residual-driving char counts
cd=dict(class_drive_total.most_common())
tot_chars=sum(cd.values())
top1_char=max(cd.values())/tot_chars
top10_char=sum(sorted(cd.values(),reverse=True)[:10])/tot_chars
gini_char=gini(list(cd.values()))

# concentration over per-pair dominant-class assignment
dc=dict(dom_class_counter.most_common())
tot_pairs_fn=sum(dc.values())
top1_pair=max(dc.values())/tot_pairs_fn
top10_pair=sum(sorted(dc.values(),reverse=True)[:10])/tot_pairs_fn
gini_pair=gini(list(dc.values()))
# how many distinct classes hold >=1% of dominant-pair mass
nontrivial=[k for k,v in dc.items() if v/tot_pairs_fn>=0.01]

results["concentration"]={
  "char_level": {"total_driving_chars":tot_chars,"top1_class_share":top1_char,"top10_class_share":top10_char,"gini":gini_char,"by_class":cd},
  "per_pair_dominant_class": {"total_fn_pairs":tot_pairs_fn,"top1_class_share":top1_pair,"top10_class_share":top10_pair,"gini":gini_pair,"classes_geq_1pct":nontrivial,"by_class":dc},
}

out="/Users/dengcchi/autonomous-research-v3/experiments/2026-06-04/EXP-0070/results/bootstrap_gini.json"
with open(out,"w") as f: json.dump(results,f,indent=2,ensure_ascii=False)
print(json.dumps(results,indent=2,ensure_ascii=False))

"""DECISIVE L1 — residual_FN on real C4-multilingual. Optimized w/ precomputed per-codepoint tables."""
import json, sys, os, unicodedata, random, collections
from normalizers import model_norm, prod_norm, prod_norm_textdedup, classify_variant
DATA = os.path.join(os.path.dirname(__file__), "..", "data")
random.seed(20260604)

# --- build sibling groups once ---
print("building sibling map...", file=sys.stderr)
groups = collections.defaultdict(list)
for cp in range(0x20, 0x30000):
    ch = chr(cp)
    if unicodedata.category(ch) in ("Cc","Cn","Cs","Co"): continue
    m = model_norm(ch)
    if m: groups[m].append(ch)

# precompute per-char tables
ANY_SIB = {}    # ch -> list of model-equivalent siblings != ch
INVIS_SIB = {}  # ch -> list of siblings s with prod(s)!=prod(ch)  (production-invisible -> residual driver)
prodcache = {}
def pn1(ch):
    v = prodcache.get(ch)
    if v is None:
        v = prod_norm(ch); prodcache[ch]=v
    return v
for m, members in groups.items():
    if len(members) < 2: continue
    for ch in members:
        alts = [s for s in members if s != ch]
        if alts:
            ANY_SIB[ch] = alts
            pc = pn1(ch)
            inv = [s for s in alts if pn1(s) != pc]
            if inv: INVIS_SIB[ch] = inv
print(f"chars with any sibling: {len(ANY_SIB)}; chars with PRODUCTION-INVISIBLE sibling: {len(INVIS_SIB)}", file=sys.stderr)

CLASS_OF = {}
def cls(ch):
    c = CLASS_OF.get(ch)
    if c is None:
        c = classify_variant(ch, model_norm(ch)); CLASS_OF[ch]=c
    return c

MAXLEN = 20000  # cap pathological docs
def iter_docs(lang, maxd):
    path=os.path.join(DATA,f"c4_{lang}.jsonl")
    if not os.path.exists(path) or os.path.getsize(path)==0: return
    n=0
    with open(path) as f:
        for line in f:
            if n>=maxd: break
            t=json.loads(line)["text"]
            yield t[:MAXLEN]; n+=1

def run(langs, maxd):
    total_docs=0
    m1_pairs=m1_fn=0
    m3_prev=m3_pairs=m3_fn=0
    drive=collections.Counter(); seen=collections.Counter()
    per_lang={}
    for lang in langs:
        L=dict(docs=0,m1_pairs=0,m1_fn=0,m3_prev=0,m3_fn=0)
        for doc in iter_docs(lang, maxd):
            total_docs+=1; L["docs"]+=1
            chars=list(doc)
            # METRIC1: swap every variation char w/ random sibling
            sw=[]; ch1=chars[:]
            for i,c in enumerate(chars):
                a=ANY_SIB.get(c)
                if a:
                    nv=random.choice(a); ch1[i]=nv; sw.append((c,nv)); seen[cls(c)]+=1
            if sw:
                var="".join(ch1)
                if model_norm(doc)==model_norm(var):
                    m1_pairs+=1; L["m1_pairs"]+=1
                    if prod_norm(doc)!=prod_norm(var):
                        m1_fn+=1; L["m1_fn"]+=1
                        for oc,nc in sw:
                            if pn1(oc)!=pn1(nc): drive[cls(oc)]+=1
            # METRIC3: production-invisible-only variant (seam-specific)
            invpos=[(i,c) for i,c in enumerate(doc[:MAXLEN]) if c in INVIS_SIB]
            if invpos:
                m3_prev+=1; L["m3_prev"]+=1
                ch3=list(doc[:MAXLEN])
                for i,c in invpos: ch3[i]=random.choice(INVIS_SIB[c])
                var3="".join(ch3)
                if model_norm(doc[:MAXLEN])==model_norm(var3):
                    m3_pairs+=1
                    if prod_norm(doc[:MAXLEN])!=prod_norm(var3):
                        m3_fn+=1; L["m3_fn"]+=1
        L["m1_fn_rate"]=L["m1_fn"]/L["m1_pairs"] if L["m1_pairs"] else None
        L["m3_prevalence"]=L["m3_prev"]/L["docs"] if L["docs"] else None
        per_lang[lang]=L
    return dict(langs=langs, maxd=maxd, total_docs=total_docs,
        METRIC1_realistic_anyvariation=dict(pairs=m1_pairs, residual_fn=m1_fn,
            residual_fn_rate=(m1_fn/m1_pairs if m1_pairs else None)),
        METRIC3_seam_production_invisible=dict(docs_with_invisible_variation=m3_prev,
            prevalence_rate=(m3_prev/total_docs if total_docs else None),
            pairs=m3_pairs, residual_fn=m3_fn,
            residual_fn_rate=(m3_fn/m3_pairs if m3_pairs else None)),
        class_seen=dict(seen.most_common()), class_drivers=dict(drive.most_common()),
        per_lang=per_lang)

if __name__=="__main__":
    langs=sys.argv[1].split(","); maxd=int(sys.argv[2])
    print(json.dumps(run(langs,maxd),indent=2,ensure_ascii=False))

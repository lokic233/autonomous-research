"""DECISIVE L1 — residual_FN_rate on real C4-multilingual, honest multi-angle.

Definitions (anti-circular; GT = model_norm equality, never read by production):
  MODEL norm  = NFKC(casefold(x))      [GT equivalence standard]
  PROD norm   = datatrove simplify_text [tested signal]

We classify every model-equivalence CLASS by whether PRODUCTION also collapses it:
  A char c carries model-variation iff it has a real Unicode sibling s with model(c)==model(s), s!=c.
  That class is PRODUCTION-VISIBLE if prod(c)==prod(s) for the swap (deduper catches it).
  That class is PRODUCTION-INVISIBLE (a RESIDUAL driver) if prod(c)!=prod(s) (escapes deduper).

METRIC 1 (REALISTIC pair rate, the headline):
  For each real doc, form a model-identical variant by swapping EACH variation-carrying char for a
  random real sibling (this models the natural Unicode-variation a real near-dup pair would carry).
  GT-verify model(doc)==model(variant). residual_FN = pair escapes production (prod(doc)!=prod(variant)).
  residual_FN_rate = #escaping / #model-identical-pairs.   <-- but see METRIC 3 for the strict version.

METRIC 2 (per-class marginal): isolate ONE class at a time. For docs containing class-C chars, form a
  variant swapping ONLY class-C chars. Report residual_FN per class -> which classes drive the residual.

METRIC 3 (STRICT residual attributable to the SEAM, not to case/diacritic which prod already handles):
  The seam-specific residual = model-identical pairs whose variation is the NFKC-COMPATIBILITY part
  (fullwidth, ligature, compat-ideograph, enclosed, letterlike, presentation forms) that production's
  lowercase+NFD+strip-Mn does NOT collapse. We form variants using ONLY compat-class siblings that are
  production-invisible, and ask: of docs that CONTAIN such variation (prevalence), how often does the
  pair escape (should be ~100% by construction) AND what is the corpus-level prevalence (the real
  exposure rate = fraction of real docs that even carry production-uncatchable model-equivalence).

Headline reported = METRIC 3 corpus exposure (prevalence of production-escaping model-equiv variation)
AND METRIC 1 realistic rate, with per-class drivers (METRIC 2).
"""
import json, sys, os, unicodedata, random, collections
from normalizers import model_norm, prod_norm, prod_norm_textdedup, classify_variant
DATA = os.path.join(os.path.dirname(__file__), "..", "data")
random.seed(20260604)

def build_sibling_map():
    groups = collections.defaultdict(set)
    for cp in range(0x20, 0x30000):
        ch = chr(cp)
        if unicodedata.category(ch) in ("Cc","Cn","Cs","Co"): continue
        m = model_norm(ch)
        if m: groups[m].add(ch)
    sib={}
    for m,mem in groups.items():
        if len(mem)>=2: sib[m]=sorted(mem)
    return sib
print("building sibling map...",file=sys.stderr)
SIB = build_sibling_map()

# Precompute, per char, its production-INVISIBLE siblings (swap escapes prod) and VISIBLE siblings.
def siblings(ch):
    return SIB.get(model_norm(ch), [])

def invisible_siblings(ch):
    """siblings s where prod(ch)!=prod(s) -> swap escapes production (residual driver)."""
    out=[]
    pc=prod_norm(ch)
    for s in siblings(ch):
        if s==ch: continue
        if prod_norm(s)!=pc: out.append(s)
    return out

def any_sibling(ch):
    return [s for s in siblings(ch) if s!=ch]

def iter_docs(lang, maxd):
    path=os.path.join(DATA,f"c4_{lang}.jsonl")
    if not os.path.exists(path) or os.path.getsize(path)==0: return
    n=0
    with open(path) as f:
        for line in f:
            if n>=maxd: break
            yield json.loads(line)["text"]; n+=1

def run(langs, maxd):
    R={"langs":langs,"maxd":maxd}
    total_docs=0
    # METRIC1 realistic: swap all variation-carrying chars w/ random sibling
    m1_pairs=m1_fn=0
    # METRIC3 seam: doc carries production-INVISIBLE model-equiv variation
    m3_docs_with_invis=0  # prevalence
    m3_pairs=m3_fn=0
    # per-class driver counts (chars that drove an escape under METRIC1)
    drive=collections.Counter(); seen_class=collections.Counter()
    per_lang={}
    for lang in langs:
        l=dict(docs=0,m1_pairs=0,m1_fn=0,m3_prev=0)
        for doc in iter_docs(lang, maxd):
            total_docs+=1; l["docs"]+=1
            # ---- METRIC 1 realistic ----
            chars=list(doc); swapped=False; sw=[]
            for i,c in enumerate(chars):
                alts=any_sibling(c)
                if alts:
                    nv=random.choice(alts)
                    if nv!=c:
                        chars[i]=nv; swapped=True; sw.append((c,nv))
                        seen_class[classify_variant(c, model_norm(c))]+=1
            if swapped:
                var="".join(chars)
                if model_norm(doc)==model_norm(var):  # GT verify
                    m1_pairs+=1; l["m1_pairs"]+=1
                    if prod_norm(doc)!=prod_norm(var):
                        m1_fn+=1; l["m1_fn"]+=1
                        for oc,nc in sw:
                            if prod_norm(oc)!=prod_norm(nc):
                                drive[classify_variant(oc,model_norm(oc))]+=1
            # ---- METRIC 3 seam-specific (production-INVISIBLE classes only) ----
            inv_positions=[(i,c) for i,c in enumerate(doc) if invisible_siblings(c)]
            if inv_positions:
                m3_docs_with_invis+=1; l["m3_prev"]+=1
                ch3=list(doc)
                for i,c in inv_positions:
                    ch3[i]=random.choice(invisible_siblings(c))
                var3="".join(ch3)
                if model_norm(doc)==model_norm(var3):
                    m3_pairs+=1
                    if prod_norm(doc)!=prod_norm(var3):
                        m3_fn+=1
        l["m1_fn_rate"]=l["m1_fn"]/l["m1_pairs"] if l["m1_pairs"] else None
        l["m3_prevalence"]=l["m3_prev"]/l["docs"] if l["docs"] else None
        per_lang[lang]=l
    R.update(dict(
        total_docs=total_docs,
        METRIC1_realistic=dict(pairs=m1_pairs, residual_fn=m1_fn,
                               residual_fn_rate=(m1_fn/m1_pairs if m1_pairs else None)),
        METRIC3_seam=dict(docs_with_invisible_variation=m3_docs_with_invis,
                          prevalence_rate=(m3_docs_with_invis/total_docs if total_docs else None),
                          pairs=m3_pairs, residual_fn=m3_fn,
                          residual_fn_rate=(m3_fn/m3_pairs if m3_pairs else None)),
        class_seen=dict(seen_class.most_common()),
        class_drivers=dict(drive.most_common()),
        per_lang=per_lang,
    ))
    return R

if __name__=="__main__":
    langs=sys.argv[1].split(",") if len(sys.argv)>1 else ["ja","zh","ar","de","fr"]
    maxd=int(sys.argv[2]) if len(sys.argv)>2 else 4000
    out=run(langs,maxd)
    print(json.dumps(out,indent=2,ensure_ascii=False))

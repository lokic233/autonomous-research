"""DECISIVE L1 FINAL — residual_FN on real C4-multilingual. Two clean, injection-free metrics.

METRIC A (NFKC-twin, the canonical real-dup scenario):
  For each real doc d, its most natural MODEL-IDENTICAL twin is its NFKC+casefold-equivalent rendering.
  We take the twin = NFKC(d)  [the common, canonical Unicode rendering -- a DIFFERENT real site writing
  the same content in canonical form]. (We use NFKC not full model_norm for the twin so the twin is a
  realistic readable doc; both d and twin are then compared under the GT = model_norm equality, and the
  TESTED production normalizer.)
  - Only count docs where twin != d AND model(d)==model(twin)  [GT: genuinely model-identical pair].
  - residual_FN: prod(d) != prod(twin)  [production dedup fails to match the model-identical pair].
  residual_FN_rate_A = #escaping / #(model-identical d/twin pairs).
  pair_formable_rate = #(twin!=d & model-identical) / total docs  [prevalence of the scenario].

METRIC B (word-shingle / token representation robustness):
  Same pairs, but compare under (i) 5-gram char shingles set-equality of prod-normalized text and
  (ii) whitespace word tokens of prod-normalized text -> does the representation change whether the
  pair is caught? (production dedup uses shingles, not exact string equality.)

Anti-circular: GT = model_norm equality (harness). Production normalizer never reads GT. No injection.
"""
import json, sys, os, unicodedata, collections
from normalizers import model_norm, prod_norm, prod_norm_textdedup, classify_variant
DATA=os.path.join(os.path.dirname(__file__),"..","data")

def char_classes_causing_residual(d, twin):
    """which classes of char in d differ from twin under production -> drive the escape."""
    cl=collections.Counter()
    for c in d:
        mc=model_norm(c)
        if mc and mc!=c and prod_norm(c)!=prod_norm(mc):
            cl[fine_class(c)]+=1
    return cl

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
    s=s.replace(" ","")  # char shingles ignore ws after prod-norm collapses it; keep simple
    return set(s[i:i+k] for i in range(max(0,len(s)-k+1)))

def jacc(a,b):
    if not a and not b: return 1.0
    if not a or not b: return 0.0
    return len(a&b)/len(a|b)

MAXLEN=50000
def run(langs, maxd, T=0.8):
    total=0
    A_pairs=0; A_fn=0
    B_shingle_fn=0; B_word_fn=0
    class_drive=collections.Counter()
    per_lang={}
    for lang in langs:
        path=os.path.join(DATA,f"c4_{lang}.jsonl")
        if not os.path.exists(path) or os.path.getsize(path)==0: continue
        ld=lp=lfn=0; n=0
        with open(path) as f:
            for line in f:
                if n>=maxd: break
                n+=1; total+=1; ld+=1
                d=json.loads(line)["text"][:MAXLEN]
                twin=unicodedata.normalize("NFKC", d)
                if twin==d: continue
                if model_norm(d)!=model_norm(twin): continue  # GT verify model-identical
                A_pairs+=1; lp+=1
                pd,pt=prod_norm(d),prod_norm(twin)
                if pd!=pt:
                    A_fn+=1; lfn+=1
                    class_drive.update(char_classes_causing_residual(d,twin))
                    # B: shingle / word representation -- do they ALSO miss (Jaccard<T)?
                    if jacc(shingles(pd),shingles(pt))<T: B_shingle_fn+=1
                    if jacc(set(pd.split()),set(pt.split()))<T: B_word_fn+=1
        per_lang[lang]=dict(docs=ld, pairs=lp, residual_fn=lfn,
                            pair_formable_rate=(lp/ld if ld else None),
                            residual_fn_rate=(lfn/lp if lp else None))
    return dict(langs=langs, maxd=maxd, total_docs=total,
        METRIC_A_nfkc_twin=dict(model_identical_pairs=A_pairs, residual_fn=A_fn,
            residual_fn_rate=(A_fn/A_pairs if A_pairs else None),
            pair_formable_rate=(A_pairs/total if total else None)),
        METRIC_B_representation=dict(
            note="of the exact-string residual FNs, how many ALSO escape under shingle/word Jaccard<T",
            T=T, char_shingle_still_fn=B_shingle_fn, word_token_still_fn=B_word_fn,
            char_shingle_fn_rate_of_A=(B_shingle_fn/A_fn if A_fn else None),
            word_token_fn_rate_of_A=(B_word_fn/A_fn if A_fn else None)),
        class_drivers=dict(class_drive.most_common()),
        per_lang=per_lang)

if __name__=="__main__":
    langs=sys.argv[1].split(","); maxd=int(sys.argv[2])
    print(json.dumps(run(langs,maxd),indent=2,ensure_ascii=False))

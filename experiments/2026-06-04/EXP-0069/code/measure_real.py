"""HONEST REAL-EXPOSURE measurement.

The decisive realistic question for hidden duplicate exposure:
  In real multilingual web text, how often does a document CONTAIN characters whose
  MODEL normalization (NFKC+casefold) collapses them to a different codepoint, but where the
  PRODUCTION normalizer (datatrove simplify_text) does NOT collapse the same way?

  Such characters mean: a model-identical twin of this doc (the version with the plain/canonical
  codepoint, which is the COMMON web form) would NOT be matched by production dedup. That is the
  real residual exposure -- it requires NO injection; the variation is already present in the doc.

We measure, per real doc:
  R(d) = set of characters c in d such that model(c)!=prod-collapsed-form, i.e. c is a NON-canonical
         model-equivalent variant that production keeps distinct from its canonical sibling.
  Concretely: c is a residual-exposure char iff NFKC+casefold(c) != c (model changes it) AND there
  exists the canonical model-form char m=model(c) (a real, common codepoint) such that
  prod(c) != prod(m)  (production does NOT map c to m's production form).
  i.e. swapping c for its own canonical model-form m would be model-invisible but production-VISIBLE.

  This is exactly: "the doc as written would NOT dedup-match its own canonicalized (model-normalized)
  form" -- the most natural model-identical twin. residual exposure = doc contains >=1 such char.

ALSO: exclude pure-case and pure-NFD-diacritic, since production already handles those. We only count
chars where the model-form vs the char's production-form DIFFER (production genuinely can't collapse).
"""
import json, sys, os, unicodedata, collections
from normalizers import model_norm, prod_norm, classify_variant
DATA=os.path.join(os.path.dirname(__file__),"..","data")

# residual-exposure char table: c such that model(c) != c (model normalizes it away) AND
# prod(c) != prod(model(c))  -> production does NOT collapse c to its canonical model form.
print("building residual char table...",file=sys.stderr)
RESID=set(); RCLASS={}
for cp in range(0x20,0x30000):
    c=chr(cp)
    if unicodedata.category(c) in ("Cc","Cn","Cs","Co"): continue
    mc=model_norm(c)
    if mc and mc!=c:
        # canonical form chars = mc (may be multi-char). compare production forms.
        if prod_norm(c)!=prod_norm(mc):
            RESID.add(c); RCLASS[c]=classify_variant(c,mc)
print(f"residual-exposure chars: {len(RESID)}",file=sys.stderr)

def fine_class(c):
    cp=ord(c); n=unicodedata.name(c,"")
    if 0xFF01<=cp<=0xFF5E: return "fullwidth_ascii"
    if 0xFF61<=cp<=0xFFDC: return "halfwidth_kana_hangul"
    if 0xFFE0<=cp<=0xFFEE: return "fullwidth_sign"
    if "MATHEMATICAL" in n: return "math_alphanumeric"
    if "CIRCLED" in n or "PARENTHESIZED" in n or (0x2460<=cp<=0x24FF): return "enclosed_circled"
    if "SQUARE" in n or (0x3300<=cp<=0x33FF): return "cjk_squared"
    if "LIGATURE" in n: return "ligature"
    if "SUPERSCRIPT" in n or "SUBSCRIPT" in n or (0x1D43<=cp<=0x1DBF): return "super_subscript_modifier"
    if "PRESENTATION FORM" in n or 0xFB00<=cp<=0xFFFD: return "presentation_form"
    if "ROMAN NUMERAL" in n: return "roman_numeral"
    if 0xF900<=cp<=0xFAFF: return "cjk_compat_ideograph"
    if "VULGAR FRACTION" in n: return "fraction"
    if cp<0x80: return "ascii_dup_target"  # base ascii that has variants (not itself a variant target normally)
    return "other_compat"

MAXLEN=50000
def run(langs, maxd):
    total=0; exposed=0
    class_docfreq=collections.Counter()   # docs containing >=1 char of class
    class_charfreq=collections.Counter()  # total residual chars by class
    per_lang={}
    for lang in langs:
        path=os.path.join(DATA,f"c4_{lang}.jsonl")
        if not os.path.exists(path) or os.path.getsize(path)==0: continue
        ld=0; lex=0; n=0
        with open(path) as f:
            for line in f:
                if n>=maxd: break
                n+=1; total+=1; ld+=1
                doc=json.loads(line)["text"][:MAXLEN]
                hits=[c for c in doc if c in RESID]
                if hits:
                    exposed+=1; lex+=1
                    seen_classes=set()
                    for c in hits:
                        fc=fine_class(c); class_charfreq[fc]+=1; seen_classes.add(fc)
                    for fc in seen_classes: class_docfreq[fc]+=1
        per_lang[lang]=dict(docs=ld, exposed_docs=lex, exposure_rate=(lex/ld if ld else None))
    return dict(langs=langs, total_docs=total, exposed_docs=exposed,
        residual_exposure_rate=(exposed/total if total else None),
        class_docfreq=dict(class_docfreq.most_common()),
        class_charfreq=dict(class_charfreq.most_common()),
        per_lang=per_lang)

if __name__=="__main__":
    langs=sys.argv[1].split(","); maxd=int(sys.argv[2])
    print(json.dumps(run(langs,maxd),indent=2,ensure_ascii=False))

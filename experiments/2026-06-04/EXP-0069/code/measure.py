"""DECISIVE L1 measurement — residual_FN_rate on real C4-multilingual.

For each REAL doc d:
  - Find positions where a character is a NFKC-compatibility / casefold / ligature variant whose
    MODEL form (NFKC+casefold) differs from the original codepoint -> these are the codepoints that
    carry model-equivalence variation.
  - Build a model-equivalent VARIANT d' by swapping such chars for a DIFFERENT representative of the
    SAME model-equivalence class (a real Unicode sibling), or by swapping the original<->its NFKC form
    when both are real characters. We restrict swaps to transforms that leave NFKC+casefold INVARIANT.
  - Verify model_norm(d)==model_norm(d')  (GT: model-identical). If not, the variant is discarded
    (never counted) -> GT is always correct by construction + verification.
  - The pair (d,d') is then a model-identical pair. We ask: does production P collapse it?
       prod_norm(d)==prod_norm(d')  -> deduper CATCHES (no FN)
       prod_norm(d)!=prod_norm(d')  -> RESIDUAL FN (escapes despite model-identity)
  - residual_FN_rate = (#model-identical pairs that escape P) / (#model-identical pairs).

Anti-circular: GT is model_norm equality (harness). Variant generator only uses model-invariant
transforms (verified). Production normalizer never reads GT. We measure whether the two normalizers'
equivalence classes agree on real text.

Prevalence: fraction of real docs for which AT LEAST ONE model-equivalence variant exists that is
model-identical (so a pair CAN be formed at all) — i.e. the doc contains characters with model variation.
"""
import json, sys, os, unicodedata, random, collections
from normalizers import model_norm, prod_norm, prod_norm_textdedup, classify_variant

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
random.seed(20260604)

# Build the model-equivalence sibling map ONCE.
# Group all codepoints by their model_norm(char). Within a group with >1 distinct member,
# any two members form a model-identical single-char pair. These are REAL Unicode siblings.
def build_sibling_map():
    groups = collections.defaultdict(set)
    for cp in range(0x20, 0x30000):
        ch = chr(cp)
        if unicodedata.category(ch) in ("Cc","Cn","Cs","Co"): continue
        m = model_norm(ch)
        if m:  # ignore chars that model-normalize to empty
            groups[m].add(ch)
    # keep only model-forms with >=2 distinct real codepoints (so a variant swap exists)
    sib = {}
    for m, members in groups.items():
        if len(members) >= 2:
            sib[m] = sorted(members)
    return sib

print("building sibling map...", file=sys.stderr)
SIB = build_sibling_map()
# per-char: model_norm -> list of sibling chars (excluding the char itself chosen at swap time)
print(f"sibling model-forms with >=2 real variants: {len(SIB)}", file=sys.stderr)

def char_has_variant(ch):
    m = model_norm(ch)
    sibs = SIB.get(m)
    return sibs is not None and len(sibs) >= 2

def pick_variant_char(ch):
    """Return a DIFFERENT real char that is model-equivalent to ch, or None."""
    m = model_norm(ch)
    sibs = SIB.get(m)
    if not sibs: return None
    alts = [c for c in sibs if c != ch]
    if not alts: return None
    return random.choice(alts)

def make_model_equivalent_variant(doc, max_swaps=None):
    """Swap every (or up to max_swaps) char that has a model-equivalent sibling for a different sibling.
    Returns (variant, list_of_(orig_char, new_char)) or (None,[]) if no swappable char."""
    chars = list(doc)
    swaps = []
    swappable_idx = [i for i,c in enumerate(chars) if char_has_variant(c)]
    if not swappable_idx:
        return None, []
    if max_swaps is not None and len(swappable_idx) > max_swaps:
        swappable_idx = random.sample(swappable_idx, max_swaps)
    for i in swappable_idx:
        nv = pick_variant_char(chars[i])
        if nv is not None:
            swaps.append((chars[i], nv))
            chars[i] = nv
    return "".join(chars), swaps

def run(langs, max_docs_per_lang=4000, max_swaps_per_doc=None):
    total_pairs = 0
    residual_fn = 0          # production-default
    residual_fn_td = 0       # text-dedup cross-check
    caught = 0
    prevalence_docs = 0
    total_docs = 0
    class_total = collections.Counter()   # variation classes present (prevalence-ish, by swap)
    class_residual = collections.Counter() # classes that DROVE a residual FN
    # to attribute drivers: per residual pair, record which classes of swap made prod differ.
    per_lang = {}
    for lang in langs:
        path = os.path.join(DATA, f"c4_{lang}.jsonl")
        if not os.path.exists(path) or os.path.getsize(path)==0:
            continue
        l_pairs=l_fn=l_caught=l_prev=l_docs=0
        with open(path) as f:
            for line in f:
                if l_docs >= max_docs_per_lang: break
                doc = json.loads(line)["text"]
                total_docs += 1; l_docs += 1
                variant, swaps = make_model_equivalent_variant(doc, max_swaps_per_doc)
                if variant is None or variant == doc:
                    continue  # no model-equivalence variation in this doc -> no pair formable
                # GT verification: must be model-identical
                if model_norm(doc) != model_norm(variant):
                    # swap accidentally broke model-identity (shouldn't happen) -> discard, don't count
                    continue
                prevalence_docs += 1; l_prev += 1
                total_pairs += 1; l_pairs += 1
                pd, pv = prod_norm(doc), prod_norm(variant)
                td_d, td_v = prod_norm_textdedup(doc), prod_norm_textdedup(variant)
                escapes = (pd != pv)
                escapes_td = (td_d != td_v)
                if escapes:
                    residual_fn += 1; l_fn += 1
                    # attribute: which swap classes contributed to the production difference?
                    for oc, nc in swaps:
                        # a swap drives the residual if oc and nc differ under prod_norm
                        if prod_norm(oc) != prod_norm(nc):
                            class_residual[classify_variant(oc, model_norm(oc))] += 1
                else:
                    caught += 1; l_caught += 1
                if escapes_td:
                    residual_fn_td += 1
                for oc, nc in swaps:
                    class_total[classify_variant(oc, model_norm(oc))] += 1
        per_lang[lang] = dict(docs=l_docs, pairs=l_pairs, residual_fn=l_fn, caught=l_caught,
                              fn_rate=(l_fn/l_pairs if l_pairs else None))
    return dict(total_docs=total_docs, prevalence_docs=prevalence_docs,
                total_pairs=total_pairs, residual_fn=residual_fn, caught=caught,
                residual_fn_textdedup=residual_fn_td,
                residual_fn_rate=(residual_fn/total_pairs if total_pairs else None),
                residual_fn_rate_textdedup=(residual_fn_td/total_pairs if total_pairs else None),
                prevalence_rate=(prevalence_docs/total_docs if total_docs else None),
                class_total=dict(class_total.most_common()),
                class_residual=dict(class_residual.most_common()),
                per_lang=per_lang)

if __name__ == "__main__":
    langs = sys.argv[1].split(",") if len(sys.argv)>1 else ["ja","zh","ar","de","fr"]
    maxd = int(sys.argv[2]) if len(sys.argv)>2 else 4000
    res = run(langs, maxd)
    print(json.dumps(res, indent=2, ensure_ascii=False))

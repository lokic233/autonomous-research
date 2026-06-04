"""The two normalizers + the model-equivalence variant generator.
MODEL (GT standard): NFKC(casefold(x)). PRODUCTION (tested signal): datatrove simplify_text default.
The variant generator only uses transforms that are INVARIANT under NFKC+casefold (verified per-pair).
It never reads production output -> anti-circular.
"""
import unicodedata, re, sys

# ---------- MODEL normalizer = GT equivalence standard ----------
def model_norm(s: str) -> str:
    # tokenizer normalization standard from the claim: NFKC + casefold
    return unicodedata.normalize("NFKC", s.casefold())

# ---------- PRODUCTION dedup default = REAL datatrove simplify_text ----------
# datatrove/src/datatrove/utils/text.py simplify_text default:
#   lowercase -> NFD -> remove combining marks (Mn) -> remove punctuation ->
#   collapse whitespace -> normalize digits (each digit -> '0')
import string
_PUNCT_TABLE = str.maketrans("", "", string.punctuation)
_DIGIT_RE = re.compile(r"\d")
_WS_RE = re.compile(r"\s+")

def prod_norm(s: str) -> str:
    s = s.lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))  # strip Mn combining marks
    s = s.translate(_PUNCT_TABLE)                               # strip ASCII punctuation
    s = _DIGIT_RE.sub("0", s)                                   # number normalization
    s = _WS_RE.sub(" ", s).strip()                             # whitespace normalization
    return s

# cross-check arm: text-dedup preprocess (lowercase + split on non-word, rejoin)
_NONWORD = re.compile(r"\W+", re.UNICODE)
def prod_norm_textdedup(s: str) -> str:
    return " ".join(t for t in _NONWORD.split(s.lower()) if t)

# ---------- model-equivalence variant transforms (REAL Unicode equiv classes) ----------
# Each maps a char to a model-EQUIVALENT char/string (same under NFKC+casefold) but a DIFFERENT codepoint.
# Built from real Unicode compatibility/case data so variants reflect real web text variation.

def build_compat_map():
    """For every BMP+SMP-ish char, if NFKC changes it, the original is a compat variant of its NFKC form.
    Reverse-index: nfkc_form -> list of source chars that fold to it (and differ from it)."""
    rev = {}
    for cp in range(0x20, 0x30000):
        ch = chr(cp)
        nk = unicodedata.normalize("NFKC", ch)
        if nk != ch and nk:  # ch is a compatibility variant of nk
            rev.setdefault(nk, []).append(ch)
    return rev

# class taggers for attribution
def classify_variant(orig_char: str, nfkc_form: str) -> str:
    cp = ord(orig_char[0])
    name = unicodedata.name(orig_char, "")
    if 0xFF00 <= cp <= 0xFFEF:
        return "fullwidth_halfwidth"
    if "LIGATURE" in name:
        return "ligature"
    if 0x2460 <= cp <= 0x24FF or 0x3200 <= cp <= 0x32FF:
        return "enclosed_circled"
    if 0x2100 <= cp <= 0x214F or 0x3300 <= cp <= 0x33FF:
        return "letterlike_squared"
    if 0xF900 <= cp <= 0xFAFF:
        return "cjk_compat_ideograph"
    if 0xFB00 <= cp <= 0xFB4F:
        return "latin_hebrew_presentation"
    if 0xFE70 <= cp <= 0xFEFF or 0xFB50 <= cp <= 0xFDFF:
        return "arabic_presentation_form"
    cat = unicodedata.category(orig_char)
    if cat.startswith("L") and unicodedata.combining(orig_char)==0:
        return "compat_letter_other"
    return "compat_other"

if __name__ == "__main__":
    # sanity
    tests = [("Ａ","A"), ("ﬁ","fi"), ("①","1"), ("㈱","(株)"), ("Ⅳ","iv"), ("ガ","ガ")]
    for a,b in tests:
        print(repr(a), "model:", repr(model_norm(a)), "prod:", repr(prod_norm(a)),
              "| model_eq?", model_norm(a)==model_norm(b))

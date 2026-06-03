"""Real answer-equivalence canonicalizers for EXP-0051 Stage A.
GT = gold-anchored true equivalence. Canonicalizers read ONLY strings."""
import re
try:
    import sympy
    from sympy import Rational, simplify, sympify, nsimplify
    from sympy.parsing.latex import parse_latex
    HAVE_SYMPY=True
except Exception:
    HAVE_SYMPY=False

# -------- (i) EXACT MATCH (low recall) --------
def canon_exact(s):
    return s.strip()

# -------- (iii) LEXICAL normalizer (intermediate recall) --------
_units = ['dollars','dollar','cents','cent','%','percent','degrees','degree','units','unit']
def canon_lexical(s):
    t=s.strip().lower()
    t=t.replace('$','').replace(',','')
    for u in _units: t=t.replace(u,'')
    t=re.sub(r'\s+','',t)
    t=t.rstrip('.')
    # strip trailing .0 / .00
    if re.fullmatch(r'-?\d+\.0+', t): t=t.split('.')[0]
    return t

# -------- (ii) NUMERIC / Minerva-style (high recall) --------
def _strip_wrappers(s):
    t=s.strip()
    t=t.replace('\\$','').replace('$','')
    t=t.replace('\\!','').replace('\\,','').replace('\\;','')
    t=t.replace('\\left','').replace('\\right','')
    t=t.replace('\\%','').replace('%','')
    t=t.replace('^\\circ','').replace('^{\\circ}','').replace('\\circ','')
    t=re.sub(r'\\text\{([^}]*)\}', r'\1', t)
    for u in _units: t=t.replace(u,'')
    t=t.replace(',','')
    t=t.strip()
    # strip a leading/trailing pair of parens for tuples? keep tuples distinct.
    return t

def _to_value(s):
    """Return a sympy value (numeric/exact) for a single scalar answer string, or None if can't."""
    if not HAVE_SYMPY: 
        return None
    raw=s.strip()
    t=_strip_wrappers(raw)
    if t=='' : return None
    t=re.sub(r'\s+','',t)
    # normalize \dfrac/\tfrac -> \frac
    t=t.replace('\\dfrac','\\frac').replace('\\tfrac','\\frac')
    # \frac{a}{b}  (possibly leading minus)
    m=re.fullmatch(r'(-?)\\frac\{(-?\d+)\}\{(-?\d+)\}', t)
    if m:
        sign=-1 if m.group(1)=='-' else 1
        try: return Rational(int(m.group(2)),int(m.group(3)))*sign
        except: return None
    # k\sqrt{n}  and \sqrt{n}
    m=re.fullmatch(r'(-?\d*)\\sqrt\{(-?\d+)\}', t)
    if m:
        coef=m.group(1)
        coef=(-1 if coef=='-' else (1 if coef=='' else int(coef)))
        try: return simplify(coef*sympy.sqrt(int(m.group(2))))
        except: return None
    # \pi multiples
    if t in ('\\pi',): return sympy.pi
    m=re.fullmatch(r'(-?\d+)\\pi', t)
    if m:
        try: return Rational(int(m.group(1)))*sympy.pi
        except: return None
    # a/b plain fraction
    m=re.fullmatch(r'(-?\d+)/(-?\d+)', t)
    if m:
        try: return Rational(int(m.group(1)),int(m.group(2)))
        except: return None
    # plain int
    if re.fullmatch(r'-?\d+', t):
        return Rational(int(t))
    # decimal -> exact Rational (so 0.5 == 1/2, 18.0 == 18)
    if re.fullmatch(r'-?\d*\.\d+', t):
        try: return Rational(t)
        except: return None
    if re.fullmatch(r'-?\d+\.\d*', t):
        try: return Rational(t)
        except: return None
    # sqrt expressions, pi, general expr -> try sympify (no latex backslashes) then simplify
    if '\\' in t:
        return None  # unparseable latex (no antlr) -> fall to LEX, keeps recall honest
    try:
        v=simplify(sympify(t))
        return v
    except Exception:
        return None

def canon_numeric(s):
    """High-recall: map to canonical numeric/exact key. Falls back to lexical if unparseable
    (so it never has LOWER recall than lexical)."""
    v=_to_value(s)
    if v is None:
        return ('LEX', canon_lexical(s))
    try:
        # canonical string for the sympy value
        return ('NUM', str(simplify(v)))
    except Exception:
        return ('NUM', str(v))

"""EXP-0075 — Cross-backend constraint-enforcement divergence (Pydantic->vLLM/xgrammar).
Measures D (drop rate) and V (violation rate) for xgrammar's compiled grammar vs declared
JSON-Schema value constraints. Tokenizer-free via GrammarMatcher.accept_string."""
import xgrammar as xgr, json, jsonschema, collections, csv, sys, math, random
random.seed(42)

KW=["minimum","maximum","exclusiveMinimum","exclusiveMaximum","multipleOf","minLength","maxLength","pattern"]

def accepts(schema_str, candidate_str):
    g = xgr.Grammar.from_json_schema(schema_str)
    compiler = xgr.GrammarCompiler(xgr.TokenizerInfo([]))
    cg = compiler.compile_grammar(g)
    m = xgr.GrammarMatcher(cg)
    if not m.accept_string(candidate_str): return False
    return m.is_terminated() or m.is_completed()

def obj(prop):
    return json.dumps({"type":"object","properties":{"x":prop},"required":["x"],"additionalProperties":False})

# ============ ARM 1: PER-KEYWORD COVERAGE (controlled, deterministic) ============
# For each keyword, build a schema with that constraint and a VIOLATING instance.
# If the violating instance is ACCEPTED -> xgrammar DROPPED the keyword.
coverage_tests = {
 "minimum":         (obj({"type":"integer","minimum":10}),      '{"x": 5}'),
 "maximum":         (obj({"type":"integer","maximum":100}),     '{"x": 999}'),
 "exclusiveMinimum":(obj({"type":"integer","exclusiveMinimum":0}),'{"x": 0}'),
 "exclusiveMaximum":(obj({"type":"integer","exclusiveMaximum":10}),'{"x": 10}'),
 "multipleOf":      (obj({"type":"integer","multipleOf":5}),     '{"x": 7}'),
 "minLength":       (obj({"type":"string","minLength":5}),       '{"x": "hi"}'),
 "maxLength":       (obj({"type":"string","maxLength":3}),       '{"x": "abcdefg"}'),
 "pattern":         (obj({"type":"string","pattern":"^[a-z]+$"}),'{"x": "ABC"}'),
}
coverage = {}  # kw -> {"enforced":bool, "violating_accepted":bool}
print("=== ARM 1: per-keyword coverage (xgrammar) ===")
for kw,(sch,viol) in coverage_tests.items():
    try:
        acc = accepts(sch, viol)  # accepted => DROPPED
        coverage[kw] = {"violating_accepted":acc, "enforced": (not acc), "error":None}
    except Exception as e:
        coverage[kw] = {"violating_accepted":None,"enforced":None,"error":str(e)[:120]}
    print(f"  {kw:18s} violating_instance_accepted={coverage[kw]['violating_accepted']}  ENFORCED={coverage[kw]['enforced']}")

dropped_kws = [k for k,v in coverage.items() if v["enforced"] is False]
enforced_kws= [k for k,v in coverage.items() if v["enforced"] is True]
print(f"\n  ENFORCED ({len(enforced_kws)}): {enforced_kws}")
print(f"  DROPPED  ({len(dropped_kws)}): {dropped_kws}")

# ============ ARM 2: REAL-CORPUS D (drop rate over JSONSchemaBench) ============
# For each constraint-bearing schema, attempt to construct a minimal violating instance
# for ONE present constrained leaf, then test grammar acceptance.
schemas = json.load(open("/tmp/constraint_schemas.json"))
print(f"\n=== ARM 2: real-corpus D over {len(schemas)} constraint-bearing schemas ===")

def find_constrained_leaf(obj, path=None):
    """Yield (path, subschema, keyword, value) for leaves bearing a value constraint."""
    if path is None: path=[]
    if isinstance(obj, dict):
        for k in KW:
            if k in obj:
                yield (path, obj, k, obj[k])
        for k,v in obj.items():
            yield from find_constrained_leaf(v, path+[k])
    elif isinstance(obj, list):
        for i,x in enumerate(obj):
            yield from find_constrained_leaf(x, path+[i])

def violating_value(subschema, kw, val):
    """Return a value that VIOLATES the constraint kw=val for this subschema, or None."""
    t = subschema.get("type")
    if isinstance(t, list): t = next((x for x in t if x in ("integer","number","string")), None)
    import re
    if kw in ("minimum","maximum","exclusiveMinimum","exclusiveMaximum","multipleOf"):
        if not isinstance(val,(int,float)) or isinstance(val,bool): return None
    if kw=="minimum": return (val-1) if t in ("integer",None) else (val-1.0)
    if kw=="maximum": return (val+1) if t in ("integer",None) else (val+1.0)
    if kw=="exclusiveMinimum": return val  # equal violates exclusive
    if kw=="exclusiveMaximum": return val
    if kw=="multipleOf":
        if isinstance(val,int) and val>1: return val+1 if (val+1)%val!=0 else val+ (1 if val!=1 else 0)
        return None
    if kw in ("minLength","maxLength"):
        if not isinstance(val,int): return None
    if kw=="minLength": return "a"*(max(0,int(val)-1))
    if kw=="maxLength": return "a"*(int(val)+1)
    if kw=="pattern":
        if not isinstance(val,str): return None
        for cand in ["___VIOLATE___","!!!!","   ","ZZZZ0000"]:
            try:
                if not re.search(val, cand): return cand
            except re.error:
                return None
        return None
    return None

# Build a minimal instance for a schema given we set leaf at `path` to viol value.
# We only handle the common case: top-level object with a property carrying the constraint
# at properties.<name> (depth-1). For deeper/complex schemas we mark "uninstantiable".
def build_instance_for_simple(full, target_path, viol_val):
    # target_path like ['properties','age', ...]; require properties.<name> direct
    if full.get("type")!="object": return None
    if len(target_path)<2 or target_path[0]!="properties": return None
    pname = target_path[1]
    props = full.get("properties",{})
    if pname not in props: return None
    # Build instance: required props get a value; the target gets viol_val
    inst={}
    required = full.get("required",[])
    def default_for(ps):
        t=ps.get("type")
        if isinstance(t,list): t=t[0]
        if "enum" in ps: return ps["enum"][0]
        if "const" in ps: return ps["const"]
        if t=="string": 
            # respect pattern/minLength loosely with a safe-ish token if present elsewhere
            return "x"
        if t=="integer": 
            lo=ps.get("minimum", ps.get("exclusiveMinimum",0)); 
            return int(lo)+ (1 if "exclusiveMinimum" in ps else 0)
        if t=="number": return float(ps.get("minimum",1.0))
        if t=="boolean": return True
        if t=="array": return []
        if t=="object": return {}
        if t=="null": return None
        return "x"
    # only set the target property to keep instance minimal & avoid violating OTHER constraints
    targ = props[pname]
    # if target requires only the constrained leaf (target itself is the constrained schema):
    if len(target_path)==2:
        inst[pname]=viol_val
    else:
        return None  # nested deeper than direct property
    # add any OTHER required props with defaults (to satisfy structure)
    for r in required:
        if r==pname: continue
        if r in props:
            try: inst[r]=default_for(props[r])
            except Exception: return None
    return inst

results=[]  # per schema rows
D_eligible=0; D_dropped=0
viol_accepted_samples=[]  # (schema_idx, kw, instance) accepted-but-violating
for r in schemas:
    cfg=r["config"]; idx=r["idx"]; sch_str=r["schema"]; kws=r["kw"]
    try:
        full=json.loads(sch_str)
    except Exception:
        continue
    row={"config":cfg,"idx":idx,"keywords":";".join(kws.keys())}
    # try to find a constrained leaf we can instantiate at depth-1
    instantiated=False; dropped_here=False; tested_kw=None; viol_inst=None
    try:
      for (path, sub, kw, val) in find_constrained_leaf(full):
        vv = violating_value(sub, kw, val)
        if vv is None: continue
        inst = build_instance_for_simple(full, path, vv)
        if inst is None: continue
        inst_str=json.dumps(inst)
        try:
            acc = accepts(sch_str, inst_str)
        except Exception:
            continue
        instantiated=True; tested_kw=kw; viol_inst=inst_str
        if acc:
            dropped_here=True
            # confirm it really violates the original schema via jsonschema
            try:
                jsonschema.validate(inst, full)
                jsonschema_says_valid=True  # would be unexpected
            except jsonschema.ValidationError:
                jsonschema_says_valid=False
                viol_accepted_samples.append((cfg,idx,kw,inst_str))
            except Exception:
                jsonschema_says_valid=None
            row["jsonschema_valid_for_accepted"]=jsonschema_says_valid
        break
    except Exception:
        pass
    row["instantiated"]=instantiated
    row["tested_keyword"]=tested_kw
    row["dropped"]=dropped_here if instantiated else None
    row["viol_instance"]=viol_inst
    results.append(row)
    if instantiated:
        D_eligible+=1
        if dropped_here: D_dropped+=1

print(f"  instantiable schemas tested: {D_eligible} / {len(schemas)}")
D = (D_dropped / D_eligible) if D_eligible else float('nan')
print(f"  D (drop rate among instantiable constraint-bearing schemas) = {D_dropped}/{D_eligible} = {D:.4f}")

# Wilson 95% CI for D
def wilson(k,n,z=1.96):
    if n==0: return (float('nan'),float('nan'))
    p=k/n; d=1+z*z/n
    c=(p+z*z/(2*n))/d; h=(z*math.sqrt(p*(1-p)/n+z*z/(4*n*n)))/d
    return (max(0,c-h),min(1,c+h))
lo,hi=wilson(D_dropped,D_eligible)
print(f"  D 95% CI = [{lo:.4f}, {hi:.4f}]")

# ============ V (violation rate among grammar-ACCEPTED violating instances) ============
# Of the instances we constructed to violate AND that the grammar ACCEPTED, what fraction
# actually fail jsonschema (true violations). This is the V proxy on constructed instances.
V_acc = D_dropped  # number grammar-accepted (our constructed violating instances)
V_true_viol = len(viol_accepted_samples)
V = (V_true_viol/V_acc) if V_acc else float('nan')
print(f"  V (grammar-accepted instances that truly violate original schema) = {V_true_viol}/{V_acc} = {V if V_acc else float('nan')}")

# per-keyword drop breakdown over real corpus
kw_eligible=collections.Counter(); kw_dropped=collections.Counter()
for row in results:
    if row.get("instantiated") and row.get("tested_keyword"):
        kw_eligible[row["tested_keyword"]]+=1
        if row.get("dropped"): kw_dropped[row["tested_keyword"]]+=1
print("\n  per-keyword (real corpus, instantiable): keyword  dropped/eligible")
for k in KW:
    e=kw_eligible[k]; d=kw_dropped[k]
    if e: print(f"    {k:18s} {d}/{e} = {d/e:.3f}")

# save CSVs
import os
OUT="/Users/dengcchi/autonomous-research-v3/experiments/2026-06-04/EXP-0075"
with open(OUT+"/per_schema.csv","w",newline="") as f:
    w=csv.DictWriter(f, fieldnames=["config","idx","keywords","instantiated","tested_keyword","dropped","jsonschema_valid_for_accepted","viol_instance"])
    w.writeheader()
    for row in results:
        w.writerow({k:row.get(k,"") for k in w.fieldnames})
with open(OUT+"/coverage.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["keyword","violating_accepted","enforced","error"])
    for k in KW:
        c=coverage.get(k,{}); w.writerow([k,c.get("violating_accepted"),c.get("enforced"),c.get("error")])

summary={
 "xgrammar_coverage":coverage,
 "enforced_kws":enforced_kws,"dropped_kws":dropped_kws,
 "D_dropped":D_dropped,"D_eligible":D_eligible,"D":D,"D_ci":[lo,hi],
 "V_accepted":V_acc,"V_true_viol":V_true_viol,"V":V,
 "kw_eligible":dict(kw_eligible),"kw_dropped":dict(kw_dropped),
 "N_constraint_schemas":len(schemas),
}
json.dump(summary, open(OUT+"/summary.json","w"), indent=2)
print("\n  saved per_schema.csv, coverage.csv, summary.json")

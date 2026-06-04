"""ARM 2b (robust): harvest REAL constrained leaf-subschemas from JSONSchemaBench, wrap each as a
minimal standalone object schema, generate a violating instance using the REAL corpus constraint
value, compile xgrammar grammar, and test acceptance. Avoids segfault-prone full-schema compiles
and always-instantiable. Isolated per-leaf in a forked worker (timeout) for crash-safety."""
import json, jsonschema, collections, csv, math, multiprocessing as mp, re, random
random.seed(42)
KW=["minimum","maximum","exclusiveMinimum","exclusiveMaximum","multipleOf","minLength","maxLength","pattern"]
SIMPLE_TYPES={"integer","number","string"}

def _worker(sch_str, inst_str, q):
    try:
        import xgrammar as xgr
        g=xgr.Grammar.from_json_schema(sch_str)
        cg=xgr.GrammarCompiler(xgr.TokenizerInfo([])).compile_grammar(g)
        m=xgr.GrammarMatcher(cg)
        ok=m.accept_string(inst_str)
        q.put(("ok", bool(ok) and (m.is_terminated() or m.is_completed())))
    except Exception as e:
        q.put(("err", str(e)[:100]))

def accepts_isolated(sch_str, inst_str, timeout=4):
    ctx=mp.get_context("fork"); q=ctx.Queue()
    p=ctx.Process(target=_worker,args=(sch_str,inst_str,q)); p.start(); p.join(timeout)
    if p.is_alive(): p.terminate(); p.join(); return ("timeout",None)
    if p.exitcode not in (0,None): return ("crash",None)
    try: return q.get_nowait()
    except Exception: return ("crash",None)

def leaf_type(sub):
    t=sub.get("type")
    if isinstance(t,list): t=next((x for x in t if x in SIMPLE_TYPES),None)
    if not isinstance(t,str): return None
    return t

def harvest(obj, acc):
    """Collect simple-typed subschemas that carry >=1 value constraint keyword."""
    if isinstance(obj,dict):
        if leaf_type(obj) in SIMPLE_TYPES and any(k in obj for k in KW):
            # keep only the type + the constraint keywords (clean standalone leaf)
            clean={"type":leaf_type(obj)}
            for k in KW:
                if k in obj: clean[k]=obj[k]
            acc.append(clean)
        for v in obj.values(): harvest(v, acc)
    elif isinstance(obj,list):
        for x in obj: harvest(x, acc)

def violating_value(sub, kw, val):
    t=sub.get("type")
    if kw in ("minimum","maximum","exclusiveMinimum","exclusiveMaximum","multipleOf"):
        if not isinstance(val,(int,float)) or isinstance(val,bool): return None
    if kw=="minimum": return (val-1) if t=="integer" else (val-1.0)
    if kw=="maximum": return (val+1) if t=="integer" else (val+1.0)
    if kw=="exclusiveMinimum": return val
    if kw=="exclusiveMaximum": return val
    if kw=="multipleOf":
        if isinstance(val,int) and val>1: return val+1
        if isinstance(val,(int,float)) and val>0: return val/2.0 if (val/2.0)%val!=0 else None
        return None
    if kw in ("minLength","maxLength") and not isinstance(val,int): return None
    if kw=="minLength": return "a"*max(0,int(val)-1)
    if kw=="maxLength": return "a"*(int(val)+1)
    if kw=="pattern":
        if not isinstance(val,str): return None
        for c in ["___VIOLATE___","!!!!","   ","ZZZZ9999","\u0000bad"]:
            try:
                if not re.search(val,c): return c
            except re.error: return None
        return None
    return None

def wilson(k,n,z=1.96):
    if n==0: return (float('nan'),float('nan'))
    p=k/n; d=1+z*z/n
    c=(p+z*z/(2*n))/d; h=(z*math.sqrt(p*(1-p)/n+z*z/(4*n*n)))/d
    return (max(0,c-h),min(1,c+h))

if __name__=="__main__":
    import sys
    schemas=json.load(open("/tmp/constraint_schemas.json"))
    leaves=[]
    for r in schemas:
        try: full=json.loads(r["schema"])
        except: continue
        harvest(full, leaves)
    # dedup identical leaves
    seen=set(); uniq=[]
    for l in leaves:
        key=json.dumps(l,sort_keys=True)
        if key not in seen: seen.add(key); uniq.append(l)
    print(f"harvested {len(leaves)} constrained leaf-subschemas ({len(uniq)} unique) from {len(schemas)} schemas", flush=True)
    N=int(sys.argv[1]) if len(sys.argv)>1 else 600
    pool = uniq if len(uniq)<=N else random.sample(uniq,N)
    print(f"testing {len(pool)} unique constrained leaves", flush=True)

    OUT="/Users/dengcchi/autonomous-research-v3/experiments/2026-06-04/EXP-0075"
    # per (leaf, keyword) test: build object wrapper, violating instance, test acceptance
    kw_elig=collections.Counter(); kw_drop=collections.Counter()
    rows=[]; crashes=0; timeouts=0; viol_accepted=0; viol_total=0
    for li,leaf in enumerate(pool):
        present=[k for k in KW if k in leaf]
        for kw in present:
            vv=violating_value(leaf, kw, leaf[kw])
            if vv is None: continue
            wrap={"type":"object","properties":{"x":leaf},"required":["x"],"additionalProperties":False}
            inst={"x":vv}; inst_str=json.dumps(inst); sch_str=json.dumps(wrap)
            status,acc=accepts_isolated(sch_str,inst_str)
            if status=="crash": crashes+=1; continue
            if status=="timeout": timeouts+=1; continue
            if status=="err": continue
            kw_elig[kw]+=1
            dropped = bool(acc)
            jvalid=None
            if dropped:
                kw_drop[kw]+=1
                viol_total+=1
                try: jsonschema.validate(inst, wrap); jvalid=True
                except jsonschema.ValidationError: jvalid=False; viol_accepted+=1
                except Exception: jvalid=None
            rows.append({"leaf_idx":li,"type":leaf.get("type"),"keyword":kw,
                         "constraint_val":json.dumps(leaf[kw]),"viol_value":json.dumps(vv),
                         "grammar_accepted":dropped,"jsonschema_violates":(None if not dropped else (jvalid is False))})
        if (li+1)%100==0:
            tot_e=sum(kw_elig.values()); tot_d=sum(kw_drop.values())
            print(f"  ...{li+1}/{len(pool)} leaves | tests={tot_e} dropped={tot_d} crashes={crashes} timeouts={timeouts}", flush=True)

    # D over (leaf,keyword) tests; also per-schema-equivalent D = fraction of leaves with >=1 dropped kw
    tot_e=sum(kw_elig.values()); tot_d=sum(kw_drop.values())
    D=tot_d/tot_e if tot_e else float('nan'); lo,hi=wilson(tot_d,tot_e)
    V = viol_accepted/viol_total if viol_total else float('nan')
    print(f"\n=== ARM 2b RESULTS (real corpus constraint VALUES, standalone leaves) ===")
    print(f"leaf-constraint tests: {tot_e} | crashes:{crashes} timeouts:{timeouts}")
    print(f"D (per-constraint drop rate) = {tot_d}/{tot_e} = {D:.4f}  95%CI [{lo:.4f},{hi:.4f}]")
    print(f"V (grammar-accepted that truly violate jsonschema) = {viol_accepted}/{viol_total} = {V}")
    print("per-keyword (real values): kw  dropped/tested  rate")
    for k in KW:
        e=kw_elig[k]
        if e: print(f"  {k:18s} {kw_drop[k]}/{e} = {kw_drop[k]/e:.3f}")
    with open(OUT+"/per_leaf_arm2b.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); [w.writerow(r) for r in rows]
    json.dump({"tests":tot_e,"dropped":tot_d,"D":D,"D_ci":[lo,hi],"V_acc":viol_accepted,"V_total":viol_total,"V":V,
               "crashes":crashes,"timeouts":timeouts,"kw_elig":dict(kw_elig),"kw_drop":dict(kw_drop),
               "n_leaves_tested":len(pool),"n_leaves_harvested":len(leaves),"n_unique":len(uniq)},
              open(OUT+"/arm2b_summary.json","w"),indent=2)
    print("saved per_leaf_arm2b.csv, arm2b_summary.json")

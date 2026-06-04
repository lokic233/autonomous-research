"""ARM 2 (crash-resilient): real-corpus D over JSONSchemaBench.
Each schema's grammar compile+accept runs in a FORKED worker with a timeout, so a
segfault/hang in xgrammar on a pathological schema kills only that child (recorded as 'crash')."""
import json, jsonschema, collections, csv, math, multiprocessing as mp, re

KW=["minimum","maximum","exclusiveMinimum","exclusiveMaximum","multipleOf","minLength","maxLength","pattern"]

def _worker(sch_str, inst_str, q):
    try:
        import xgrammar as xgr
        g = xgr.Grammar.from_json_schema(sch_str)
        cg = xgr.GrammarCompiler(xgr.TokenizerInfo([])).compile_grammar(g)
        m = xgr.GrammarMatcher(cg)
        ok = m.accept_string(inst_str)
        res = bool(ok) and (m.is_terminated() or m.is_completed())
        q.put(("ok", res))
    except Exception as e:
        q.put(("err", str(e)[:120]))

def accepts_isolated(sch_str, inst_str, timeout=3):
    ctx = mp.get_context("fork")
    q = ctx.Queue()
    p = ctx.Process(target=_worker, args=(sch_str, inst_str, q))
    p.start(); p.join(timeout)
    if p.is_alive():
        p.terminate(); p.join()
        return ("timeout", None)
    if p.exitcode is not None and p.exitcode != 0:
        return ("crash", None)
    try:
        return q.get_nowait()
    except Exception:
        return ("crash", None)

def find_constrained_leaf(obj, path=None):
    if path is None: path=[]
    if isinstance(obj, dict):
        for k in KW:
            if k in obj: yield (path, obj, k, obj[k])
        for k,v in obj.items():
            yield from find_constrained_leaf(v, path+[k])
    elif isinstance(obj, list):
        for i,x in enumerate(obj):
            yield from find_constrained_leaf(x, path+[i])

def violating_value(subschema, kw, val):
    t = subschema.get("type")
    if isinstance(t, list): t = next((x for x in t if x in ("integer","number","string")), None)
    if kw in ("minimum","maximum","exclusiveMinimum","exclusiveMaximum","multipleOf"):
        if not isinstance(val,(int,float)) or isinstance(val,bool): return None
    if kw=="minimum": return (val-1) if t in ("integer",None) else (val-1.0)
    if kw=="maximum": return (val+1) if t in ("integer",None) else (val+1.0)
    if kw=="exclusiveMinimum": return val
    if kw=="exclusiveMaximum": return val
    if kw=="multipleOf":
        if isinstance(val,int) and val>1: return val+1
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
            except re.error: return None
        return None
    return None

def build_instance_for_simple(full, target_path, viol_val):
    if full.get("type")!="object": return None
    if len(target_path)<2 or target_path[0]!="properties": return None
    pname = target_path[1]
    props = full.get("properties",{})
    if pname not in props: return None
    if len(target_path)!=2: return None
    inst={pname: viol_val}
    required = full.get("required",[])
    def default_for(ps):
        t=ps.get("type")
        if isinstance(t,list): t=t[0]
        if "enum" in ps: return ps["enum"][0]
        if "const" in ps: return ps["const"]
        if t=="string": return "x"
        if t=="integer": return int(ps.get("minimum", ps.get("exclusiveMinimum",0)))+(1 if "exclusiveMinimum" in ps else 0)
        if t=="number": return float(ps.get("minimum",1.0))
        if t=="boolean": return True
        if t=="array": return []
        if t=="object": return {}
        if t=="null": return None
        return "x"
    for r in required:
        if r==pname: continue
        if r in props:
            try: inst[r]=default_for(props[r])
            except Exception: return None
    return inst

def wilson(k,n,z=1.96):
    if n==0: return (float('nan'),float('nan'))
    p=k/n; d=1+z*z/n
    c=(p+z*z/(2*n))/d; h=(z*math.sqrt(p*(1-p)/n+z*z/(4*n*n)))/d
    return (max(0,c-h),min(1,c+h))

if __name__=="__main__":
    schemas = json.load(open("/tmp/constraint_schemas.json"))
    import random, sys
    random.seed(42)
    N_SAMPLE = int(sys.argv[1]) if len(sys.argv)>1 else 400
    if len(schemas) > N_SAMPLE:
        schemas = random.sample(schemas, N_SAMPLE)
    print(f"sampled {len(schemas)} constraint-bearing schemas (seed=42)", flush=True)
    OUT="/Users/dengcchi/autonomous-research-v3/experiments/2026-06-04/EXP-0075"
    results=[]; D_eligible=0; D_dropped=0; crashes=0; timeouts=0
    viol_accepted=[]
    kw_eligible=collections.Counter(); kw_dropped=collections.Counter()
    for n,r in enumerate(schemas):
        cfg=r["config"]; idx=r["idx"]; sch_str=r["schema"]
        try: full=json.loads(sch_str)
        except Exception: continue
        row={"config":cfg,"idx":idx,"keywords":";".join(r["kw"].keys()),
             "instantiated":False,"tested_keyword":None,"dropped":None,
             "jsonschema_valid_for_accepted":None,"status":None,"viol_instance":None}
        try:
            for (path, sub, kw, val) in find_constrained_leaf(full):
                vv = violating_value(sub, kw, val)
                if vv is None: continue
                inst = build_instance_for_simple(full, path, vv)
                if inst is None: continue
                inst_str=json.dumps(inst)
                status, acc = accepts_isolated(sch_str, inst_str)
                row["status"]=status
                if status=="crash": crashes+=1; break
                if status=="timeout": timeouts+=1; break
                if status=="err": break
                row["instantiated"]=True; row["tested_keyword"]=kw; row["viol_instance"]=inst_str
                D_eligible+=1; kw_eligible[kw]+=1
                if acc:
                    row["dropped"]=True; D_dropped+=1; kw_dropped[kw]+=1
                    try:
                        jsonschema.validate(inst, full); row["jsonschema_valid_for_accepted"]=True
                    except jsonschema.ValidationError:
                        row["jsonschema_valid_for_accepted"]=False; viol_accepted.append((cfg,idx,kw,inst_str))
                    except Exception:
                        row["jsonschema_valid_for_accepted"]=None
                else:
                    row["dropped"]=False
                break
        except Exception as e:
            row["status"]="pyerr:"+str(e)[:60]
        results.append(row)
        if (n+1)%50==0:
            print(f"  ...{n+1}/{len(schemas)} processed | eligible={D_eligible} dropped={D_dropped} crashes={crashes} timeouts={timeouts}", flush=True)

    D = (D_dropped/D_eligible) if D_eligible else float('nan')
    lo,hi = wilson(D_dropped, D_eligible)
    V_acc=D_dropped; V_true=len(viol_accepted); V=(V_true/V_acc) if V_acc else float('nan')
    print(f"\n=== ARM2 REAL-CORPUS RESULTS ===")
    print(f"N constraint-bearing schemas: {len(schemas)}")
    print(f"instantiable (depth-1) tested: {D_eligible}")
    print(f"crashes(xgrammar segfault): {crashes} | timeouts: {timeouts}")
    print(f"D (drop rate) = {D_dropped}/{D_eligible} = {D:.4f}  95%CI [{lo:.4f},{hi:.4f}]")
    print(f"V (accepted-and-truly-violating / accepted) = {V_true}/{V_acc} = {V}")
    print("per-keyword drop (real corpus): kw  dropped/eligible")
    for k in KW:
        e=kw_eligible[k]
        if e: print(f"  {k:18s} {kw_dropped[k]}/{e} = {kw_dropped[k]/e:.3f}")

    with open(OUT+"/per_schema_arm2.csv","w",newline="") as f:
        w=csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader(); [w.writerow(row) for row in results]
    json.dump({"N":len(schemas),"D_eligible":D_eligible,"D_dropped":D_dropped,"D":D,"D_ci":[lo,hi],
               "crashes":crashes,"timeouts":timeouts,"V_acc":V_acc,"V_true":V_true,"V":V,
               "kw_eligible":dict(kw_eligible),"kw_dropped":dict(kw_dropped)},
              open(OUT+"/arm2_summary.json","w"), indent=2)
    print("saved per_schema_arm2.csv, arm2_summary.json")

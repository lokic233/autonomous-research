import json, jsonschema, collections, csv, math, re, random, sys
random.seed(42)
import xgrammar as xgr
KW=["minimum","maximum","exclusiveMinimum","exclusiveMaximum","multipleOf","minLength","maxLength","pattern"]
ST={"integer","number","string"}
def accepts(sch_str, inst_str):
    g=xgr.Grammar.from_json_schema(sch_str)
    cg=xgr.GrammarCompiler(xgr.TokenizerInfo([])).compile_grammar(g)
    m=xgr.GrammarMatcher(cg)
    if not m.accept_string(inst_str): return False
    return m.is_terminated() or m.is_completed()
def lt(sub):
    t=sub.get("type")
    if isinstance(t,list): t=next((x for x in t if x in ST),None)
    return t if isinstance(t,str) else None
def harvest(o,acc):
    if isinstance(o,dict):
        if lt(o) in ST and any(k in o for k in KW):
            c={"type":lt(o)}
            for k in KW:
                if k in o: c[k]=o[k]
            acc.append(c)
        for v in o.values(): harvest(v,acc)
    elif isinstance(o,list):
        for x in o: harvest(x,acc)
def vv(sub,kw,val):
    t=sub.get("type")
    if kw in("minimum","maximum","exclusiveMinimum","exclusiveMaximum","multipleOf") and (not isinstance(val,(int,float)) or isinstance(val,bool)): return None
    if kw=="minimum": return (val-1) if t=="integer" else val-1.0
    if kw=="maximum": return (val+1) if t=="integer" else val+1.0
    if kw=="exclusiveMinimum": return val
    if kw=="exclusiveMaximum": return val
    if kw=="multipleOf": return (val+1) if isinstance(val,int) and val>1 else None
    if kw in("minLength","maxLength") and not isinstance(val,int): return None
    if kw=="minLength": return "a"*max(0,int(val)-1)
    if kw=="maxLength": return "a"*(int(val)+1)
    if kw=="pattern":
        if not isinstance(val,str): return None
        for c in ["___VIOLATE___","!!!!","   ","ZZZZ9999"]:
            try:
                if not re.search(val,c): return c
            except re.error: return None
    return None
def wilson(k,n,z=1.96):
    if n==0: return (float('nan'),)*2
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return (max(0,c-h),min(1,c+h))
schemas=json.load(open("/tmp/constraint_schemas.json"))
leaves=[]
for r in schemas:
    try: harvest(json.loads(r["schema"]),leaves)
    except: pass
seen=set(); uniq=[]
for l in leaves:
    k=json.dumps(l,sort_keys=True)
    if k not in seen: seen.add(k); uniq.append(l)
N=int(sys.argv[1]) if len(sys.argv)>1 else 800
pool=uniq if len(uniq)<=N else random.sample(uniq,N)
print(f"harvested {len(leaves)} leaves ({len(uniq)} unique); testing {len(pool)}",flush=True)
OUT="/Users/dengcchi/autonomous-research-v3/experiments/2026-06-04/EXP-0075"
ke=collections.Counter(); kd=collections.Counter(); rows=[]; errs=0; vacc=0; vtot=0
for li,leaf in enumerate(pool):
    for kw in [k for k in KW if k in leaf]:
        v=vv(leaf,kw,leaf[kw])
        if v is None: continue
        wrap={"type":"object","properties":{"x":leaf},"required":["x"],"additionalProperties":False}
        inst={"x":v}
        try: acc=accepts(json.dumps(wrap),json.dumps(inst))
        except Exception: errs+=1; continue
        ke[kw]+=1; dropped=bool(acc)
        jv=None
        if dropped:
            kd[kw]+=1; vtot+=1
            try: jsonschema.validate(inst,wrap); jv=True
            except jsonschema.ValidationError: jv=False; vacc+=1
            except Exception: jv=None
        rows.append({"type":leaf.get("type"),"keyword":kw,"constraint":json.dumps(leaf[kw]),
                     "viol":json.dumps(v),"grammar_accepted":dropped,"truly_violates":(jv is False) if dropped else None})
    if (li+1)%200==0: print(f"  {li+1}/{len(pool)} | tests={sum(ke.values())} dropped={sum(kd.values())} errs={errs}",flush=True)
te=sum(ke.values()); td=sum(kd.values()); D=td/te if te else float('nan'); lo,hi=wilson(td,te)
V=vacc/vtot if vtot else float('nan')
print(f"\n=== ARM2c RESULTS (standalone real-value leaves, no fork) ===")
print(f"tests={te} errs={errs}")
print(f"D = {td}/{te} = {D:.4f}  95%CI [{lo:.4f},{hi:.4f}]")
print(f"V = {vacc}/{vtot} = {V}")
print("per-keyword: kw dropped/tested rate")
for k in KW:
    if ke[k]: print(f"  {k:18s} {kd[k]}/{ke[k]} = {kd[k]/ke[k]:.3f}")
with open(OUT+"/per_leaf_arm2c.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); [w.writerow(r) for r in rows]
json.dump({"tests":te,"dropped":td,"D":D,"D_ci":[lo,hi],"V_acc":vacc,"V_tot":vtot,"V":V,"errs":errs,
           "kw_elig":dict(ke),"kw_drop":dict(kd),"n_unique_leaves":len(uniq),"n_tested":len(pool)},
          open(OUT+"/arm2c_summary.json","w"),indent=2)
print("saved per_leaf_arm2c.csv, arm2c_summary.json")

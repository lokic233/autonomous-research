import json, sys
probes = json.load(open("probes.json"))

# Python negative control: the OpenAI/Pydantic-style path.
# json.loads default: integers -> Python int (arbitrary precision). This is the runtime difference.
def run_jsonloads():
    above_tot=above_surv=0; below_tot=below_surv=0
    rows=[]
    for band, source, valstr in probes:
        text = f'{{"id":{valstr},"ts":{valstr}}}'
        obj = json.loads(text)             # default parse_int=int -> exact
        survived = (str(obj["id"]) == valstr)
        rows.append((band,source,valstr,str(obj["id"]),1 if survived else 0))
        if band=="above":
            above_tot+=1; above_surv+= 1 if survived else 0
        else:
            below_tot+=1; below_surv+= 1 if survived else 0
    return above_surv/above_tot, below_surv/below_tot, rows

s_above, s_below, rows = run_jsonloads()
print(json.dumps({"path":"json.loads(parse_int=int)","survival_above":s_above,"survival_below":s_below}))

# write CSV
with open("results_python_jsonloads.csv","w") as f:
    f.write("band,source,original,parsed,survived\n")
    for r in rows:
        f.write(",".join(map(str,r))+"\n")

# Pydantic leg (if available)
try:
    from pydantic import BaseModel
    import pydantic
    class M(BaseModel):
        id:int
        ts:int
    above_tot=above_surv=0; below_tot=below_surv=0; pass_above=0
    for band, source, valstr in probes:
        text = f'{{"id":{valstr},"ts":{valstr}}}'
        m = M.model_validate_json(text)    # pydantic parses JSON itself
        survived = (str(m.id)==valstr)
        if band=="above":
            above_tot+=1; above_surv+= 1 if survived else 0; pass_above+=1
        else:
            below_tot+=1; below_surv+= 1 if survived else 0
    print(json.dumps({"path":f"pydantic-{pydantic.VERSION}","survival_above":above_surv/above_tot,"survival_below":below_surv/below_tot}))
except ImportError:
    print(json.dumps({"path":"pydantic","status":"not_installed"}))

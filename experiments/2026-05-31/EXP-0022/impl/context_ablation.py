
import json, glob, os, re, random, math
from collections import defaultdict, Counter
import importlib.util
spec = importlib.util.spec_from_file_location("tl", "/Users/dengcchi/autonomous-research/experiments/2026-05-31/EXP-0022/impl/two_layer_decomposition.py")
tl = importlib.util.module_from_spec(spec)
# we only want the helper functions, not main(); guard already on __main__
spec.loader.exec_module(tl)

ROOT = os.path.expanduser("~/.claude/projects")
random.seed(20260531)
files=sorted(glob.glob(os.path.join(ROOT,"**","*.jsonl"),recursive=True))
rows=[]
for path in files:
    calls=tl.parse_session(path)
    if len(calls)<2: continue
    for i,c in enumerate(calls):
        if not c["is_error"]: continue
        cls=tl.classify_error(c["name"],c["cmd"],c["text"]); gt=tl.gate_type(cls)
        nxt=calls[i+1] if i+1<len(calls) else None
        nt=tl.routing_tool(nxt) if nxt is not None else "(END)"
        prior=tl.routing_tool(calls[i-1]) if i>0 else "(START)"
        ft=tl.routing_tool(c)
        rows.append({"cls":cls,"gate":gt,"next":nt,"prior":prior,"feats":tl.text_features(c["text"]),"failed_tool":ft})

def run_ctx(grp, feat_keys):
    labels=[r["next"] for r in grp]; toolset=set(labels); n=len(grp)
    def featset(r):
        fs=set()
        if "kw" in feat_keys: fs |= set(r["feats"])
        if "prior" in feat_keys: fs.add("prior:"+r["prior"])
        if "cls" in feat_keys: fs.add("cls:"+r["cls"])
        if "ft" in feat_keys: fs.add("ft:"+r["failed_tool"])
        return fs
    tool_count=Counter(labels); feat_tool=defaultdict(Counter)
    for r in grp:
        for f in featset(r): feat_tool[f][r["next"]]+=1
    cnt=Counter(labels); base=0; ctx=0
    for r in grp:
        c2=Counter(cnt); c2[r["next"]]-=1; base += (c2.most_common(1)[0][0]==r["next"])
        tc=Counter(tool_count); tc[r["next"]]-=1; rf=featset(r)
        best=None; bs=-1e9
        for tool in toolset:
            if tc[tool]<=0: continue
            score=math.log(tc[tool])
            for f in rf:
                num=feat_tool[f][tool]-(1 if r["next"]==tool else 0)
                score+=math.log((num+1)/(tc[tool]+len(toolset)))
            if score>bs: bs=score; best=tool
        ctx += (best==r["next"])
    return base/n, ctx/n

for g in ["REDIRECTABLE","GRANT_REQUIRED","TRANSIENT"]:
    grp=[r for r in rows if r["gate"]==g]
    b,_=run_ctx(grp,set())
    _,full=run_ctx(grp,{"kw","prior","cls","ft"})
    _,noft=run_ctx(grp,{"kw","prior","cls"})       # drop failed_tool (the same-tool-retry leak)
    _,kwcls=run_ctx(grp,{"kw","cls"})              # only genuine situation: error text + class
    _,clsonly=run_ctx(grp,{"cls"})
    print(f"{g:15s} n={len(grp):4d} base={b:.3f} | full={full:.3f}  no_failed_tool={noft:.3f}  kw+cls={kwcls:.3f}  cls_only={clsonly:.3f}")

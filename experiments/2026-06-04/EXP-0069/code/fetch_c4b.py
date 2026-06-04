import json, time, sys, urllib.parse, requests, os
OUT = os.path.join(os.path.dirname(__file__), "..", "data")
BASE = "https://datasets-server.huggingface.co/rows"
def fetch_lang(cfg, split, n_target, per=100):
    rows=[]; off=0; fails=0
    while len(rows) < n_target:
        params={"dataset":"allenai/c4","config":cfg,"split":split,"offset":off,"length":per}
        url=BASE+"?"+urllib.parse.urlencode(params); ok=False
        for attempt in range(6):
            try:
                r=requests.get(url,timeout=40)
                if r.status_code==200: ok=True; break
                time.sleep(2.0*(attempt+1))
            except Exception: time.sleep(2.0*(attempt+1))
        if not ok:
            fails+=1; print(f"  [{cfg}] fail off={off} (#{fails})",file=sys.stderr)
            if fails>5: break
            time.sleep(5); off+=per; continue
        data=r.json(); batch=data.get("rows",[])
        if not batch: break
        for item in batch:
            t=item["row"].get("text","")
            if t: rows.append(t)
        off+=per
        if off%500==0: print(f"  [{cfg}] {len(rows)} docs",file=sys.stderr)
        time.sleep(0.3)
    return rows[:n_target]
if __name__=="__main__":
    langs=sys.argv[1].split(","); n=int(sys.argv[2])
    for cfg in langs:
        t0=time.time(); docs=fetch_lang(cfg,"validation",n)
        path=os.path.join(OUT,f"c4_{cfg}.jsonl")
        with open(path,"w") as f:
            for d in docs: f.write(json.dumps({"text":d})+"\n")
        print(f"[{cfg}] saved {len(docs)} -> {path} ({time.time()-t0:.0f}s)")

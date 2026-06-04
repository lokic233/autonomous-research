"""Stream real C4-multilingual docs via HF datasets-server /rows (no big download).
Saves JSONL per language. CPU-only, network-light."""
import json, time, sys, urllib.parse, requests, os

OUT = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(OUT, exist_ok=True)
BASE = "https://datasets-server.huggingface.co/rows"

def fetch_lang(cfg, split, n_target, per=100):
    rows = []
    off = 0
    while len(rows) < n_target:
        params = {"dataset":"allenai/c4","config":cfg,"split":split,"offset":off,"length":per}
        url = BASE + "?" + urllib.parse.urlencode(params)
        for attempt in range(4):
            try:
                r = requests.get(url, timeout=30)
                if r.status_code==200:
                    break
                time.sleep(1.5)
            except Exception as e:
                time.sleep(1.5)
        else:
            print(f"  [{cfg}] failed at off={off}", file=sys.stderr); break
        data = r.json()
        batch = data.get("rows", [])
        if not batch:
            break
        for item in batch:
            t = item["row"].get("text","")
            if t:
                rows.append(t)
        off += per
        if off % 1000 == 0:
            print(f"  [{cfg}] {len(rows)} docs", file=sys.stderr)
    return rows[:n_target]

if __name__ == "__main__":
    langs = sys.argv[1].split(",") if len(sys.argv)>1 else ["ja","zh","ar","de","fr"]
    n = int(sys.argv[2]) if len(sys.argv)>2 else 6000
    for cfg in langs:
        t0=time.time()
        docs = fetch_lang(cfg, "validation", n)
        path = os.path.join(OUT, f"c4_{cfg}.jsonl")
        with open(path,"w") as f:
            for d in docs: f.write(json.dumps({"text":d})+"\n")
        print(f"[{cfg}] saved {len(docs)} docs -> {path} ({time.time()-t0:.0f}s)")

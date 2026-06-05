import os, json, io, csv
os.environ["no_proxy"]="localhost,127.0.0.1,.internalfb.com"
os.environ["NO_PROXY"]="localhost,127.0.0.1,.internalfb.com"
import requests, pyarrow as pa, pyarrow.parquet as pq

HF="https://huggingface.co"
S=requests.Session()

class HttpRangeFile(io.RawIOBase):
    """Minimal seekable file over HTTP byte-range — only reads what pyarrow asks for (footer)."""
    def __init__(self,url):
        self.url=url; self._pos=0
        r=S.head(url,allow_redirects=True,timeout=30)
        self.url=r.url
        self.size=int(r.headers.get("Content-Length",0))
        if self.size==0:
            r2=S.get(url,headers={"Range":"bytes=0-0"},allow_redirects=True,timeout=30)
            cr=r2.headers.get("Content-Range","")
            self.url=r2.url
            if "/" in cr: self.size=int(cr.split("/")[-1])
    def seekable(self): return True
    def readable(self): return True
    def seek(self,off,whence=0):
        if whence==0: self._pos=off
        elif whence==1: self._pos+=off
        elif whence==2: self._pos=self.size+off
        return self._pos
    def tell(self): return self._pos
    def read(self,n=-1):
        if n is None or n<0: n=self.size-self._pos
        if n==0: return b""
        end=min(self._pos+n-1,self.size-1)
        r=S.get(self.url,headers={"Range":f"bytes={self._pos}-{end}"},allow_redirects=True,timeout=60)
        data=r.content; self._pos+=len(data); return data
    def readall(self):
        return self.read(self.size-self._pos)

def list_parquet_datasets(n):
    r=S.get(f"{HF}/api/datasets",params={"filter":"format:parquet","sort":"downloads","direction":"-1","limit":n},timeout=30)
    return [d["id"] for d in r.json()]

def parquet_files(repo,max_files=2):
    try:
        r=S.get(f"{HF}/api/datasets/{repo}/tree/main",params={"recursive":"true"},timeout=30)
        return [it["path"] for it in r.json() if isinstance(it,dict) and it.get("path","").endswith(".parquet")][:max_files]
    except Exception: return []

def url(repo,pf): return f"{HF}/datasets/{repo}/resolve/main/{pf}"

results=[]; errors=[]
scanned_files=scanned_cols=dict_cols=ordered_cols=ordered_nonalpha=0
repos=list_parquet_datasets(200)
print(f"got {len(repos)} datasets",flush=True)
for repo in repos:
    if scanned_files>=250: break
    for pf in parquet_files(repo,2):
        if scanned_files>=250: break
        try:
            fobj=HttpRangeFile(url(repo,pf))
            pqf=pq.ParquetFile(fobj)
            sch=pqf.schema_arrow; scanned_files+=1
            for field in sch:
                scanned_cols+=1; t=field.type
                if pa.types.is_dictionary(t):
                    dict_cols+=1; ordered=bool(t.ordered)
                    rec={"repo":repo,"file":pf,"col":field.name,"ordered":ordered,"value_type":str(t.value_type)}
                    if ordered:
                        ordered_cols+=1
                        try:
                            col=pqf.read_row_group(0,columns=[field.name])[field.name]
                            ch=col.chunk(0) if col.num_chunks>0 else None
                            dom=ch.dictionary.to_pylist() if ch is not None else []
                        except Exception: dom=[]
                        vs=[v for v in dom if v is not None]; na=(vs!=sorted(vs))
                        rec["domain"]=vs[:20]; rec["nonalpha"]=na
                        if na: ordered_nonalpha+=1
                    results.append(rec)
        except Exception as e:
            errors.append({"repo":repo,"file":pf,"err":f"{type(e).__name__}:{str(e)[:100]}"}); continue
    if scanned_files>0 and scanned_files%20==0:
        print(f"...{scanned_files} files | {dict_cols} dict | {ordered_cols} ordered | {ordered_nonalpha} ord+nonalpha",flush=True)

summary={"scanned_files":scanned_files,"scanned_cols":scanned_cols,"dict_cols":dict_cols,
         "ordered_cols":ordered_cols,"ordered_nonalpha_cols":ordered_nonalpha,
         "errors":len(errors),"repos_attempted":len(repos)}
print("\n=== PREVALENCE SUMMARY ==="); print(json.dumps(summary,indent=2))
json.dump({"summary":summary,"records":results,"errors":errors[:40]},open("prevalence.json","w"),indent=2)
with open("prevalence_cols.csv","w",newline="") as fh:
    w=csv.writer(fh); w.writerow(["repo","file","col","ordered","nonalpha","value_type","domain_sample"])
    for r in results:
        w.writerow([r["repo"],r["file"],r["col"],r["ordered"],r.get("nonalpha",""),r["value_type"],"|".join(map(str,r.get("domain",[])[:8]))])
print("wrote prevalence.json + prevalence_cols.csv")

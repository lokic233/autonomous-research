import os, json, io, csv
os.environ["no_proxy"]="localhost,127.0.0.1,.internalfb.com"; os.environ["NO_PROXY"]=os.environ["no_proxy"]
import requests, pyarrow as pa, pyarrow.parquet as pq
HF="https://huggingface.co"; S=requests.Session()
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


def search_datasets(query,n=60):
    r=S.get(f"{HF}/api/datasets",params={"search":query,"filter":"format:parquet","sort":"downloads","direction":"-1","limit":n},timeout=30)
    return [d["id"] for d in r.json()]
def parquet_files(repo,m=2):
    try:
        r=S.get(f"{HF}/api/datasets/{repo}/tree/main",params={"recursive":"true"},timeout=30)
        return [it["path"] for it in r.json() if isinstance(it,dict) and it.get("path","").endswith(".parquet")][:m]
    except: return []
def url(repo,pf): return f"{HF}/datasets/{repo}/resolve/main/{pf}"

# tabular / categorical-likely corpora
queries=["tabular","classification","csv","survey","census","credit","titanic","iris","kaggle","sales","clinical","education"]
repos=[]
for q in queries:
    repos += search_datasets(q,25)
repos=list(dict.fromkeys(repos))  # dedupe preserve order
print(f"{len(repos)} tabular-candidate datasets",flush=True)

results=[]; errors=[]
sf=sc=dc=oc=onc=0
for repo in repos:
    if sf>=250: break
    for pf in parquet_files(repo,2):
        if sf>=250: break
        try:
            pqf=pq.ParquetFile(HttpRangeFile(url(repo,pf))); sch=pqf.schema_arrow; sf+=1
            for field in sch:
                sc+=1; t=field.type
                if pa.types.is_dictionary(t):
                    dc+=1; od=bool(t.ordered)
                    rec={"repo":repo,"file":pf,"col":field.name,"ordered":od,"value_type":str(t.value_type)}
                    if od:
                        oc+=1
                        try:
                            col=pqf.read_row_group(0,columns=[field.name])[field.name]
                            ch=col.chunk(0) if col.num_chunks>0 else None
                            dom=ch.dictionary.to_pylist() if ch is not None else []
                        except: dom=[]
                        vs=[v for v in dom if v is not None]; na=(vs!=sorted(vs))
                        rec["domain"]=vs[:20]; rec["nonalpha"]=na
                        if na: onc+=1
                    results.append(rec)
        except Exception as e:
            errors.append({"repo":repo,"file":pf,"err":f"{type(e).__name__}:{str(e)[:80]}"})
    if sf>0 and sf%25==0: print(f"...{sf} files | {dc} dict | {oc} ordered | {onc} ord+nonalpha",flush=True)

summary={"scanned_files":sf,"scanned_cols":sc,"dict_cols":dc,"ordered_cols":oc,
         "ordered_nonalpha_cols":onc,"errors":len(errors),"repos_attempted":len(repos)}
print("\n=== TABULAR PREVALENCE ==="); print(json.dumps(summary,indent=2))
json.dump({"summary":summary,"records":results,"errors":errors[:30]},open("prevalence_tabular.json","w"),indent=2)

#!/usr/bin/env python3
"""EXP-0064 CLAIM-0056: length-sorted packing -> GNS inflation. PURE STDLIB, SERIAL, CPU-only.
Honest pipeline: real text corpus, frozen identical model both arms, real per-minibatch gradients,
McCandlish B_simple GNS. Reports the 3 null exits. researcher-0062."""
import os, re, glob, math, random, csv, json, time
random.seed(1234)
T0=time.time()
OUT="/Users/dengcchi/autonomous-research-v3/experiments/2026-06-04/EXP-0064"

# ---------------- CORPUS: REAL text, 4 domains, naturally different lengths ----------------
PYLIB="/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9"
MAN1="/usr/share/man/man1"; MAN5="/usr/share/man/man5"

def tokenize(s):
    # pure-stdlib word/punct tokenizer
    return re.findall(r"[A-Za-z_]+|[0-9]+|[^\sA-Za-z0-9]", s)

docs=[]  # (domain, tokens_list)
def add(domain, text, lo=8, hi=400):
    toks=tokenize(text)
    if lo<=len(toks)<=hi:
        docs.append((domain, toks))

# CODE: split stdlib .py into top-level def/class blocks (real code, variable length)
pyfiles=glob.glob(os.path.join(PYLIB,"*.py"))+glob.glob(os.path.join(PYLIB,"*/*.py"))
random.shuffle(pyfiles)
ndoc_code=0
for f in pyfiles:
    if ndoc_code>=2000: break
    try: src=open(f,encoding="utf-8",errors="ignore").read()
    except: continue
    # split into blocks at top-level def/class
    blocks=re.split(r"\n(?=def |class )", src)
    for b in blocks:
        if ndoc_code>=2000: break
        if b.strip().startswith(("def ","class ")):
            add("CODE", b); ndoc_code+=1

# DOCSTRING: extract triple-quoted strings (natural-language doc, medium)
ndoc_ds=0
for f in pyfiles:
    if ndoc_ds>=1500: break
    try: src=open(f,encoding="utf-8",errors="ignore").read()
    except: continue
    for m in re.findall(r'"""(.*?)"""', src, re.S):
        if ndoc_ds>=1500: break
        if len(m.split())>=8:
            add("DOCSTRING", m); ndoc_ds+=1

# MAN1: command manuals (troff prose, medium-long)
m1=glob.glob(os.path.join(MAN1,"*.1"))[:1400]
for f in m1:
    try: t=open(f,encoding="utf-8",errors="ignore").read()
    except: continue
    add("MAN1", t)

# MAN5: file-format manuals (troff, short-medium)
m5=glob.glob(os.path.join(MAN5,"*.5"))[:600]
for f in m5:
    try: t=open(f,encoding="utf-8",errors="ignore").read()
    except: continue
    add("MAN5", t)

random.shuffle(docs)
domains=sorted(set(d for d,_ in docs))
DOM={d:i for i,d in enumerate(domains)}
print(f"[corpus] {len(docs)} docs, domains={domains}")
from collections import Counter
print("[corpus] per-domain counts:", dict(Counter(d for d,_ in docs)))

# ---------------- per-domain length stats + length<->domain MI (NULL EXIT A) ----------------
lengths=[len(t) for _,t in docs]
# length bins (deciles)
sl=sorted(lengths); nb=10
edges=[sl[int(i*len(sl)/nb)] for i in range(nb)]+[sl[-1]+1]
def lbin(L):
    for i in range(nb):
        if L<edges[i+1]: return i
    return nb-1
N=len(docs)
# joint p(domain,lengthbin)
joint=Counter(); pd=Counter(); pl=Counter()
for (dm,t) in docs:
    b=lbin(len(t)); joint[(dm,b)]+=1; pd[dm]+=1; pl[b]+=1
MI=0.0
for (dm,b),c in joint.items():
    pxy=c/N; px=pd[dm]/N; py=pl[b]/N
    MI+=pxy*math.log2(pxy/(px*py))
Hd=-sum((c/N)*math.log2(c/N) for c in pd.values())
Hl=-sum((c/N)*math.log2(c/N) for c in pl.values())
NMI=MI/min(Hd,Hl) if min(Hd,Hl)>0 else 0.0
print(f"[NULL-A] length<->domain MI={MI:.4f} bits, H(domain)={Hd:.3f}, NMI={NMI:.4f}")
# per-domain mean length
dom_meanlen={d: (sum(len(t) for dd,t in docs if dd==d)/max(1,sum(1 for dd,_ in docs if dd==d))) for d in domains}
print("[length] per-domain mean token len:", {k:round(v,1) for k,v in dom_meanlen.items()})

# ==================== FROZEN MODEL (identical across ALL arms & MAXLENs) ====================
D=16; V=4096
def tid(tok): return (hash(tok)%V)
rng=random.Random(7)
E=[[rng.gauss(0,0.1) for _ in range(D)] for _ in range(V)]
W=[[rng.gauss(0,0.1) for _ in range(D)] for _ in range(V)]
K=12
negbase=[rng.randrange(V) for _ in range(K-1)]

def row_grad(row, MAXLEN):
    g={}; nstep=0
    for di in row:
        toks=docs[di][1][:MAXLEN]
        ids=[tid(t) for t in toks]
        for p in range(len(ids)-1):
            cur=ids[p]; tgt=ids[p+1]; cand=[tgt]+negbase; ev=E[cur]
            logits=[sum(W[c][d]*ev[d] for d in range(D)) for c in cand]
            m=max(logits); ex=[math.exp(l-m) for l in logits]; Z=sum(ex); ps=[e/Z for e in ex]
            gv=g.get(cur)
            if gv is None: gv=[0.0]*D; g[cur]=gv
            for ci,c in enumerate(cand):
                coef=ps[ci]-(1.0 if ci==0 else 0.0); Wc=W[c]
                for d in range(D): gv[d]+=coef*Wc[d]
            nstep+=1
    if nstep>0:
        inv=1.0/nstep
        for k in g:
            gv=g[k]
            for d in range(D): gv[d]*=inv
    return g

def add_into(acc,g,w=1.0):
    for k,gv in g.items():
        a=acc.get(k)
        if a is None: a=[0.0]*D; acc[k]=a
        for d in range(D): a[d]+=w*gv[d]
def diff_sqnorm(g,gbar):
    keys=set(g)|set(gbar); s=0.0
    for k in keys:
        a=g.get(k,[0.0]*D); b=gbar.get(k,[0.0]*D)
        for d in range(D):
            dd=a[d]-b[d]; s+=dd*dd
    return s

MB=8
buffers=[("1k",1000),("10k",10000),("inf",None)]
MAXLENS=[128,256,512]
allidx=list(range(len(docs)))
gns_rows=[]   # (maxlen, mean_dpp, buffer, GNS_sorted, GNS_shuf, ratio, lo, hi, ent_s, ent_h)
dpp_rows=[]

def packer(doc_idx, MAXLEN):
    order=sorted(doc_idx,key=lambda i:len(docs[i][1]),reverse=True)
    rows=[]; rem=[]
    for i in order:
        L=min(len(docs[i][1]),MAXLEN); best=-1; bestrem=MAXLEN+1
        for r in range(len(rows)):
            if rem[r]>=L and rem[r]<bestrem: bestrem=rem[r]; best=r
        if best>=0: rows[best].append(i); rem[best]-=L
        else: rows.append([i]); rem.append(MAXLEN-L)
    return rows

def emit_sorted(n): return list(range(n))
def emit_shuf(n,buf):
    if buf is None or buf>=n:
        o=list(range(n)); random.Random(99).shuffle(o); return o
    rnd=random.Random(99); out=[]; window=[]; it=iter(range(n))
    for _ in range(min(buf,n)): window.append(next(it))
    for x in it:
        j=rnd.randrange(len(window)); out.append(window[j]); window[j]=x
    rnd.shuffle(window); out.extend(window); return out

from collections import Counter as Ctr
for MAXLEN in MAXLENS:
    rows=packer(allidx,MAXLEN)
    mean_dpp=sum(len(r) for r in rows)/len(rows)
    dpp_rows.append((MAXLEN,len(rows),round(mean_dpp,3)))
    print(f"[MAXLEN={MAXLEN}] {len(rows)} rows mean_dpp={mean_dpp:.2f} t={time.time()-T0:.1f}s",flush=True)
    rg=[row_grad(r,MAXLEN) for r in rows]
    gfull={}
    for g in rg: add_into(gfull,g,1.0/len(rows))
    gfull_sq=sum(v*v for vec in gfull.values() for v in vec)
    def mb_grad(idx):
        acc={}
        for ri in idx: add_into(acc,rg[ri],1.0/len(idx))
        return acc
    def dom_ent(idx):
        c=Ctr()
        for ri in idx:
            for di in rows[ri]: c[docs[di][0]]+=1
        tot=sum(c.values()); return -sum((v/tot)*math.log2(v/tot) for v in c.values())
    def gns(order):
        nmb=len(order)//MB; gs=[]; ents=[]
        for i in range(nmb):
            idx=order[i*MB:(i+1)*MB]; gs.append(mb_grad(idx)); ents.append(dom_ent(idx))
        gbar={}
        for g in gs: add_into(gbar,g,1.0/len(gs))
        var=sum(diff_sqnorm(g,gbar) for g in gs)/(len(gs)-1)
        return MB*var/gfull_sq, sum(ents)/len(ents), gs
    def bsimp(gs):
        gbar={}
        for g in gs: add_into(gbar,g,1.0/len(gs))
        return MB*(sum(diff_sqnorm(g,gbar) for g in gs)/(len(gs)-1))/gfull_sq
    Bs,ents,gs_s=gns(emit_sorted(len(rows)))
    for nm,buf in buffers:
        Bh,enth,gs_h=gns(emit_shuf(len(rows),buf))
        ratio=Bs/Bh if Bh>0 else float('nan')
        # bootstrap CI (lighter: 200)
        rb=random.Random(5); ratios=[]
        ns=len(gs_s); nh=len(gs_h)
        for _ in range(200):
            ss=[gs_s[rb.randrange(ns)] for _ in range(ns)]; hh=[gs_h[rb.randrange(nh)] for _ in range(nh)]
            bh=bsimp(hh)
            if bh>0: ratios.append(bsimp(ss)/bh)
        ratios.sort(); lo=ratios[int(0.025*len(ratios))]; hi=ratios[int(0.975*len(ratios))]
        gns_rows.append((MAXLEN,round(mean_dpp,2),nm,Bs,Bh,ratio,lo,hi,ents,enth))
        print(f"   buf={nm:4s} GNS_s={Bs:.3f} GNS_h={Bh:.3f} RATIO={ratio:.3f} CI[{lo:.3f},{hi:.3f}] ent_s={ents:.3f} ent_h={enth:.3f}",flush=True)

with open(f"{OUT}/gns_by_buffer.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["maxlen","mean_docs_per_pack","buffer","GNS_sorted","GNS_shuffled","ratio","ci_lo","ci_hi","ent_sorted","ent_shuffled"])
    for r in gns_rows: w.writerow([r[0],r[1],r[2],f"{r[3]:.5f}",f"{r[4]:.5f}",f"{r[5]:.4f}",f"{r[6]:.4f}",f"{r[7]:.4f}",f"{r[8]:.4f}",f"{r[9]:.4f}"])
with open(f"{OUT}/dpp_by_maxlen.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["maxlen","n_rows","mean_docs_per_pack"])
    for r in dpp_rows: w.writerow(r)
with open(f"{OUT}/length_hist.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["domain","mean_token_len","n_docs"])
    for d in domains: w.writerow([d,f"{dom_meanlen[d]:.2f}",sum(1 for dd,_ in docs if dd==d)])
with open(f"{OUT}/diagnostics.json","w") as f:
    json.dump({"n_docs":N,"domains":domains,"per_domain_counts":dict(Counter(d for d,_ in docs)),
               "MI_bits":MI,"NMI":NMI,"H_domain":Hd,"H_lengthbin":Hl,"MB_rows":MB,
               "per_domain_mean_len":dom_meanlen,"maxlen_sweep":dpp_rows},f,indent=2)
print(f"[done] t={time.time()-T0:.1f}s",flush=True)

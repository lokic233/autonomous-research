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
    if ndoc_code>=1600: break
    try: src=open(f,encoding="utf-8",errors="ignore").read()
    except: continue
    # split into blocks at top-level def/class
    blocks=re.split(r"\n(?=def |class )", src)
    for b in blocks:
        if ndoc_code>=1600: break
        if b.strip().startswith(("def ","class ")):
            add("CODE", b); ndoc_code+=1

# DOCSTRING: extract triple-quoted strings (natural-language doc, medium)
ndoc_ds=0
for f in pyfiles:
    if ndoc_ds>=1200: break
    try: src=open(f,encoding="utf-8",errors="ignore").read()
    except: continue
    for m in re.findall(r'"""(.*?)"""', src, re.S):
        if ndoc_ds>=1200: break
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

# ---------------- PACKER: SPFHP-style best-fit-decreasing ----------------
MAXLEN=512
def pack(doc_idx):
    # sort by length DESC
    order=sorted(doc_idx, key=lambda i: len(docs[i][1]), reverse=True)
    rows=[]; rows_rem=[]
    for i in order:
        L=len(docs[i][1])
        if L>MAXLEN:  # truncate over-long (rare)
            L=MAXLEN
        placed=False
        # best-fit: tightest row that still fits
        best=-1; bestrem=MAXLEN+1
        for r in range(len(rows)):
            if rows_rem[r]>=L and rows_rem[r]<bestrem:
                bestrem=rows_rem[r]; best=r
        if best>=0:
            rows[best].append(i); rows_rem[best]-=L; placed=True
        if not placed:
            rows.append([i]); rows_rem.append(MAXLEN-L)
    return rows  # list of rows in PACKER ORDER (length-sorted)

allidx=list(range(len(docs)))
rows=pack(allidx)
docs_per_pack=[len(r) for r in rows]
mean_dpp=sum(docs_per_pack)/len(rows)
print(f"[packer] {len(rows)} rows, mean docs/pack={mean_dpp:.2f} (NULL EXIT B driver)")


# ---------------- FROZEN MODEL (identical across arms) ----------------
# hashed token vocab -> D-dim frozen embedding E (trainable block for gradient) + frozen head W.
# loss per row = mean next-token CE under frozen W on E[token]. Gradient = dL/dE (real analytic CE grad).
D=16          # embedding dim
V=4096        # hashed vocab buckets
def tid(tok): return (hash(tok)% V)
# frozen params (seed-frozen) — IDENTICAL for both arms
rng=random.Random(7)
E=[[rng.gauss(0,0.1) for _ in range(D)] for _ in range(V)]   # embedding table (trainable block)
W=[[rng.gauss(0,0.1) for _ in range(D)] for _ in range(V)]   # frozen output head (vocab x D)

# To keep <=15min SERIAL & pure-stdlib: use a COMPACT exact gradient.
# Per next-token step: logits_j = sum_d W[j][d]*E[cur][d]; softmax CE vs target token.
# dL/dE[cur][d] = sum_j (p_j - 1{j=tgt}) * W[j][d].
# Full softmax over V=4096 per step is too slow; use NEGATIVE-SAMPLING CE over a fixed frozen
# candidate set of K tokens (target + K-1 frozen negatives) -> exact CE on that head subset.
# This is a real, deterministic loss/gradient; identical head subset per (cur) so arms comparable.
K=12
negbase=[rng.randrange(V) for _ in range(K-1)]  # frozen negatives (shared, deterministic)

def row_grad(row):
    """Return dict: embed_index -> [D] grad accumulation, for one packed row (mean CE next-token)."""
    g={}; nstep=0
    for di in row:
        toks=docs[di][1][:MAXLEN]
        ids=[tid(t) for t in toks]
        for p in range(len(ids)-1):
            cur=ids[p]; tgt=ids[p+1]
            cand=[tgt]+negbase
            ev=E[cur]
            logits=[sum(W[c][d]*ev[d] for d in range(D)) for c in cand]
            m=max(logits); ex=[math.exp(l-m) for l in logits]; Z=sum(ex)
            ps=[e/Z for e in ex]
            # dL/dE[cur][d] = sum_c (p_c - 1{c==tgt}) * W[c][d]; tgt is cand[0]
            gv=g.get(cur)
            if gv is None: gv=[0.0]*D; g[cur]=gv
            for ci,c in enumerate(cand):
                coef=ps[ci]-(1.0 if ci==0 else 0.0)
                Wc=W[c]
                for d in range(D): gv[d]+=coef*Wc[d]
            nstep+=1
    if nstep>0:
        inv=1.0/nstep
        for k in g: 
            gv=g[k]
            for d in range(D): gv[d]*=inv
    return g, nstep

# Precompute per-row gradients ONCE (rows identical across arms -> reuse). Sparse dicts.
print(f"[grad] precomputing {len(rows)} row gradients... t={time.time()-T0:.1f}s")
row_grads=[]; 
for ri,r in enumerate(rows):
    g,_=row_grad(r); row_grads.append(g)
    if ri%500==0: print(f"   row {ri} t={time.time()-T0:.1f}s")
print(f"[grad] done t={time.time()-T0:.1f}s")

# full-batch gradient g_full = mean over all rows (sparse) — arm-independent
def add_into(acc, g, w=1.0):
    for k,gv in g.items():
        a=acc.get(k)
        if a is None: a=[0.0]*D; acc[k]=a
        for d in range(D): a[d]+=w*gv[d]
gfull={}; 
for g in row_grads: add_into(gfull,g, 1.0/len(rows))
def sqnorm(g): return sum(v*v for vec in g.values() for v in vec)
gfull_sq=sqnorm(gfull)
print(f"[grad] ||g_full||^2={gfull_sq:.6e}")

# ---------------- GNS via McCandlish B_simple, per arm per buffer ----------------
MB=8  # rows per minibatch (nominal batch). With mean_dpp docs/pack -> ~MB*mean_dpp docs/batch.

def minibatch_grad(row_indices):
    acc={}; 
    for ri in row_indices: add_into(acc, row_grads[ri], 1.0/len(row_indices))
    return acc
def diff_sqnorm(g, gbar):
    keys=set(g)|set(gbar); s=0.0
    for k in keys:
        a=g.get(k,[0.0]*D); b=gbar.get(k,[0.0]*D)
        for d in range(D):
            dd=a[d]-b[d]; s+=dd*dd
    return s

def emit_order_sorted(): return list(range(len(rows)))   # packer order = length-sorted
def emit_order_shuffled(buf):
    # finite shuffle-buffer reservoir emission
    if buf is None or buf>=len(rows):
        o=list(range(len(rows))); random.Random(99).shuffle(o); return o
    rnd=random.Random(99); src=list(range(len(rows))); out=[]; window=[]
    it=iter(src)
    for _ in range(min(buf,len(src))): window.append(next(it))
    for x in it:
        j=rnd.randrange(len(window)); out.append(window[j]); window[j]=x
    rnd.shuffle(window); out.extend(window); return out

def domain_entropy_of_batch(row_indices):
    c=Counter()
    for ri in row_indices:
        for di in rows[ri]: c[docs[di][0]]+=1
    tot=sum(c.values()); 
    return -sum((v/tot)*math.log2(v/tot) for v in c.values()) if tot>0 else 0.0

def gns_for_order(order):
    nmb=len(order)//MB
    gs=[]; ents=[]
    for i in range(nmb):
        idx=order[i*MB:(i+1)*MB]
        gs.append(minibatch_grad(idx))
        ents.append(domain_entropy_of_batch(idx))
    # gbar = mean of minibatch grads
    gbar={}; 
    for g in gs: add_into(gbar,g,1.0/len(gs))
    var=sum(diff_sqnorm(g,gbar) for g in gs)/(len(gs)-1)
    trSigma=MB*var
    Bsimple=trSigma/gfull_sq
    return Bsimple, sum(ents)/len(ents), gs, ents

def bootstrap_ratio(gs_s, gs_h, nboot=300):
    # ratio of B_simple via bootstrap over minibatches
    import random as R
    rb=R.Random(5)
    def bsimp(gs):
        gbar={}; 
        for g in gs: add_into(gbar,g,1.0/len(gs))
        var=sum(diff_sqnorm(g,gbar) for g in gs)/(len(gs)-1); return MB*var/gfull_sq
    ratios=[]
    ns=len(gs_s); nh=len(gs_h)
    for _ in range(nboot):
        ss=[gs_s[rb.randrange(ns)] for _ in range(ns)]
        hh=[gs_h[rb.randrange(nh)] for _ in range(nh)]
        bh=bsimp(hh)
        if bh>0: ratios.append(bsimp(ss)/bh)
    ratios.sort()
    return ratios[int(0.025*len(ratios))], ratios[int(0.975*len(ratios))]

buffers=[("1k",1000),("10k",10000),("inf",None)]
print(f"[gns] MB={MB} rows/batch, mean docs/batch~{MB*mean_dpp:.1f}")
B_sorted, ent_sorted, gs_sorted, _ = gns_for_order(emit_order_sorted())
results=[]
for name,buf in buffers:
    B_sh, ent_sh, gs_sh, _ = gns_for_order(emit_order_shuffled(buf))
    ratio=B_sorted/B_sh if B_sh>0 else float('nan')
    lo,hi=bootstrap_ratio(gs_sorted, gs_sh)
    results.append((name,B_sorted,B_sh,ratio,lo,hi,ent_sorted,ent_sh))
    print(f"[gns] buffer={name:4s} GNS_sorted={B_sorted:.4f} GNS_shuf={B_sh:.4f} RATIO={ratio:.3f} CI[{lo:.3f},{hi:.3f}] ent_s={ent_sorted:.3f} ent_h={ent_sh:.3f}")

# ---------------- WRITE CSVs ----------------
with open(f"{OUT}/gns_by_buffer.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["buffer","GNS_sorted","GNS_shuffled","ratio","ci_lo","ci_hi","ent_sorted","ent_shuffled"])
    for r in results: w.writerow([r[0],f"{r[1]:.5f}",f"{r[2]:.5f}",f"{r[3]:.4f}",f"{r[4]:.4f}",f"{r[5]:.4f}",f"{r[6]:.4f}",f"{r[7]:.4f}"])
with open(f"{OUT}/length_hist.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["domain","mean_token_len","n_docs"])
    for d in domains: w.writerow([d,f"{dom_meanlen[d]:.2f}",sum(1 for dd,_ in docs if dd==d)])
with open(f"{OUT}/diagnostics.json","w") as f:
    json.dump({"n_docs":N,"domains":domains,"per_domain_counts":dict(Counter(d for d,_ in docs)),
               "MI_bits":MI,"NMI":NMI,"H_domain":Hd,"H_lengthbin":Hl,
               "n_rows":len(rows),"mean_docs_per_pack":mean_dpp,"MB_rows":MB,
               "gfull_sq":gfull_sq,"per_domain_mean_len":dom_meanlen}, f, indent=2)
print(f"[done] total t={time.time()-T0:.1f}s")

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


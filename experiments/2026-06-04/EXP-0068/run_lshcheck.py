import sys,importlib,random,statistics as st,json,time
sys.path.insert(0,'.'); import harness; importlib.reload(harness); import harness as H
t0=time.time()
# REAL banded MinHash-LSH with a HIGH-knee config (b=4,r=16 -> knee~0.92, production-strict near-dup)
# Use UNIQUE doc content (sequential ids) so common-word collisions don't inflate band matches.
def uniq_doc(rng,length,uid):
    # prepend a unique token so docs aren't near-duplicates of each other by chance
    return f"DOC{uid}X " + " ".join(rng.choice(H.VOCAB) for _ in range(length))
def cell(arm,nm,frac,b,r,perms_n,n,seed):
    rng=random.Random(seed*131+hash(nm)%71+hash(arm)%41+int(frac*1000))
    perms,MAXH=H.make_perms(perms_n,seed=999); dn=H.NORMALIZERS[nm]
    ngt=0;miss=0
    for u in range(n):
        d1=uniq_doc(rng,55,seed*100000+u); npos=H.normalizable_positions(d1)
        if not npos:continue
        rng.shuffle(npos); ch=npos[:max(1,round(frac*len(npos)))]
        d2,ap=(H.apply_normalizable_at(d1,ch) if arm=='normalizable' else H.apply_typo(d1,rng,ch))
        if ap==0:continue
        gt=(H.model_normalize(d1)==H.model_normalize(d2))
        if not gt: continue
        ngt+=1
        s1=H.shingles(dn(d1));s2=H.shingles(dn(d2))
        sig1=H.minhash_sig(s1,perms,MAXH);sig2=H.minhash_sig(s2,perms,MAXH)
        if not H.lsh_collide(sig1,sig2,b,r): miss+=1
    return miss/ngt if ngt else float('nan'),ngt
SEEDS=[1,2,3]
print("REAL banded MinHash-LSH, b=4 r=16 (64 perms, knee~0.92), unique docs, normalizable arm FN:")
print(f"{'frac':<6}{'raw':>9}{'NFC':>9}{'NFKC':>9}{'NFKC+cf':>9}")
out=[]
for frac in [0.1,0.2,0.3,0.5]:
    row=f"{frac:<6}"
    rec={'frac':frac}
    for nm in ['raw','NFC','NFKC','NFKC+casefold']:
        vals=[cell('normalizable',nm,frac,4,16,64,120,s)[0] for s in SEEDS]
        m=st.mean([v for v in vals if v==v]); row+=f"{m:>9.2f}"; rec[nm]=m
    out.append(rec); print(row,flush=True)
json.dump(out,open('results/lshcheck.json','w'),indent=1)
print(f"elapsed {time.time()-t0:.0f}s")

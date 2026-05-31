import json,glob,collections,math,statistics,re
fs=glob.glob('/Users/dengcchi/.codex/sessions/**/*.jsonl',recursive=True)

def runs_z(seq):
    n1=sum(seq); n0=len(seq)-n1
    if n1==0 or n0==0: return None
    R=1
    for i in range(1,len(seq)):
        if seq[i]!=seq[i-1]: R+=1
    n=n0+n1; mu=2*n0*n1/n+1
    var=(2*n0*n1*(2*n0*n1-n))/(n*n*(n-1))
    if var<=0: return None
    return (R-mu)/math.sqrt(var)

zs=[]; tot=0; errs=0; nfiles=0
for f in fs:
    seen=set(); seq=[]
    for line in open(f):
        line=line.strip()
        if not line: continue
        try: d=json.loads(line)
        except: continue
        p=d.get('payload') or d
        if p.get('type')=='function_call_output':
            cid=p.get('call_id')
            if cid in seen: continue  # dedup
            seen.add(cid)
            out=str(p.get('output',''))
            m=re.search(r'exited with code (\d+)', out)
            err=0
            if m and m.group(1)!='0': err=1
            elif 'error' in out[:120].lower() and 'code 0' not in out: err=1
            seq.append(err)
    if len(seq)>=8:
        tot+=len(seq); errs+=sum(seq); nfiles+=1
        if 0<sum(seq)<len(seq):
            z=runs_z(seq)
            if z is not None: zs.append(z)
print(f"codex sessions>=8 calls: {nfiles}, total calls: {tot}, failures: {errs} ({errs/max(tot,1):.3f})")
if zs:
    print(f"usable={len(zs)} meanZ={statistics.mean(zs):.3f} medianZ={statistics.median(zs):.3f} StoufferZ={sum(zs)/math.sqrt(len(zs)):.2f}")
    print(f"sessions Z<0: {sum(1 for z in zs if z<0)}/{len(zs)}")

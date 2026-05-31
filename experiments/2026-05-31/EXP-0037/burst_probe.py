import json, glob, collections, math, random

def iter_events(f):
    """Yield (timestamp, kind) where kind in {'use','result_ok','result_err'} in file order."""
    for line in open(f):
        line=line.strip()
        if not line: continue
        try: d=json.loads(line)
        except: continue
        ts=d.get('timestamp')
        msg=d.get('message')
        if isinstance(msg,dict) and isinstance(msg.get('content'),list):
            for b in msg['content']:
                if not isinstance(b,dict): continue
                if b.get('type')=='tool_use':
                    yield (ts,'use', b.get('name'))
                elif b.get('type')=='tool_result':
                    yield (ts,'err' if b.get('is_error') else 'ok', None)

fs = glob.glob('/Users/dengcchi/.claude/projects/*/*.jsonl')

# Per session: ordered sequence of tool RESULTS (ok/err). A "trial" = each tool_result.
# Burstiness target: is the failure indicator sequence overdispersed (runs of failures)
# relative to a Bernoulli(p) null with the same p?
sessions=collections.defaultdict(list)  # sessionId -> list of 0/1 (1=err)
for f in fs:
    sid=None
    seq=[]
    for ts,kind,name in iter_events(f):
        if kind in ('ok','err'):
            seq.append(1 if kind=='err' else 0)
    if len(seq)>=8:  # need enough trials for a runs test
        sessions[f]=seq

print(f"sessions with >=8 tool_results: {len(sessions)}")
tot=sum(len(v) for v in sessions.values())
errs=sum(sum(v) for v in sessions.values())
print(f"total tool_results: {tot}, total failures: {errs}, overall fail rate: {errs/tot:.3f}")

# Wald-Wolfowitz runs test per session: fewer runs than expected => clustering (overdispersion)
# Z = (R - mu_R)/sigma_R ; negative Z => clustered failures
def runs_stats(seq):
    n1=sum(seq); n0=len(seq)-n1
    if n1==0 or n0==0: return None
    R=1
    for i in range(1,len(seq)):
        if seq[i]!=seq[i-1]: R+=1
    n=n0+n1
    mu = 2*n0*n1/n + 1
    var = (2*n0*n1*(2*n0*n1-n))/(n*n*(n-1))
    if var<=0: return None
    z=(R-mu)/math.sqrt(var)
    return R, mu, z, n1, n

# Also dispersion index on fixed windows: variance/mean of failures-per-window
zs=[]
clustered=0; usable=0
disp_ratios=[]
for f,seq in sessions.items():
    rs=runs_stats(seq)
    if rs is None: continue
    R,mu,z,n1,n=rs
    usable+=1
    zs.append(z)
    if z< -1.0: clustered+=1
    # dispersion index, window=5
    w=5
    cnts=[sum(seq[i:i+w]) for i in range(0,len(seq)-w+1, w)]
    if len(cnts)>=2:
        m=sum(cnts)/len(cnts)
        if m>0:
            var=sum((c-m)**2 for c in cnts)/(len(cnts)-1)
            disp_ratios.append(var/m)

import statistics
print(f"\nusable sessions (both ok+err present): {usable}")
if zs:
    print(f"runs-test Z: mean={statistics.mean(zs):.3f} median={statistics.median(zs):.3f} (negative => clustered)")
    print(f"sessions with Z<-1 (clustered failures): {clustered}/{usable} = {clustered/usable:.2f}")
    neg=sum(1 for z in zs if z<0)
    print(f"sessions with Z<0 (any clustering tendency): {neg}/{usable} = {neg/usable:.2f}")
if disp_ratios:
    print(f"dispersion index (var/mean, window=5): mean={statistics.mean(disp_ratios):.3f} median={statistics.median(disp_ratios):.3f} (>1 => overdispersed/bursty, =1 Poisson)")

# Aggregate runs test combining sessions (Stouffer)
if zs:
    Z_comb=sum(zs)/math.sqrt(len(zs))
    print(f"\nStouffer combined Z across sessions: {Z_comb:.2f} (large negative => systematic clustering)")

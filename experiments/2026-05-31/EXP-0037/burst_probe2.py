import json, glob, collections, math, statistics

def iter_results(f):
    for line in open(f):
        line=line.strip()
        if not line: continue
        try: d=json.loads(line)
        except: continue
        msg=d.get('message')
        if isinstance(msg,dict) and isinstance(msg.get('content'),list):
            for b in msg['content']:
                if isinstance(b,dict) and b.get('type')=='tool_result':
                    txt=str(b.get('content'))[:300]
                    yield (1 if b.get('is_error') else 0, txt)

fs = glob.glob('/Users/dengcchi/.claude/projects/*/*.jsonl')

# What ARE the failures? classify by signature to see if clustering is web_disabled-carried
sig=collections.Counter()
for f in fs:
    for err,txt in iter_results(f):
        if err:
            t=txt.lower()
            if 'internet mode' in t or 'web' in t and 'enabl' in t: k='web_disabled'
            elif 'permission' in t or 'not allowed' in t or 'denied' in t: k='permission'
            elif 'no such file' in t or 'not found' in t or 'enoent' in t: k='file_notfound'
            elif 'timed out' in t or 'timeout' in t: k='timeout'
            elif 'string to replace' in t or 'no changes' in t or 'old_string' in t: k='edit_mismatch'
            else: k='other'
            sig[k]+=1
print("FAILURE SIGNATURES:", sig.most_common())

# Re-run runs test EXCLUDING web_disabled failures (treat them as non-failure / drop)
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

for mode in ['all','no_webdisabled']:
    zs=[]
    for f in fs:
        seq=[]
        for err,txt in iter_results(f):
            if mode=='no_webdisabled' and err and ('internet mode' in txt.lower() or ('web' in txt.lower() and 'enabl' in txt.lower())):
                seq.append(0)  # reclassify web_disabled as non-failure
            else:
                seq.append(err)
        if len(seq)>=8 and 0<sum(seq)<len(seq):
            z=runs_z(seq)
            if z is not None: zs.append(z)
    if zs:
        comb=sum(zs)/math.sqrt(len(zs))
        print(f"[{mode}] usable={len(zs)} meanZ={statistics.mean(zs):.3f} StoufferZ={comb:.2f}")

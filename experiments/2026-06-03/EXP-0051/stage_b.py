"""EXP-0051 Stage B — REAL model-pair maj@k ranking inversion under grader swap."""
import os, sys, json, re, random, collections, math
sys.path.insert(0,'/home/dengcchi/exp0051')
import canon
from canon import canon_numeric, canon_exact
import sympy

def gt_key(s):
    v=canon._to_value(s)
    if v is not None:
        try: return str(sympy.simplify(v))
        except: return str(v)
    return s.strip()

def extract(text):
    m=re.search(r'####\s*([\-\$0-9,\.\/]+)', text)
    if m: return m.group(1).strip().rstrip('.')
    m=re.search(r'(?:answer|total|result)[^\d\-\$]{0,15}(\$?\-?[0-9][0-9,\.\/]*)', text, re.I)
    if m: return m.group(1).strip().rstrip('.')
    nums=re.findall(r'\$?\-?\d[\d,]*\.?\d*', text)
    return nums[-1].strip().rstrip('.') if nums else ""

def majk_acc(per_problem_answers, golds, grader):
    correct=0
    for ans_list, gold in zip(per_problem_answers, golds):
        gk=gt_key(gold); votes=collections.Counter(); rep={}
        for a in ans_list:
            if a=="" : continue
            ck=grader(a); votes[ck]+=1; rep.setdefault(ck,a)
        if not votes: continue
        win_key,_=votes.most_common(1)[0]
        if gt_key(rep[win_key])==gk: correct+=1
    return correct/len(golds)

def main():
    random.seed(0)
    N_PROB=int(os.environ.get('NPROB','150')); K=int(os.environ.get('K','16')); TEMP=0.8
    MODELS=[("Qwen/Qwen2.5-0.5B-Instruct","qwen05"),
            ("Qwen/Qwen2.5-7B-Instruct","qwen7b")]
    probs=[]
    for line in open('/home/dengcchi/gsm8k_test.jsonl'):
        d=json.loads(line); m=re.search(r'####\s*(.+)\s*$', d['answer'].strip())
        if m: probs.append((d['question'], m.group(1).strip().replace(',','')))
    random.shuffle(probs); probs=probs[:N_PROB]
    print(f"[data] {len(probs)} GSM8K problems, k={K}, temp={TEMP}", flush=True)
    from vllm import LLM, SamplingParams
    PROMPT="Solve the math problem. Show brief reasoning, then end with '#### <final numeric answer>'.\n\nProblem: {q}\n\nSolution:"
    results={}
    for model_id, tag in MODELS:
        print(f"[load] {model_id}", flush=True)
        llm=LLM(model=model_id, gpu_memory_utilization=0.55, max_model_len=2048,
                enforce_eager=True, dtype="bfloat16")
        sp=SamplingParams(n=K, temperature=TEMP, top_p=0.95, max_tokens=512, seed=0)
        outs=llm.generate([PROMPT.format(q=q) for q,_ in probs], sp)
        results[tag]=[[extract(c.text) for c in o.outputs] for o in outs]
        del llm
        import gc, torch; gc.collect(); torch.cuda.empty_cache()
        print(f"[done] {tag}", flush=True)
    golds=[g for _,g in probs]; tags=[t for _,t in MODELS]
    print("\n=== STAGE B RESULTS (maj@k accuracy) ===", flush=True)
    acc={}
    for t in tags:
        ax=majk_acc(results[t],golds,canon_exact); an=majk_acc(results[t],golds,canon_numeric)
        acc[t]=(ax,an); print(f"  {t}: maj@k EXACT={ax:.3f}  NUMERIC={an:.3f}", flush=True)
    ta,tb=tags; ax,an=acc[ta]; bx,bn=acc[tb]
    print(f"\n  EXACT:  {ta}={ax:.3f} vs {tb}={bx:.3f} -> winner {ta if ax>bx else tb} (gap {ax-bx:+.3f})", flush=True)
    print(f"  NUMERIC:{ta}={an:.3f} vs {tb}={bn:.3f} -> winner {ta if an>bn else tb} (gap {an-bn:+.3f})", flush=True)
    inv=(ax>bx)!=(an>bn)
    print(f"\n  RANKING INVERSION under grader swap: {'YES' if inv else 'NO (null)'}", flush=True)
    # surface-diversity diagnostic per model
    for t in tags:
        nx=sum(len(set(canon_exact(a) for a in al if a))  for al in results[t])
        nn=sum(len(set(canon_numeric(a) for a in al if a)) for al in results[t])
        print(f"  [diag] {t}: total distinct EXACT buckets={nx}  NUMERIC buckets={nn} (collapse={nx-nn})", flush=True)
    with open('/home/dengcchi/exp0051/stage_b_summary.json','w') as f:
        json.dump({'n':len(golds),'k':K,'acc':acc,'inversion':inv,
                   'exact_gap':ax-bx,'numeric_gap':an-bn}, f, indent=2)
    # save raw extracted answers for audit
    with open('/home/dengcchi/exp0051/stage_b_raw.json','w') as f:
        json.dump({'golds':golds,'results':results}, f)
    print("[saved] stage_b_summary.json + raw", flush=True)
    sys.stdout.flush(); os._exit(0)

if __name__=='__main__':
    main()

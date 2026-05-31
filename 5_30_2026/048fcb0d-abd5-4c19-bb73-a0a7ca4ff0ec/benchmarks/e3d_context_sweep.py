"""
E3d — close CC4.8's gaps: (2) n>=3 context counts to claim a degradation pattern (not n=2),
(3) reconcile the K constant. Runs 1, 2, 3, 4 concurrent contexts on ONE clean GPU; each maps
to OOM; report per-context and TOTAL mappings. If total DROPS as contexts increase => confirmed
super-linear degradation with >=3 points.
"""
import sys, os, json, multiprocessing as mp
sys.path.insert(0,"<HOME>/branchable_replay/src")
def worker(q, cap=1_200_000):
    from cuda import cuda
    from vmm_pool import VMMPool, CudaCallError, _ck
    pool=VMMPool(device_id=0); pg=pool.create_phys_page()
    big=_ck(cuda.cuMemAddressReserve(pool.page_size*cap,0,0,0),call_site="reserve")
    n=0
    try:
        for n in range(cap):
            addr=int(big)+n*pool.page_size
            _ck(cuda.cuMemMap(addr,pool.page_size,0,pg.handle,0),call_site="cuMemMap")
            _ck(cuda.cuMemSetAccess(addr,pool.page_size,[pool._access],1),call_site="cuMemSetAccess")
    except CudaCallError as e:
        q.put(n); return
    q.put(n)
def run_n(nctx):
    q=mp.Queue(); ps=[mp.Process(target=worker,args=(q,)) for _ in range(nctx)]
    for p in ps:p.start()
    res=[q.get() for _ in ps]
    for p in ps:p.join()
    return sorted(res), sum(res)
if __name__=="__main__":
    mp.set_start_method("spawn")
    n=int(sys.argv[1])
    per,total=run_n(n)
    print(json.dumps({"n_contexts":n,"per_context":per,"total":total,"avg":total//n}))

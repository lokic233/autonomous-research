"""
E3a — NT1 root-cause: WHAT does the K~520K ceiling actually count? (H100, SAFE: stops at OOM)
Competing hypotheses for what the driver caps:
  H1: # of cuMemMap operations (mapping descriptors)
  H2: # of distinct VA reservations (cuMemAddressReserve)
  H3: total mapped BYTES (a VA-space or page-table-size limit)
  H4: # of (VA-page -> phys-handle) access descriptors set by cuMemSetAccess
Design: hold ONE physical page, alias it into many VA pages (1 reserve, many maps) and see
where it fails -> isolates map/setaccess count from reservation count. Then repeat reserving
ONE big VA range and mapping within it (few reserves) vs many small reserves.
Compares which call OOMs (forensic call_site) and at what count, across 3 regimes.
"""
import sys, os, json
sys.path.insert(0,"<HOME>/branchable_replay/src")
from cuda import cuda
from vmm_pool import VMMPool, CudaCallError, _ck

def regime(name, mode, cap=2_000_000):
    """mode: 'many_reserve_one_map' | 'one_reserve_many_map' | 'big_pages'"""
    pool = VMMPool(device_id=0)
    pg = pool.create_phys_page()  # ONE shared physical page, aliased many times
    n=0; fail=None; va_reserves=0
    try:
        if mode=="one_reserve_many_map":
            # reserve a huge VA range once, map the shared page into each slot
            big = _ck(cuda.cuMemAddressReserve(pool.page_size*cap, 0, 0, 0), call_site="reserve_big")
            va_reserves=1
            for n in range(cap):
                addr = int(big)+n*pool.page_size
                _ck(cuda.cuMemMap(addr, pool.page_size, 0, pg.handle, 0), call_site="cuMemMap")
                _ck(cuda.cuMemSetAccess(addr, pool.page_size, [pool._access], 1), call_site="cuMemSetAccess")
                if n and n%100000==0: print(f"  {name}: {n}", flush=True)
        else:  # many_reserve_one_map : one reserve + one map each
            for n in range(cap):
                va = _ck(cuda.cuMemAddressReserve(pool.page_size,0,0,0), call_site="cuMemAddressReserve"); va_reserves+=1
                _ck(cuda.cuMemMap(va, pool.page_size, 0, pg.handle, 0), call_site="cuMemMap")
                _ck(cuda.cuMemSetAccess(va, pool.page_size, [pool._access],1), call_site="cuMemSetAccess")
                if n and n%100000==0: print(f"  {name}: {n}", flush=True)
    except CudaCallError as e:
        fail={"count":n,"oom_call":e.call_site,"is_oom":e.is_oom,"err":str(e)[:80]}
    except Exception as e:
        fail={"count":n,"err":repr(e)[:120]}
    return {"regime":name,"mode":mode,"mappings_before_fail":n,"va_reserves":va_reserves,"fail":fail}

if __name__=="__main__":
    import sys
    mode=sys.argv[1]; name=sys.argv[2]
    r=regime(name,mode)
    print(json.dumps(r))

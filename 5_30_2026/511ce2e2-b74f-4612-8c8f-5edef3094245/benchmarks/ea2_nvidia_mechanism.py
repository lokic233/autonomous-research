#!/usr/bin/env python3
"""
E-A2: Mechanism probe for the NVIDIA CUDA-VMM ~520K mapping ceiling.
CC48's objection: is 520K a FIXED table size, a METADATA-MEMORY function, or tunable?
Test: map a single 2MiB physical page into N distinct VA slots (the CoW-alias case) and
find where cuMemSetAccess fails. Then repeat with MANY distinct physical handles to see if
the ceiling is per-MAPPING (constant ~520K regardless of #phys handles) or per-BYTE.
If K is ~constant across both regimes => fixed mapping-table-entry ceiling (not data-memory).
"""
import sys
from cuda.bindings import driver as cuda

def ck(err, *a):
    if isinstance(err, tuple): err=err[0]
    if err != cuda.CUresult.CUDA_SUCCESS:
        raise RuntimeError(f"CUDA err {err}")

def init():
    ck(cuda.cuInit(0))
    dev = cuda.cuDeviceGet(0)[1]
    ctx = cuda.cuDevicePrimaryCtxRetain(dev)[1]
    cuda.cuCtxSetCurrent(ctx)
    return dev, ctx

def granularity(dev):
    prop = cuda.CUmemAllocationProp()
    prop.type = cuda.CUmemAllocationType.CU_MEM_ALLOCATION_TYPE_PINNED
    prop.location.type = cuda.CUmemLocationType.CU_MEM_LOCATION_TYPE_DEVICE
    prop.location.id = dev
    gran = cuda.cuMemGetAllocationGranularity(prop,
        cuda.CUmemAllocationGranularity_flags.CU_MEM_ALLOC_GRANULARITY_MINIMUM)[1]
    return prop, gran

def probe(dev, prop, gran, shared_phys, cap):
    """Map into 'cap' VA slots. If shared_phys: 1 phys handle aliased; else 1 phys per slot
       (until we run out of HBM). Returns (mappings_before_fail, fail_call)."""
    adesc = cuda.CUmemAccessDesc()
    adesc.location.type = cuda.CUmemLocationType.CU_MEM_LOCATION_TYPE_DEVICE
    adesc.location.id = dev
    adesc.flags = cuda.CUmemAccess_flags.CU_MEM_ACCESS_FLAGS_PROT_READWRITE
    # reserve VA range
    va = cuda.cuMemAddressReserve(cap*gran, 0, 0, 0)
    if va[0] != cuda.CUresult.CUDA_SUCCESS:
        return 0, f"VA_RESERVE_FAIL(cap={cap})"
    base = va[1]
    phys_shared = None
    if shared_phys:
        h = cuda.cuMemCreate(gran, prop, 0)
        ck(h); phys_shared = h[1]
    mapped=0; fail="none"
    for i in range(cap):
        slot = int(base) + i*gran
        if shared_phys:
            ph = phys_shared
        else:
            hc = cuda.cuMemCreate(gran, prop, 0)
            if hc[0] != cuda.CUresult.CUDA_SUCCESS:
                fail=f"cuMemCreate(HBM_exhausted)@{mapped}"; break
            ph = hc[1]
        e1 = cuda.cuMemMap(slot, gran, 0, ph, 0)
        if e1[0] != cuda.CUresult.CUDA_SUCCESS:
            fail=f"cuMemMap@{mapped}"; break
        e2 = cuda.cuMemSetAccess(slot, gran, [adesc], 1)
        if e2[0] != cuda.CUresult.CUDA_SUCCESS:
            fail=f"cuMemSetAccess@{mapped}"; break
        mapped+=1
        if mapped % 100000 == 0:
            print(f"    ...{mapped} mappings ok (shared={shared_phys})", flush=True)
    return mapped, fail

def main():
    dev, ctx = init()
    prop, gran = granularity(dev)
    print(f"GRANULARITY={gran} bytes ({gran/1048576:.2f} MiB)", flush=True)
    # Regime 1: 1 shared physical page aliased into many VAs (pure mapping-metadata test)
    print("=== REGIME 1: shared phys (1 page), alias into many VAs ===", flush=True)
    m1, f1 = probe(dev, prop, gran, shared_phys=True, cap=1200000)
    print(f"REGIME1_CEILING={m1}  fail={f1}  (HBM used = 1 page = {gran/1048576:.0f}MiB)", flush=True)
    print(f"RESULT: shared_alias_ceiling={m1}", flush=True)

if __name__=="__main__":
    main()

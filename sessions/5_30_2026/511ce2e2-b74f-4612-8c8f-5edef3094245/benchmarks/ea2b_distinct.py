#!/usr/bin/env python3
"""E-A2b: isolate the mechanism. Does the ceiling differ for shared-handle aliasing vs
distinct-handle mapping? Repo measured 520K with DISTINCT handles (real prefix pages).
My shared-handle probe got 5637. Run distinct-handle here (1 phys per VA, until HBM or
mapping ceiling), and also shared-handle but using PER-BRANCH contiguous reservations
(mimicking the repo) to see which variable controls the limit."""
import sys
from cuda.bindings import driver as cuda
def ck(e):
    if isinstance(e,tuple): e=e[0]
    if e!=cuda.CUresult.CUDA_SUCCESS: raise RuntimeError(f"CUDA {e}")
ck(cuda.cuInit(0)); dev=cuda.cuDeviceGet(0)[1]
ctx=cuda.cuDevicePrimaryCtxRetain(dev)[1]; cuda.cuCtxSetCurrent(ctx)
prop=cuda.CUmemAllocationProp()
prop.type=cuda.CUmemAllocationType.CU_MEM_ALLOCATION_TYPE_PINNED
prop.location.type=cuda.CUmemLocationType.CU_MEM_LOCATION_TYPE_DEVICE
prop.location.id=dev
gran=cuda.cuMemGetAllocationGranularity(prop,
    cuda.CUmemAllocationGranularity_flags.CU_MEM_ALLOC_GRANULARITY_MINIMUM)[1]
ad=cuda.CUmemAccessDesc()
ad.location.type=cuda.CUmemLocationType.CU_MEM_LOCATION_TYPE_DEVICE
ad.location.id=dev; ad.flags=cuda.CUmemAccess_flags.CU_MEM_ACCESS_FLAGS_PROT_READWRITE
print(f"GRAN={gran} ({gran/1048576:.0f}MiB)",flush=True)

# REGIME 2: repo-style. P distinct phys pages, each branch = 1 contiguous VA reserve of P
# pages, map the P distinct handles, setaccess. Count branches until cuMemSetAccess fails.
# Use small P=512 (1GiB) so HBM (97GiB) isn't the binding constraint at the mapping ceiling.
P=512
# create P distinct physical handles ONCE (the shared "prefix"); aliasing them across branches
phys=[]
for i in range(P):
    h=cuda.cuMemCreate(gran,prop,0)
    if h[0]!=cuda.CUresult.CUDA_SUCCESS: 
        print(f"phys create fail @{i}"); break
    phys.append(h[1])
print(f"created {len(phys)} distinct phys pages ({len(phys)*gran/1048576:.0f}MiB live)",flush=True)
branches=0; total_map=0; fail="none"
reserves=[]
for b in range(5000):
    va=cuda.cuMemAddressReserve(P*gran,0,0,0)
    if va[0]!=cuda.CUresult.CUDA_SUCCESS: fail=f"VA_RESERVE@branch{b}"; break
    base=va[1]; reserves.append(base)
    ok=True
    for j in range(P):
        slot=int(base)+j*gran
        if cuda.cuMemMap(slot,gran,0,phys[j],0)[0]!=cuda.CUresult.CUDA_SUCCESS:
            fail=f"cuMemMap@branch{b}page{j}(total={total_map})"; ok=False; break
        if cuda.cuMemSetAccess(slot,gran,[ad],1)[0]!=cuda.CUresult.CUDA_SUCCESS:
            fail=f"cuMemSetAccess@branch{b}page{j}(total={total_map})"; ok=False; break
        total_map+=1
    if not ok: break
    branches+=1
    if branches%200==0: print(f"  branch {branches}, total_mappings {total_map}",flush=True)
print(f"REGIME2_DISTINCT: branches={branches} P={P} total_mappings={total_map} K_product={branches*P} fail={fail}",flush=True)
print(f"RESULT: distinct_handle_ceiling_total_mappings={total_map} branches={branches}",flush=True)

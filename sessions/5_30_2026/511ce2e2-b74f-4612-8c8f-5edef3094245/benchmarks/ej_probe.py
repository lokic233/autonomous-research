#!/usr/bin/env python3
"""E-J pre-flight: is cuMemRetainAllocationHandle a forge-resistant physical identifier or a
fabricable userspace integer? This decides whether Candidate J lives. Bounded allocations."""
import sys
from cuda.bindings import driver as cuda
def ck(e,what=""):
    if isinstance(e,tuple): 
        if e[0]!=cuda.CUresult.CUDA_SUCCESS: raise RuntimeError(f"{what}:{e[0]}")
        return e[1] if len(e)>1 else None
    if e!=cuda.CUresult.CUDA_SUCCESS: raise RuntimeError(f"{what}:{e}")
ck(cuda.cuInit(0)); dev=ck(cuda.cuDeviceGet(0),"devget")
ctx=ck(cuda.cuDevicePrimaryCtxRetain(dev),"ctx"); cuda.cuCtxSetCurrent(ctx)
prop=cuda.CUmemAllocationProp()
prop.type=cuda.CUmemAllocationType.CU_MEM_ALLOCATION_TYPE_PINNED
prop.location.type=cuda.CUmemLocationType.CU_MEM_LOCATION_TYPE_DEVICE
prop.location.id=dev
gran=ck(cuda.cuMemGetAllocationGranularity(prop,cuda.CUmemAllocationGranularity_flags.CU_MEM_ALLOC_GRANULARITY_MINIMUM),"gran")
ad=cuda.CUmemAccessDesc(); ad.location.type=cuda.CUmemLocationType.CU_MEM_LOCATION_TYPE_DEVICE
ad.location.id=dev; ad.flags=cuda.CUmemAccess_flags.CU_MEM_ACCESS_FLAGS_PROT_READWRITE

def reserve_map(phys):
    va=ck(cuda.cuMemAddressReserve(gran,0,0,0),"reserve")
    ck(cuda.cuMemMap(va,gran,0,phys,0),"map"); ck(cuda.cuMemSetAccess(va,gran,[ad],1),"sa")
    return va

# Two distinct physical pages + one shared alias
pA=ck(cuda.cuMemCreate(gran,prop,0),"createA")
pB=ck(cuda.cuMemCreate(gran,prop,0),"createB")
vA=reserve_map(pA); vA2=reserve_map(pA); vB=reserve_map(pB)  # vA,vA2 alias pA; vB distinct

hA  = int(ck(cuda.cuMemRetainAllocationHandle(vA),"rA"))
hA2 = int(ck(cuda.cuMemRetainAllocationHandle(vA2),"rA2"))
hB  = int(ck(cuda.cuMemRetainAllocationHandle(vB),"rB"))
print(f"handle(vA)={hA}")
print(f"handle(vA2)={hA2}  [aliases vA: should EQUAL]")
print(f"handle(vB)={hB}   [distinct: should DIFFER]")
print(f"ALIAS_DETECT: vA==vA2 ? {hA==hA2}   vA==vB ? {hA==hB}")

# FORGE TEST 1: is the handle a stable physical ID or does it change across re-retain?
hA_again=int(ck(cuda.cuMemRetainAllocationHandle(vA),"rA_again"))
print(f"FORGE1 re-retain stable? {hA==hA_again} (hA_again={hA_again})")

# FORGE TEST 2: what IS the value — compare to the original cuMemCreate handle int
print(f"FORGE2 retained_handle == original cuMemCreate handle(pA)? {hA==int(pA)} (pA={int(pA)})")

# FORGE TEST 3: can an untrusted party FABRICATE a matching handle without the driver?
# The handle is a CUmemGenericAllocationHandle (an opaque driver ref). Key question: is it a
# per-process opaque ref (forgeable by reuse) or globally meaningful? Test: does releasing and
# recreating give a colliding handle value (=> just a recycled slot => forgeable)?
ck(cuda.cuMemRelease(cuda.CUmemGenericAllocationHandle(hA)),"relA")  # release retained ref
pC=ck(cuda.cuMemCreate(gran,prop,0),"createC")
print(f"FORGE3 new handle(pC)={int(pC)} collides with freed hA({hA})? {int(pC)==hA} (slot-recycle => userspace-ish)")
print("VERDICT_INPUTS: see above — equal-for-alias + differ-for-distinct is the PROOF; forge tests gauge robustness.")

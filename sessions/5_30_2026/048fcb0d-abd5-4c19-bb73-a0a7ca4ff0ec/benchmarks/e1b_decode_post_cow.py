"""
E1b — NT3 GREEN-gating experiment (H100-only, SAFE: 1 layer, 3-page prefix).
Claim: after a write-after-share CoW on a forked branch, UNMODIFIED SDPA/FlashAttention runs
on that branch THROUGH THE SAME CONTIGUOUS VA and produces bit-identical attention output to a
full-clone branch that received the identical edit. (The decode-correctness number the
committee demanded for GREEN — proves "unmodified FlashAttention works post-CoW", not a proxy.)
"""
import sys, os, json
sys.path.insert(0, "<HOME>/branchable_replay/src")
import torch
torch.cuda.init(); torch.cuda.set_device(0); _=torch.zeros(8,device="cuda"); torch.cuda.synchronize()
from kv_branch_manager import KVBranchManager
from decode_layer import QwenLayerN, BranchKV

R={"experiment":"E1b_unmodified_SDPA_decode_post_write_after_share_CoW"}
L = QwenLayerN(num_layers=1)
n_kv, hd = L.n_kv, L.hd
mgr = KVBranchManager(device_id=0)
toks_per_page = mgr.page_size // (n_kv*hd*2)
prefix_tokens = toks_per_page * 3
HR=8
mgr.create_branch("pK",1,headroom_pages=HR); mgr.create_branch("pV",1,headroom_pages=HR)
p = BranchKV(mgr,n_kv,hd,"pK","pV",reset=True)
h_tok=1234
for pos in range(prefix_tokens):
    hh=L.embed[h_tok].clone(); q,k,v=L.project(0,hh,pos); p.append_token(k,v)
    hh=L.attend_mlp(0,hh,q,p.k_view(),p.v_view()); h_tok=int(L.logits_of(hh).argmax())
torch.cuda.synchronize()
R["prefix_tokens"]=prefix_tokens; R["prefix_pages"]=mgr.branches["pK"].num_pages

snapK=mgr.snapshot("pK"); snapV=mgr.snapshot("pV")
# Branch CoW: fork a child that aliases the prefix
mgr.fork(snapK,"cK",headroom_pages=HR); mgr.fork(snapV,"cV",headroom_pages=HR)
child = BranchKV(mgr,n_kv,hd,"cK","cV",reset=False); child.seq=prefix_tokens

# Full-clone reference: deep-copy the prefix KV into ordinary contiguous tensors
ref_K = p.k_view().clone().contiguous()   # [n_kv, seq, hd]
ref_V = p.v_view().clone().contiguous()

# --- the EDIT: overwrite a shared interior prefix token (write-after-share) on BOTH paths ---
target_pos = toks_per_page + 5            # lands in shared page 1
edit_tok = 777
hh=L.embed[edit_tok].clone(); qe,ke,ve=L.project(0,hh,target_pos)
# CoW path: write the new k/v at target_pos via the manager (fires _cow on the shared page)
va_before = [mgr.branches["cK"].va_of(i) for i in range(mgr.branches["cK"].num_pages)]
cow_before = mgr.pool.stat_cow_events
# write into the contiguous VA view at the target position (this dirties the shared page -> CoW)
child._ensure_private("cK", target_pos // toks_per_page)
child._ensure_private("cV", target_pos // toks_per_page)
kc = child.k_view(); vc = child.v_view()
kc[:, target_pos, :] = ke.to(kc.dtype); vc[:, target_pos, :] = ve.to(vc.dtype)
torch.cuda.synchronize()
cow_after = mgr.pool.stat_cow_events
va_after = [mgr.branches["cK"].va_of(i) for i in range(mgr.branches["cK"].num_pages)]
# reference path: identical edit on the clone tensors
ref_K[:, target_pos, :] = ke.to(ref_K.dtype); ref_V[:, target_pos, :] = ve.to(ref_V.dtype)

# --- run UNMODIFIED SDPA on BOTH, at a fresh query, compare bit-exact ---
qpos = prefix_tokens
hq = L.embed[321].clone(); qq,_,_ = L.project(0, hq, qpos)
out_cow = L.attend_mlp(0, hq.clone(), qq, child.k_view(), child.v_view())
out_ref = L.attend_mlp(0, hq.clone(), qq, ref_K, ref_V)
torch.cuda.synchronize()

bit_identical = torch.equal(out_cow, out_ref)
max_abs = float((out_cow.float()-out_ref.float()).abs().max())
R["forkedkv_post_cow"]={
  "cow_fired": (cow_after-cow_before)>=1,
  "cow_events": cow_after-cow_before,
  "branch_VA_unchanged_after_CoW": va_before==va_after,
  "sdpa_output_bit_identical_to_full_clone": bool(bit_identical),
  "max_abs_diff_vs_clone": max_abs,
  "kernel_modified": False,   # same L.attend_mlp / SDPA for both; no block-table path
}
R["verdict_NT3_E2E"]= bool(bit_identical) and (cow_after-cow_before)>=1 and (va_before==va_after)
print(json.dumps(R,indent=2)); json.dump(R,open("e1b_result.json","w"),indent=2)

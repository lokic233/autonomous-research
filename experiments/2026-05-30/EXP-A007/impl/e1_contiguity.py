"""
E1 — NT3 gating experiment (H100-only, SAFE: <10 pages, no stress sweep).
Claim under test: ForkedKV's VMM page-aliasing preserves a CONTIGUOUS virtual address per
branch EVEN AFTER write-after-share CoW, while a vLLM-APC-style block table cannot (the CoW'd
block lands at an arbitrary pool slot => non-contiguous => mandatory block-table indirection).
This is the falsifiable delta vs vAttention (read-only contiguous VA, no fork/CoW) and APC.
"""
import sys, json
sys.path.insert(0, "/home/dengcchi/branchable_replay/src")
from kv_branch_manager import KVBranchManager

R = {"experiment":"E1_contiguity_under_write_after_share"}

# ---- ForkedKV (CUDA VMM) ----
m = KVBranchManager(device_id=0, max_pages_per_branch=64)
P = 4  # 4-page shared prefix (tiny, safe)
m.create_branch("parent", P); m.fill_prefix("parent", P, fill_value=7)
snap = m.snapshot("parent")
m.fork(snap, "childA"); m.fork(snap, "childB")

# VA contiguity BEFORE write
va_A = [m.branches["childA"].va_of(i) for i in range(P)]
contig_before = all(va_A[i+1]-va_A[i] == m.page_size for i in range(P-1))

# all 3 alias page 2 (shared)?
shared_before = (m.shared_handle("parent","childA",2) and m.shared_handle("childA","childB",2))

# childA OVERWRITES shared page 2 (write-after-share -> CoW)
m.write_page("childA", 2, fill_value=99)

# VA contiguity AFTER write (the key claim: STILL contiguous)
va_A2 = [m.branches["childA"].va_of(i) for i in range(P)]
contig_after = all(va_A2[i+1]-va_A2[i] == m.page_size for i in range(P-1))
va_unchanged = (va_A == va_A2)   # the branch's VA addresses didn't move

# correctness: only page 2 diverged; siblings B & parent still aliased & unchanged
diverged = m.diverged_pages("childA","childB")
B_parent_still_shared = m.shared_handle("childB","parent",2)
other_pages_still_shared = all(m.shared_handle("childA","childB",i) for i in [0,1,3])

R["forkedkv"] = {
  "prefix_pages": P,
  "contiguous_VA_before_write": contig_before,
  "contiguous_VA_after_write":  contig_after,
  "branch_VA_unchanged_after_CoW": va_unchanged,
  "shared_before_write": bool(shared_before),
  "diverged_pages_after_write": diverged,
  "sibling_B_and_parent_still_aliased": bool(B_parent_still_shared),
  "untouched_pages_still_aliased": bool(other_pages_still_shared),
  "page_size_bytes": m.page_size,
}
m.destroy_branch("childA"); m.destroy_branch("childB"); m.destroy_branch("parent")
print(json.dumps(R, indent=2))
json.dump(R, open("e1_result.json","w"), indent=2)

# ---- vLLM-APC-style software baseline (block table) ----
from baseline_prefix_sharing import SoftwarePrefixSharingManager
sw = SoftwarePrefixSharingManager(n_blocks=64, block_bytes=2*1024*1024)
sw.create_filled_branch("parent", P)
sw.fork("parent","childA"); sw.fork("parent","childB")
bt_before = list(sw.branches["childA"])           # physical block ids, logical order
# is the block table contiguous in physical-slot space? (the property a kernel would need
# to treat it as a flat tensor without indirection)
sw_contig_before = all(bt_before[i+1]-bt_before[i]==1 for i in range(P-1))
sw.write_block("childA", 2)                        # CoW on shared logical block 2
bt_after = list(sw.branches["childA"])
sw_contig_after = all(bt_after[i+1]-bt_after[i]==1 for i in range(P-1))
sw_bt_moved = (bt_before != bt_after)

R["software_apc"] = {
  "block_table_before": bt_before,
  "block_table_after_CoW": bt_after,
  "phys_contiguous_before": sw_contig_before,
  "phys_contiguous_after_CoW": sw_contig_after,
  "block_table_entry_moved_on_CoW": sw_bt_moved,
  "requires_block_table_indirection": True,  # by construction: kernel must gather via bt[]
}

R["verdict"] = {
  "forkedkv_keeps_contiguous_VA_after_write_after_share":
      R["forkedkv"]["contiguous_VA_after_write"] and R["forkedkv"]["branch_VA_unchanged_after_CoW"],
  "software_apc_loses_contiguity_after_CoW":
      (not R["software_apc"]["phys_contiguous_after_CoW"]) or R["software_apc"]["block_table_entry_moved_on_CoW"],
  "NT3_delta_demonstrated": None,  # filled below
}
R["verdict"]["NT3_delta_demonstrated"] = (
    R["verdict"]["forkedkv_keeps_contiguous_VA_after_write_after_share"]
    and R["verdict"]["software_apc_loses_contiguity_after_CoW"]
)
print(json.dumps(R, indent=2))
json.dump(R, open("e1_result.json","w"), indent=2)

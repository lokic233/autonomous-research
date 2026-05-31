# E1 RESULT — NT3 gating experiment (H100-only, SAFE: 4 pages, no stress)
Date: 2026-05-30. Node: <GPU-NODE-A> (H100), branchable_replay/.venv. Tiny footprint (<10 MiB).

## Claim under test (NT3)
ForkedKV's GPU-MMU page-aliasing preserves a CONTIGUOUS virtual address per branch EVEN AFTER
write-after-share CoW; a vLLM-APC-style block table cannot (CoW'd block moves to an arbitrary
pool slot => mandatory block-table indirection). This is the delta vs vAttention (read-only
contiguous VA, no fork/CoW) and vLLM APC.

## Measured (e1_result.json)
| Property | ForkedKV (CUDA VMM) | vLLM-APC (block table) |
|---|---|---|
| contiguous addr BEFORE write | YES | NO (slots [63,62,61,60]) |
| **contiguous addr AFTER write-after-share CoW** | **YES (VA unchanged)** | **NO (entry 61->59, table [63,62,59,60])** |
| only written page/block diverges | YES (page [2]) | YES (block 2) |
| siblings+parent stay aliased bit-identical | YES | YES |
| kernel needs block-table indirection | **NO** | **YES (by construction)** |

## Verdict
- forkedkv_keeps_contiguous_VA_after_write_after_share = TRUE
- software_apc_loses_contiguity_after_CoW = TRUE
- **NT3_delta_demonstrated = TRUE**

Both mechanisms fork+CoW correctly (so "we have CoW" is NOT the delta — that would be dead
territory). The surviving, measured delta is: ForkedKV's branch VA is INVARIANT under CoW (MMU
repoints one physical page beneath a fixed VA); APC's logical->physical block mapping MOVES,
forcing per-token gather. That is the kernel-transparency property vAttention/APC cannot provide
under write-after-share. This is the empirical evidence the committee demanded ("prove vAttention
CANNOT express it") at the mechanism level.

## Honest scope
- This proves the ADDRESS-SPACE property (VA invariance vs block-table move), not yet an
  end-to-end FlashAttention-runs-unmodified-post-CoW decode. That E2E demo (NT3's full 30-day
  ask) is the next step; this is the core falsifiable kernel-transparency claim, done safely.
- vAttention comparison is structural/by-construction (vAttention is read-only per-request, has
  no fork primitive); a literal vAttention integration would strengthen but isn't required to
  show the capability gap.
Artifacts: ~/committee_gen_e1/e1_contiguity.py, e1_result.json.

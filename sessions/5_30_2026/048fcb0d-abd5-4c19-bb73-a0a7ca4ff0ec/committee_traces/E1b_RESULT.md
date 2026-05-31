# E1b RESULT — NT3 GREEN-gating experiment (H100-only, SAFE: 1 layer, 3-page prefix)
Date: 2026-05-30. Node: <GPU-NODE-A> (H100). Real Qwen2.5-7B layer-0, real SDPA.

## Claim under test (the YELLOW->GREEN gap from the NT3 re-vote)
"Unmodified FlashAttention/SDPA works on a forked branch AFTER write-after-share CoW" — the
payload claim 4 of 5 agents said needed an actual E2E decode-correctness number, not the
VA-invariance proxy from E1.

## Method
3-page (6,144-token) real-forward prefix → fork child (aliases prefix, zero copy) → child
overwrites a SHARED interior prefix token (pos = toks_per_page+5) triggering CoW → run the SAME
unmodified L.attend_mlp (SDPA) on (a) the post-CoW branch via its contiguous VA view and (b) a
full-clone reference tensor that got the identical edit → compare bit-exact.

## Measured (e1b_result.json)
- cow_fired: TRUE (2 events: K page + V page)
- branch_VA_unchanged_after_CoW: TRUE (contiguous-VA invariant holds through CoW)
- sdpa_output_bit_identical_to_full_clone: TRUE
- max_abs_diff_vs_clone: 0.0
- kernel_modified: FALSE (identical SDPA path for both; no block-table gather)
- verdict_NT3_E2E: TRUE

## Significance
E1 proved the address-space property (VA invariant; APC block-table moves). E1b now proves the
FUNCTIONAL consequence: an UNMODIFIED attention kernel decodes BIT-IDENTICAL output on the
post-CoW branch through the unchanged contiguous VA (max_abs_diff 0.0). This is the exact
evidence CC4.8/CC4.7/Codex/Gemini required for GREEN. vLLM-APC cannot match this without a
block-table-aware kernel (E1 showed its mapping moves under CoW).
Artifacts: ~/committee_gen_e1b/e1b_decode_post_cow.py, e1b_result.json.

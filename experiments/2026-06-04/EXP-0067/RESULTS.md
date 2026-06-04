# RESULTS — EXP-0067 / CLAIM-0058
**Researcher:** researcher-0064 · **Project:** PROJ-0028 · **Verdict: HELD (support, with a precise scope condition)**
**Level:** L0 (CPU-only, stdlib pure-Python Aho-Corasick, SERIAL, 16.1 s wall) · 5 seeds × N=30,000 completions each.
Prereg committed BEFORE run (HEAD e905de4). Harness owns GT; the filter never reads GT.

## Headline
The token-flush CHUNK GRANULARITY causally degrades the recall of an incremental output safety
filter on multi-token policy-violating phrases — **and the loss survives against the PRODUCTION
sliding-window-with-overlap moderator at a realistic default window (W=16)**, not just the naive
stateless scanner. At W=16, multi-token recall falls from 100% (small chunks) to **57.3%** at the
production-scale chunk size C=32 — a **42.7pp** drop. Recall recovers to ~100% only when the window
**W ≥ ~2·C** (W=16 heals C=8; C=16 needs W=32; C=32 needs W=64) — i.e. the window must exceed the
chunk size by the max-phrase-length, a coupling the latency-tuning runtime team sets blind.

## Sanity ceiling (alias control B) — PASSED
Unbounded-rescan / whole-text scan = **100.0% recall at every chunk size C∈{1..32}**, 0 false
positives on benign+decoy completions. -> any recall loss is streaming FRAGMENTATION, not filter
weakness or phrase difficulty. Completion text is byte-identical across all C (only flush boundaries
move) — alias control A holds by construction.

## Recall vs chunk-size C, per moderator arm (multi-token phrases, mean over 5 seeds, % )
| Arm | C=1 | C=2 | C=4 | C=8 | C=16 | C=32 |
|-----|-----|-----|-----|-----|------|------|
| (a) stateless-per-delta | 0.0 | 18.8 | 54.3 | 78.4 | 90.5 | 97.1 |
| (b) ★ sliding-window W=16 (PRODUCTION) | 100.0 | 100.0 | 100.0 | 100.0 | 95.5 | 57.3 |
| (c) unbounded-rescan (ceiling) | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |

- **Stateless** recall is LOW at small C (C=1 → 0%: every token is its own delta, no multi-token
  phrase is ever seen intact) and *rises* with C (large chunk often contains the whole phrase). This
  is the naive worst case and is the wrong knob direction to reason about — hence the production arm.
- **★ Sliding-window W=16** (the decisive arm): 100% for C≤8, **95.5% at C=16, 57.3% at C=32**.
  As soon as the chunk size approaches/exceeds the window, boundary-straddling phrases fall in the
  blind spot between what the window retains and the next chunk. **Material (>15pp) loss at
  production chunk sizes against the production baseline.**

## ★ THE OVERLAP RECOVERY POINT (decisive measurement) — multi-token recall vs window W (%)
| | W=0(stateless) | W=2 | W=4 | W=8 | W=16 | W=32 | W=64 |
|--|--|--|--|--|--|--|--|
| C=8  | 78.4 | 5.2 | 29.9 | 82.5 | 100.0 | 100.0 | 100.0 |
| C=16 | 90.5 | 2.9 | 16.5 | 46.2 | 95.5 | 100.0 | 100.0 |

**Recovery point W\*** (smallest W with recall≥99%): **C=8 → W\*=16 ; C=16 → W\*=32.**
Empirically **W\* ≈ 2·C** (the window must hold the current chunk PLUS a full-chunk lookback so any
phrase straddling the latest flush boundary lands inside one re-scanned window). Critically: a
realistic *small* default overlap (W=8) does **NOT** heal it (46% at C=16) — so this is **not** a
WEAKEN. The seam is healed only when the runtime team happens to set W ≥ 2·C, which requires
knowing both the chunk size AND the safety max-phrase-length — exactly the cross-org coupling the
claim predicts they lack.

## Phrase-length moderation control (alias control C; stateless arm, fixed C=8, %)
| phrase_len | 1 (NULL control) | 2 | 3 | 4 |
|--|--|--|--|--|
| recall | 100.0 | 88.5 | 77.1 | 65.3 |

1-token phrases = **100%** (cannot be fragmented — null control passes). Recall falls monotonically
with phrase length (88.5 → 77.1 → 65.3%). **Phrase length is the confirmed effect-moderator** — the
loss is specifically multi-token fragmentation, exactly the mechanism in the claim.

## NULL exit — DID NOT trigger
The genuine null exit (stateless multi-token recall flat across C) did NOT fire: stateless recall
spans 0%→97% across C (huge fragmentation effect), and the production arm shows a 42.7pp drop. The
effect is real and large, so we report HELD honestly — but note the *direction* nuance: the danger
zone is LARGE chunks vs the window, not small chunks (small chunks fragment so badly that even
stateless misses everything; the production window heals small chunks but breaks at C≳W).

## VERDICT: HELD (support)
Per the prereg decision rule: the production sliding-window arm at a realistic default overlap
(W=16) shows **material (42.7pp > 15pp) multi-token recall loss at production chunk size C=32**,
recovering to ~100% only at **W ≥ 2·C** — a window the latency-conscious runtime team would not pick
without knowing the safety max-phrase-length and reconciling it with the chunk schedule. This is the
predicted cross-seam coupling: a latency-tuning runtime knob silently lowering safety recall via
benign span fragmentation across the org boundary. **NOT a WEAKEN** — a small default overlap does
not heal it.

## Files
- PRE_REGISTRATION.md (committed pre-run, HEAD e905de4)
- harness.py · run_all.py · run_all.log · summary.json
- recall_by_chunk_arm.csv · recall_by_overlap.csv · recall_by_phraselen.csv

## What L1 should measure
Real vLLM/TGI SSE at varying `output_token_chunk` / scheduler flush granularity × a REAL streaming
moderator (Llama-Guard-streaming / OpenAI-Moderation incremental) on a real red-team multi-token
violation set. Confirm: (1) recall vs flush granularity for the production sliding-window moderator;
(2) the recovery condition — does W ≥ chunk_size + max_phrase_len heal it on real tokenization
(subword BPE may split a "phrase" into many more tokens than the 2-4 here, *widening* the gap);
(3) whether real moderators re-scan a window in *characters/subtokens* vs words (changes W\*). The L0
prediction: the seam is real and its fix requires the runtime to set W as a function of BOTH its own
chunk size and the safety team's max-phrase token-length — a parameter neither side owns alone.

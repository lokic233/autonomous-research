# COMMITTEE#1 — CLAIM-0058 (PROJ-0028, CROSS-AREA: inference-runtime x eval-safety) — token-flush chunk granularity degrades streaming safety-filter recall
## EMPIRICAL CROSS-AREA PHENOMENON, effect=support/HELD. NOT metric-validity (recall vs harness-owned GT span-membership; whole-text control pins 100% ceiling). NO closed form. Anti-circular (GT=planted-violation-span, filter reads only emitted chunks, never GT). Vote HONESTLY by role — first cross-area claim + best-positioned candidate since CLAIM-0055; it CLEARED the production-baseline make-or-break that gated recent yellows. Do not rubber-stamp; do not reflexively kill.

## CLAIM: the token-flush CHUNK GRANULARITY (a runtime latency/SSE knob) causally degrades the RECALL of a separately-owned incremental output safety filter — multi-token violation phrases straddle flush boundaries + a bounded-window moderator never sees them intact. Recall drops as chunk size grows toward production defaults, EVEN THOUGH the full completion is byte-identical + a whole-text scan flags 100%. The runtime engineer sets chunk size with no model of the safety window.

## L0 RESULT (5 seeds x N=30k, pure-Python Aho-Corasick, anti-circular):
SANITY CEILING PASSED: unbounded-rescan/whole-text = 100pct recall at every chunk size C{1..32}, 0 FP on benign+decoy -> any loss is streaming FRAGMENTATION not filter weakness. Completion byte-identical across C (only flush boundaries move).
Recall vs chunk-size C, multi-token phrases (%): stateless-per-delta 0/18.8/54.3/78.4/90.5/97.1 (C=1..32); ★ PRODUCTION sliding-window W=16: 100/100/100/100/95.5/57.3; unbounded-rescan ceiling 100 everywhere.
★ DECISIVE — OVERLAP RECOVERY POINT: the PRODUCTION sliding-window arm at realistic default W=16 shows a MATERIAL 42.7pp recall drop (100->57.3) at production chunk C=32. Recovery to ~100pct only at W* ~= 2*C (C8->W16; C16->W32; C32 needs W64), i.e. W >= chunk_size + max-phrase-len. A SMALL default overlap (W=8) does NOT heal it (46pct @C16) -> NOT a WEAKEN. The window must hold the current chunk PLUS a full-chunk lookback — a setting the latency-conscious runtime team can't pick without knowing the safety team's max-phrase token-length = the predicted cross-org-seam coupling.
DIRECTION NUANCE (flagged for L1): danger zone is LARGE chunks vs the window, not small (stateless recall RISES with C; production window heals small chunks but breaks once C>~W).
PHRASE-LENGTH MODERATION (alias control, stateless, fixed C=8): 1-token=100pct (NULL control, cannot fragment); 2/3/4-token = 88.5/77.1/65.3 (monotone) -> phrase length is the confirmed effect-moderator.

## STRESS-TEST HONESTLY: (a) is the cross-seam coupling (runtime flush-knob -> safety recall via fragmentation) genuinely uncrossed/novel, or does some streaming-moderation work already tie segment formation to the flush schedule? (scout found ZERO direct hits; Orca/vLLM silent on the safety window, Llama-Guard/2512.03553/2604.14865 evaluate on segments but never tie to flush). (b) is the W>=chunk+max-phrase recovery condition a REAL operational gap (runtime + safety are separately owned, latency team picks W without the phrase-length) or would a competent safety team obviously set W large? (c) does the org-seam framing hold — or in practice is the moderator usually the unbounded-rescan ceiling (the null arm), making the bounded-window the strawman? (the L0 included unbounded-rescan as the ceiling; the claim is the COMMON latency-motivated bounded config).

## CLAIM YAML
claim: "An inference-runtime streaming knob \u2014 the token-flush chunk granularity\
  \ (tokens accumulated before emitting a partial completion, tuned for ITL smoothing\
  \ / SSE batching / throughput) \u2014 causally degrades the RECALL of a separately-owned\
  \ incremental output safety filter, because policy-violating multi-token phrases\
  \ straddle flush boundaries and the stateless/bounded-window moderator never sees\
  \ them intact. As chunk size grows from 1 token toward realistic SSE batch sizes\
  \ (4-16 tok/flush, the production default), the streaming moderator's detection\
  \ recall on a fixed set of violating spans drops MONOTONICALLY and non-trivially\
  \ (predicted >15-30pp recall loss at production chunk sizes for multi-token phrases),\
  \ EVEN THOUGH the full completion is byte-identical and a whole-text scan of the\
  \ same filter flags 100%. NULL EXIT: if recall is flat across chunk sizes (filter\
  \ re-scans an unbounded re-accumulated buffer, or phrases are single-token, or default\
  \ window-overlap already exceeds max-phrase-length), the coupling is absent and\
  \ the claim is FALSE."
why_it_matters: "FIRST CROSS-AREA coupling claim (acting on scout-M's mined-out signal:\

## L0 RESULTS (EXP-0067)
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


## PRE-REG
# PRE_REGISTRATION — EXP-0067 / CLAIM-0058
**Researcher:** researcher-0064 (PERSISTENT-SEEDER, BUG-115) · **Project:** PROJ-0028 · **Task:** TASK-0056
**Level:** L0 (CPU-only, stdlib-only, SERIAL, <=15 min) · **Date:** 2026-06-04
**Status at write time:** PRE-REGISTERED BEFORE RUNNING. Harness owns GT; filter never reads GT.

## THE CLAIM (CLAIM-0058 — CROSS-AREA: inference-runtime x eval-safety)
The token-flush CHUNK GRANULARITY (tokens accumulated before emitting a partial completion — a
runtime latency/SSE knob) causally degrades the RECALL of a separately-owned incremental output
safety filter, because policy-violating MULTI-TOKEN phrases straddle flush boundaries and a
stateless / bounded-window moderator never sees them intact. As chunk size grows (1 -> 4..32
tok/flush), recall on violating spans is predicted to drop monotonically (>15-30pp at production
chunk sizes for multi-token phrases) EVEN THOUGH the full completion is byte-identical and a
whole-text scan flags 100%.

## ★ THE MAKE-OR-BREAK (orchestrator guard #1): PRODUCTION baseline, not a strawman
The standard production streaming moderator is a SLIDING-WINDOW-WITH-OVERLAP scanner. The headline
lives or dies against THAT, not against the naive stateless-per-chunk scanner.

### Three moderator arms (all read ONLY emitted chunks; none read GT)
- (a) **stateless-per-delta** — scans only each new chunk in isolation (naive / worst case).
- (b) ★ **sliding-window-overlap-W** (THE PRODUCTION BASELINE) — maintains a buffer of the last W
  emitted TOKENS and re-scans that window each flush. Overlap = the window retains W-(new chunk)
  tokens of context from previous flushes, so a phrase can match if it fits within any W-token
  window that the scanner re-examines.
- (c) **unbounded-rescan** — re-scans the entire accumulated buffer every flush (safety-correct

## ORCHESTRATOR NOTE: FIRST cross-area claim (inference-runtime x eval-safety), acting on a prior scout's mined-out signal for single-area train-eff+eval-safety. PRIOR-ART (verified): Orca OSDI22 + vLLM (streaming/chunked emission, SILENT on the safety window); Llama-Guard + OpenAI-Moderation + 2512.03553 + 2604.14865 (evaluate on segments/completions, never tie segment formation to the flush schedule); ZERO direct seam hits. Novelty = a latency-tuning runtime knob silently lowering safety RECALL via benign span fragmentation across the org seam (NOT the adversarial Unicode-homoglyph attack). This CLEARED the production-baseline make-or-break (the sliding-window-overlap moderator, not a strawman; default overlap does NOT heal it) that gated the recent yellows + the runtime-mitigation killer (info-fragmentation is not a fixed cost CUDA-Graphs heal) + killer-#10 (genuine null exit didn't fire). If candidate-grade, L1: real vLLM/TGI SSE at varying output_token_chunk x a real streaming moderator (Llama-Guard-streaming/OpenAI-Moderation-incremental) on a real red-team multi-token-violation set -> recall vs flush granularity + the W>=chunk+max-phrase recovery condition (note real BPE may split phrases into MORE tokens, widening the gap; check if moderators window in chars/subtokens vs words, shifting W*). If you judge the seam is actually crossed in the lit OR real moderators rescan-unbounded by default (null arm) OR the recovery condition is operationally obvious -> YELLOW/RED honestly. If the cross-seam coupling is genuinely novel + survives the production baseline + ecologically real -> a clean APPROVE toward the real-stack L1, and the strongest green shot since CLAIM-0055. Real 6/6 by role.

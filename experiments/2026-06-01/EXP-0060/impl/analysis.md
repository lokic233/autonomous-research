# EXP-0060 — Analysis & Disposition (PROJ-0014 / CLAIM-0025)

**Agent:** researcher-0025-L0-r7 | **Sub-monitor:** sub-monitor-0014-r7 | **LOCKED-TS:** `2026-06-01T22:42:08Z`
**Pre-reg:** `impl/PRE_REGISTRATION.md` (committed BEFORE run, HEAD `69ea904`) | **Run:** `logs/run_main.log` | **Numbers:** `results/summary.json`
**Corpora:** CC (primary) 72 sessions / 3290 reuse units; Codex (FIX-4) 90 sessions / 2122 reuse units. Runtime **2.59 s**, CPU stdlib.
**Harness:** extends `EXP-0057/impl/reuse_distance_census.py` VERBATIM (parsers, `extract_paths`, `build_units`, recompute-mass touch-stream, `gini`, `det_hash`); adds SGLang-LFU, SGLang-SLRU, ARC (Megiddo–Modha), LRU-K (K=2), static-pin+LRU(N∈2/3/5); keeps LRU + Belady-oracle.

## HEADLINE (one-liner)
On the live CC agent corpus the LRU→Belady recompute-mass gap is **real but oracle-only**: at matched cache residency,
**NO** classical history-only eviction policy — SGLang-LFU/SLRU, the mandatory killer baselines **ARC and LRU-K**, or
the custom static-pin+LRU — captures ≥50% of the (LRU−Belady) gap at ≥3 of 5 pre-declared capacities. The best cheap
policy (static-pin N=2) reaches the 50% bar at only **1/5** capacities, and only at the loosest capacity where the
absolute gap is negligible (0.6% of LRU); in the meaningful tight-cache regime (frac 0.1–0.3, where Belady saves
6–11%) the best capture is 15–31% and **SGLang-LFU is *worse than LRU*** (captured = −0.32 to −0.75). The result is
**session-robust** (HHI≈0.08, well below the 0.20 flag) and **0/15 static-pin cells survive BH or Bonferroni**.
→ **CLEAN-NEGATIVE-KILL.** Ship classical LRU; the ≤11% agent-KV Belady gap is not cheaply capturable. Reinforces
DEAD-0019 from the policy side.

## PER-GATE DISPOSITION (CC = primary corpus)

| Gate | Result | Disposition |
|---|---|---|
| **RE-B0** premise floor | far_share=**0.188** (≥0.15 ✓); Belady saves **max 11.0%** over LRU (frac 0.1), ≥5% ✓ | **PASS** — bimodality + LRU<Belady gap reproduced; the premise (EXP-0057 survivor) holds. |
| **RE-B1** LOAD-BEARING | best cheap policy (pin2) ≥0.50 captured at **1/5** caps; required ≥3/5 at matched residency | **FAIL → CLEAN-NEGATIVE.** No cheap policy realizes half the gap without future knowledge. |
| **FIX-2** ARC/LRU-K killer baselines | **ARC 0/5, LRU-K 0/5** caps ≥0.50 captured (even *below* the custom pin's 1/5) | ARC does **NOT** already capture the gap; but the custom two-tier doesn't win either — **all** classical policies fail. |
| **FIX-5** matched residency | pinned blocks charged against C (total resident ≤ C); pin "win" at frac 0.7 is on a 0.6%-of-LRU gap | No capacity illusion — the negative is *not* an artifact of pinning extra mass. |
| **RE-B3** robustness | HHI≈**0.08** (<0.20, no flag); **0/15** static-pin cells significant under BH **or** Bonferroni (pin2@0.7 boot-p=0.49) | The negative is session-robust; the single ≥0.50 point estimate is not statistically distinguishable from 0.50. |

### CC captured-fraction matrix `(LRU − policy)/(LRU − Belady)`, matched residency
| policy \ cap-frac | 0.10 | 0.20 | 0.30 | 0.50 | 0.70 | n≥0.50 |
|---|---|---|---|---|---|---|
| SGLang-LFU  | −0.747 | −0.396 | −0.317 | 0.312 | 0.175 | 0 |
| SGLang-SLRU | −0.391 | 0.126 | 0.307 | 0.312 | 0.175 | 0 |
| **ARC**     | 0.149 | 0.126 | 0.297 | 0.312 | 0.175 | **0** |
| **LRU-K(2)**| 0.189 | −0.044 | −0.065 | 0.312 | 0.175 | **0** |
| pin+LRU N=2 | 0.174 | 0.101 | 0.134 | 0.221 | **0.539** | 1 |
| pin+LRU N=3 | 0.225 | 0.072 | 0.060 | 0.218 | **0.539** | 1 |
| pin+LRU N=5 | 0.244 | 0.107 | 0.096 | 0.091 | **0.539** | 1 |
| *(Belady gap, % of LRU)* | *11.0%* | *9.2%* | *6.4%* | *3.1%* | *0.6%* | — |

**Reading:** the gap is largest at tight caches (frac 0.1–0.3) — exactly where every cheap policy captures least
(≤0.31, several negative). The only ≥0.50 cells sit at frac 0.7 where the entire Belady gap is 0.6% of LRU recompute
(≈16.8k tok pooled) — i.e., the policies "capture half" of an essentially negligible prize. Capture and gap-size are
**anti-correlated**: where it matters, classical policies don't help; where they help, it doesn't matter.

## FIX-2 — ARC-vs-CUSTOM VERDICT (explicit)
ARC and LRU-K, the mandatory parameter-free killer baselines, **do not capture the Belady gap** (0/5 caps ≥0.50 on CC).
This *refutes* the worry that "ARC already captures it, making the custom two-tier obsolete" — but it does so by killing
**both**: the custom static-pin (1/5) is not obsoleted by ARC because *neither* works. ARC slightly trails the custom pin
on CC and slightly leads it on Codex; the difference is within noise and immaterial because **all classical policies miss
the ≥3/5 bar**. The honest verdict is not "ARC wins" or "custom wins" — it is **"the gap is oracle-only; no classical
eviction policy, adaptive or pinned, captures it at matched residency."**

## FIX-4 — CODEX (honest cross-instrument, non-gating)
Codex is **NOT bimodal** (far_share=**0.035** < 0.15 → RE-B0 FAIL on Codex, consistent with EXP-0057's 0.036): it is
near-reuse-dominated (near_share=0.80), Belady saves max 9.3% but concentrated at tiny caps, and the capture ratios are
noisy on few far positives. On Codex the ordering flips — ARC/LRU-K/LFU edge the pin family (custom_obsolete=True there) —
but **no policy reaches ≥3/5** and the pin family even goes *negative* at frac 0.3–0.5 (capacity-charged pinning hurts on
a corpus with little far-reuse to protect). Codex does not gate the CC disposition; reported in full per FIX-4 (selective
CC-only reporting would be a kill flag). It corroborates: where far-reuse is scarce, the cheap policies neither help nor
are needed.

## HONEST NOTES / CEILINGS
- **The gap is genuine but small and oracle-only.** Belady saves ≤11% over LRU (CC), realized only with future-touch
  knowledge. The cheap policies recover at most ~⅓ of it at tight caches and frequently *under-perform LRU* (SGLang-LFU
  captured −0.75 at frac 0.1: chasing frequency evicts soon-to-be-reused fresh paths in agent traces).
- **Matched-residency (FIX-5) is honored structurally:** pinned blocks consume capacity slots (total resident ≤ C); the
  static-pin numbers are NOT inflated by holding extra mass. The one ≥0.50 pin cell is on a 0.6%-of-LRU gap.
- **Slot-count capacity** (each path = one resident block) is the EXP-0057 harness unit, frozen in the pre-reg as the
  faithful operationalization of "resident mass" (a mass-cap would require rewriting the Belady oracle, which the
  harness-verbatim mandate forbids). Documented ceiling.
- **Correctness verified:** unit tests confirm LFU beats LRU where it provably should (AABCA: 4 vs 3), Belady is a valid
  lower bound for every policy across 200 random traces, and the policies are genuinely distinct (not aliased). The
  high-capacity convergence of LFU/SLRU/ARC/LRU-K to identical recompute is real (few evictions remain once Belady hits
  its compulsory-miss floor by frac 0.5), not a bug.
- **Path-identity ceiling** (relative Bash path vs absolute file-tool path counted distinct) is inherited and CONSERVATIVE
  — only reduces measured reuse, cannot inflate any gate.
- Frozen thresholds honored verbatim; no threshold moved. far_share 0.188 vs EXP-0057's 0.189 confirms a stable corpus.

## COMMITTEE-FACING RECOMMENDATION
1. **CLEAN NEGATIVE (first-class):** on real agent KV traces, the LRU→Belady recompute-mass gap (≤11%) is **not captured
   to ≥50% by any classical history-only eviction policy at matched residency** — not SGLang-LFU/SLRU, not the killer
   baselines ARC and LRU-K, not a custom static-pin two-tier (best = 1/5 caps, statistically null after BH/Bonferroni,
   session-robust HHI≈0.08).
2. **Actionable verdict: ship classical LRU for agent file-prefix KV eviction.** Do NOT deploy LFU/frequency-aware
   variants — SGLang-LFU is *worse than LRU* at the tight capacities that matter (chases stale-frequent paths). The
   modest oracle-realizable gap requires near-oracle future-step knowledge (the explicit execution-plan direction of
   KVFlow 2507.07400 / ScaleSim), not cheap statistical policies.
3. **Reinforces DEAD-0019 from the policy side:** EXP-0057 killed a cheap causal *predictor* of far-reuse; EXP-0060 now
   shows the gap is equally unreachable by cheap classical *policies*. Both the predictor and the policy route fail ⇒ the
   agent-KV Belady gap is oracle-only; invest elsewhere.

**DISPOSITION: CLEAN-NEGATIVE-KILL (RE-B1).** Premise (RE-B0) re-confirmed; best cheap policy captures < 50% of the
Belady gap at < 3/5 capacities at matched residency ⇒ the gap is oracle-only ⇒ ship classical eviction.

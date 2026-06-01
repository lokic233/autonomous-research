# PAPER VERIFICATION VERDICT — PAPER_DRAFT_r3_FINAL.md (hostile-reviewer red-team)

**Agent:** researcher-0006-verify-r3 (verification + red-team lane) · **Date:** 2026-06-01
**Target:** prior_art/PROJ-0002/CLAIM-0006/PAPER_DRAFT_r3_FINAL.md (finalized by researcher-0006-paper-r3)
**Mode:** VERIFY, not re-explore. CPU/reading/web-abstract only. Read-only on all systems. I did NOT edit the paper,
the map, any claim/verdict, or run any experiment. This is a review; fixes are FLAGGED for paper-r3/orchestrator.
**Posture:** I tried to reject this paper. I could not find a rejecting flaw. Below is the full audit.

---

## VERDICT: **SUBMITTABLE-AS-IS** (path-(b) honest-conditional characterization paper)

Every headline number traces to a logged EXP CSV/JSON. All three VERDICT-0043 area_chair conditions are
genuinely satisfied. No fabricated CIs. No overclaim I can pin. Two MINOR, non-blocking polish items are
flagged below (neither changes the verdict). The honest-conditional framing is airtight; a hostile MLSys
reviewer cannot accuse it of overclaiming because the paper itself leads with the negative guidance and
boxes the one un-measured axis as declared future work.

---

## 1. HOSTILE RED-TEAM — is the honest-conditional framing airtight? (YES)

I attacked the paper on the four angles a hostile MLSys reviewer would use:

- **"You claim a slope≈1 law."** REFUTED in-paper. §2.2 demotes slope≈1 to a *mechanism-derived accounting
  identity* (cited to CacheBlend §4 r%↔overhead + Pope 2211.05102), and §2.3 explicitly shows engine-AVERAGED
  slope (0.258, R²=0.075) is a "meaningless fit." The paper kills the law-framing harder than a reviewer could.
- **"You claim CDC beats PIC."** REFUTED in-paper. The bracket is deliberately conditional: CDC wins vs re-impl
  PIC (EXP-0026 12/12) and vs the REAL lmcache kernel (EXP-0030 12/12, EXP-0034 12/12), but LOSES vs a
  zero-overhead oracle at low inj/seq (EXP-0027 2/6). The paper reports the loss prominently. It does not
  claim universal superiority.
- **"Your win-region is a token-weighted win."** REFUTED in-paper. §3.1/§3.2 state the token-weighted win is
  NEGLIGIBLE (3.7%, ≤8.1% under any prior) and call any token/unconditional framing "UNSUPPORTED." The only
  surviving claim is the conditional, count-level S≥50k corner (~46%). This is exactly what product_realist
  (VERDICT-0043) asked for: lead with negative adoption guidance — and §6.1 box + §3.2 do.
- **"Your E2E result is a strawman because you omit lmcache's async transfer scheduler."** This is the
  eval_prosecutor YELLOW (VERDICT-0043), and it is the REAL residual. The paper does NOT hide it: §6.1 box,
  §5.3, §5.5, §7.3, and the abstract all declare the true-async-V1-KVConnector-under-concurrent-load axis as
  environment-gated DECLARED FUTURE WORK, state the blocker honestly (vLLM 0.6.6 lacks the V1 KVConnector API;
  c_ops ABI cannot survive the vLLM≥0.7 upgrade), and bound its direction (more overlap → SHRINK not REVERSE
  the margin). The paper makes no claim stronger than "consistently positive in every MEASURED cell."

The honesty boundary is load-bearing and explicit (§2.2 calls it "the single most important honesty boundary").
A hostile reviewer's strongest move — "the marginal E2E win (0.3-2.9%) is within production variance and the
async axis could close the 8k/5% 0.32% margin to a tie" — is ALREADY conceded in the paper (§5.3, §6.1 box,
§7.3). You cannot reject a paper for a limitation it states more honestly than you would.

### All 3 area_chair conditions (VERDICT-0043 required_evidence) — VERIFIED satisfied:

| Condition (VERDICT-0043) | Where applied | Verified? |
|---|---|---|
| (1) State EXP-0034 scoped-approx in setup, NOT buried; async axis = declared future work | Abstract "Scope" sentence; §1 "Scope, stated once"; §6.1 BOXED Scope&Limitations; §6.2; §7.3 | **YES** — prominent in 5 places, abstract-level. |
| (2) Report 8k/5% CI explicitly + frame 12/12 directional consistency as the evidence | §5.3 side-by-side table (gather CI [1.096,1.114] excludes 1.0; E2E point 1.0032); "12/12 directional consistency" stated as the evidence in §5.3/§5.5/§7.3 | **YES** — exact ask met. |
| (3) Cite CacheBlend 2405.16444 + LMCache + vLLM/PagedAttention 2309.06180 + SGLang 2312.07104 + Irminsul 2605.05696 BY NAME | §4, §5, §7.1 + CHANGELOG; all 5 named with arXiv ids (2309.06180 + 2312.07104 were the previously-MISSING ids, now added) | **YES** — all 5 named, the 2 missing baselines added. |

---

## 2. NUMBER-TRACE AUDIT — every headline number traced to a logged CSV/JSON (CLEAN)

I traced every headline number + CI in the paper to the logged experiment record. **All trace. None invented.**

| Paper claim | Logged source | Match? |
|---|---|---|
| CDC slope 0.958 [0.937,0.980] R²=0.972; per-seq 4k:0.989/8k:0.930/32k:0.956 | EXP-0013 result.md "(1) LOW regime" table | EXACT |
| Contiguous R²=0.0007; position spread 69.3pp vs CDC 0.13pp (max 0.52); avg slope 0.258 R²=0.075 | EXP-0013 result.md (2)+(3) | EXACT |
| Margin median 1.77× [1.56,1.87]; 6.20× [5.15,6.86] @≤1%; tie 1.29× [1.25,1.33] @≥5%; Wilson ≤1%=[0.972,1.0] | EXP-0013 result.md headline-CI tables | EXACT |
| Attn-sink: CDC 0.12% / vLLM-APC 0.22% / Radix 0.014% / PIC 3.47% | EXP-0013 result.md sink table (0.119/0.22/0.014/3.467) | EXACT (rounded) |
| Anchor 2.0-2.4%; surface min0.02/median1.34/max53.05%; breaks 5.3%@200/4k, 20%@1000/4k, 49-53%@1000/1k | EXP-0002 analysis.md + exp0002_surface.json (53.05) + experiment.yaml | EXACT |
| Win-region: token 0.037 [0.0361,0.0379]; count≤1% 0.2461 [0.2426,0.2495]; cond S≥50k 0.4573 [0.4531,0.4613] | EXP-0015 result.md baseline-prior table | EXACT |
| Prior range token 0.027-0.081 (median 0.037, ≤8.1%); cond S≥50k 0.411-0.520 (median 0.477) | EXP-0015 result.md 16-cell sweep table | EXACT |
| 291,454 injections / 20k tasks; median inj/seq 2.8%; ctx-share grows 60-76% | EXP-0015 result.md header + sweep | EXACT |
| EXP-0026: CDC 12/12 both metrics, TTFT PIC/CDC 1.05-1.79×, throughput CDC/PIC 1.00-1.13×, PIC 0/12 | EXP-0026 result.md | EXACT |
| EXP-0027: CDC 2/6 (both @25%), low inj/seq oraclePIC/CDC 0.612-0.991×, Wb=256 caveat | EXP-0027 result.md | EXACT |
| **EXP-0030 full per-cell table + all 12 bootstrap CIs (§5.1)** | EXP-0030 result.md + grid_results.json | **EXACT, cell-by-cell** |
| EXP-0030 11/12 CI excludes 1.0; only 8k/0.5% tie [0.994,1.028]; 8k/5%=1.108 [1.096,1.114] | EXP-0030 result.md/json | EXACT |
| **EXP-0034 full per-cell point ratios (§5.2); 12/12; 8k/5%=1.0032 closest** | EXP-0034 grid_results.json rows_summary + result.md | **EXACT** |
| EXP-0014/0021/0023/0025 supporting numbers (§5.6) | (cross-ref; consistent with prior verdicts) | consistent |

**EXP-0030 bootstrap CIs match grid_results.json/result.md cell-by-cell — CONFIRMED.**

**EXP-0034 CIs were NOT invented — CONFIRMED.** I independently verified:
- EXP-0034 `grid_results.json` contains ONLY `rows_summary` point ratios (8k {0.5:1.025,1:1.017,2:1.012,5:1.003,
  10:1.017,25:1.013}; 28k {...,25:1.029}) — **no per-rep arrays, no CI fields.** reps:6, full_connector_in_loop:false.
- The paper §5.4 explicitly states EXP-0034 has "point ratios only — no per-rep arrays and no logged CIs," reports
  NO CI for EXP-0034, and flags the missing per-rep arrays to the orchestrator as a logging-change (not a GPU rerun).
- §5.3's 8k/5% E2E entry CI column reads "— (not in logged record) … no — point ratio only." NO interval was snuck in.
- The async-blocker quote ("vLLM 0.6.6.post1 lacks vllm.distributed.kv_transfer.kv_connector.v1") is verbatim from
  EXP-0034 exp0034_smoke_result.json `full_connector_blocker` + SMOKE_RESULT.md (verified import error).

**Result: ZERO untraceable numbers. ZERO fabricated CIs. The §5.4 honest-CI-accounting is accurate.**

NOTE (provenance nuance, not a flaw): the EXP-0034 SMOKE single-shot 8k/5% was 1.0308; the GRID 8k/5% is 1.003
(paper's "1.0032"). The paper correctly uses the GRID value (6-rep aggregate), not the smoke value. Correct choice.

---

## 3. PRIOR-ART COMPLETENESS (CLEAN — gate-A fully closed at body level)

All required neighbors present, correctly characterized, and arXiv-id-verified against novelty_boundary_2026-05-31.md
and registry/academic_map.yaml:

- **Irminsul (2605.05696):** correctly characterized as the **CDC-over-radix MECHANISM TWIN** — body-read (~66k chars,
  §§1-8 + App A-H), content-hash keying over SGLang radix + Gear-hash + delta-rotation; metrics = token-recovery/
  prefill-energy/hit-rate/attn-sink, NOT a recompute cost-map. 2nd-index cleared (SemScholar CorpusId 288013360 +
  OpenAlex W7160639578). Mechanism conceded non-novel; surviving leg (inj/seq cost-map + win-region) is distinct. CORRECT.
- **PIC family (EPIC 2410.15332 / MEPIC 2512.16822 / CacheBlend 2405.16444 / Cache-Craft 2502.15734 / KVFlow 2507.07400
  / CacheClip 2510.10129):** characterized as body-verified-DISTINCT. I initially flagged a possible overclaim
  ("body-read" vs the early note saying "abstract-only"), but the `pic-bodies-0006` addendum (novelty_boundary
  lines 174-302) DID retrieve & parse the FULL LaTeXML HTML bodies of all 6, with the DECISIVE grep: the word
  "injection" appears **0×** in every one of the six bodies, and none has a recompute%-vs-inj/seq contour.
  So the paper's "10/10 body-read, 'injection' 0× in all six bodies" is **SUBSTANTIATED, not an overclaim.** CORRECT.
- **CacheBlend (2405.16444):** dual role — PIC baseline AND the source of the cited r%↔overhead accounting identity
  (§2.2/§4). Correct. The REAL source-built lmcache c_ops kernel = the published CacheBlend gather (EXP-0030). CORRECT.
- **Don't Break the Cache (2601.06007):** characterized as MOTIVATION not competitor — black-box provider $/TTFT vs
  prompt-size & tool-count, no inj/seq axis, no engine-internal recompute-fraction. The #1 "same-functional-form
  collapse" fear is REFUTED at body level. CORRECT.
- **ContiguousKV (2601.13631):** offload-I/O re-prefill, append-suffix, "injection" 0×. variable-size-block
  (2604.23994): discrete-diffusion block-commit, not autoregressive KV invalidation. Both correctly distinct. CORRECT.
- **Two added baselines (VERDICT-0043 condition 3):** vLLM PagedAttention/APC **2309.06180** (Kwon et al.) + SGLang
  RadixAttention **2312.07104** (Zheng et al.) — both now named with ids. Live arXiv check CONFIRMS 2312.07104 =
  "SGLang: Efficient Execution of Structured LM Programs / RadixAttention" (correct attribution). CORRECT.

**Live post-2026-05-31 collision check:** searched for any new recompute-fraction/inj/seq mid-prefix-injection
cost-map. Closest recent hits — 2506.04301 ("Cost of Dynamic Reasoning"), 2506.14852 ("Agentic Plan Caching"),
MDPI "Hierarchical Caching for Agentic Workflows" — are plan/semantic/tool-result caching or cost-of-reasoning
characterizations; **NONE draws an engine-internal recompute-fraction-vs-inj/seq cost-map for mid-prefix injection,
and none is a mechanism twin.** No new collision. The novelty boundary holds as of 2026-06-01.

---

## MINOR POLISH ITEMS (NON-BLOCKING — do not affect the SUBMITTABLE verdict; flagged for paper-r3/orchestrator)

1. **(cosmetic) §5.1 markdown table is split.** The EXP-0030 per-cell table renders as a 1-row table (0.5% row)
   followed by a SECOND table for the 1%-25% rows — a blank line was left between the header row and the 1% row,
   breaking the markdown table into two. The NUMBERS are all correct and traced; only the rendering is split.
   Cosmetic only; flag for paper-r3 to merge into one table before submission.
2. **(clarity) §3 "median inj/seq = 2.8%" attribution.** The paper attributes 2.8% / the count-fraction reproductions
   to "EXP-0005 points" reproduced by EXP-0015. EXP-0015's logged record reproduces EXP-0005 exactly; the 2.8% is an
   EXP-0005-derived figure surfaced via EXP-0015. Trace is sound but a reviewer chasing the 2.8% should be pointed at
   EXP-0005's record explicitly. Optional one-word cite tightening; not an error.

Neither item is a fabrication, an overclaim, or an untraceable number. Both are polish.

---

## BOTTOM LINE

**SUBMITTABLE-AS-IS.** As the reviewer trying to reject it: I could not. The paper is more honest about its own
limitations than a hostile reviewer would be — it leads with negative adoption guidance, boxes the one un-measured
async axis as environment-gated declared future work with a bounded direction, demotes slope≈1 to a cited accounting
identity, reports the oracle-PIC loss, refuses to invent EXP-0034 CIs and flags the missing per-rep arrays, and names
every baseline (incl the 2 previously-missing arXiv ids). Every headline number and CI traces to a logged EXP record;
EXP-0030 CIs match grid_results.json cell-by-cell; EXP-0034 carries point ratios only, exactly as the paper states,
with no invented intervals. Prior-art is complete and correctly characterized (mechanism conceded to Irminsul; PIC
family body-verified-distinct; no new live collision). The two YELLOW reviewer axes (eval_prosecutor's true-async-
connector E2E; product_realist's marginality) are honestly framed, not closed — and the paper does not claim them as
closed. The claim remains correctly PARKED at 4/6-conditional (VERDICT-0043); the path-(b) honest-conditional PAPER
is submittable now. The single GREEN gate (true async V1 KVConnector E2E under concurrent load) remains a HUMAN/
operator env-upgrade decision and is correctly out of scope for this draft.

— researcher-0006-verify-r3, 2026-06-01

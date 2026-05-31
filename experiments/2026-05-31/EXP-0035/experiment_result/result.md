# EXP-0035 — RIGOR CHECK: does CLAIM-0010's deflated two-layer form survive EXP-0033 + error-class==gate-type?

**Agent:** researcher-0010-reframe · **Date:** 2026-05-31 · **Domain:** MAP-0002 · **CPU/stdlib-only, ~level-1**
**Claim under test:** CLAIM-0010 (deflated form, VERDICT-0035) — "(A) partial web_disabled-carried coarse
gate-table + (B) context-conditioned fine selection with a ~0.6–0.74 norm-entropy irreducible floor."
**Method:** NO new corpus parse. Arithmetic re-verification (Wilson CIs) of the load-bearing numbers from
EXP-0022/0029 (coarse U + carrying cell; fine LOSO lift + residual floor) cross-checked against the
EXP-0032/0033 strict-definition + Codex-double-log correction applied to the SAME REDIRECTABLE/web_disabled
cell, and against EXP-0012's error-class==gate-type (<=0.2% over 1 bit) result.

## Finding 1 — the coarse layer is one cell, and that cell's "determinism" is a definitional artifact
- EXP-0029: Theil U(modality|gate) FULL = 0.381 [0.310,0.472]; drop `web_disabled` (LOCO) -> 0.034
  [0.003,0.091], upper < 0.15. **91% of the coarse signal is the single REDIRECTABLE/web_disabled cell.**
- That cell's "deterministic CROSS_TOOL_REDIRECT modality" (normH=0, 68/68) is computed under the LENIENT
  any-twin-after-window (K=6) recovery definition — the SAME object EXP-0033 corrected. Re-measured on the
  same cell under EXP-0032/0033 discipline (deduped, strict reactive = twin AFTER block not before):

  | definition | count | Wilson95 |
  |---|---|---|
  | strict reactive-redirect (EXP-0032) | 2/43 = 0.047 | [0.013,0.155] |
  | strict reactive-redirect (EXP-0033 deduped) | 5/43 = 0.116 | [0.051,0.245] |
  | **PREEMPT** (parallel twin BEFORE block) | 34/43 = 0.791 | [0.648,0.886] |
  | lenient any-after-window (the 66/68-style count) | 40/43 = 0.930 | [0.814,0.976] |

  => The cell is ~79% PREEMPT, ~12% reactive. The "cross-tool redirect" modality label that gives the
  coarse layer its normH=0 is the lenient-definition artifact (preempt mislabeled as redirect), NOT a
  routing decision the gate deterministically produces.
- EXP-0012: error-class adds <=0.2% over the single REDIRECTABLE bit. So the coarse "layer" IS one
  config bit (is-this-the-web_disabled-block) = the gate-type config-fact already in the synthesis.

**Coarse layer does NOT survive as an independent finding.** It reduces to (a) the gate-type config-fact
(synthesis 3.1 / EXP-0012) + (b) one cell whose "deterministic redirect modality" is the EXP-0033 artifact.

## Finding 2 — the fine layer's only non-tiny lift lives in that same artifact cell
EXP-0029 leak-free LOSO + paired bootstrap:

| gate | lift | paired 95% CI | residual normH [CI] | verdict |
|---|---|---|---|---|
| REDIRECTABLE | +0.126 | [+0.063,+0.189] | 0.608 [0.543,0.717] | significant |
| GRANT_REQUIRED | +0.081 | [+0.000,+0.189] | 0.676 [0.490,0.798] | borderline n.s. |
| TRANSIENT | +0.030 | [+0.008,+0.055] | 0.740 [0.684,0.789] | significant but TINY |

- The only clearly-significant, non-tiny fine lift (+12.6 pts) is in REDIRECTABLE = the web_disabled cell.
  Given EXP-0033 (recovery there is dominated by PREEMPTIVE parallel twin-firing — the web tool was already
  going to be batched), this lift is largely "context predicts WHICH web-twin was preemptively batched" — a
  property of CC's parallel-batching policy hook, single-harness and CC-policy-specific, not an adaptive
  recovery decision.
- TRANSIENT lift is real but tiny (+3 pts) on a 0.74 residual floor; GRANT borderline (n=37).

**Fine layer survives ONLY as:** a small CC-policy-specific context lift concentrated in the web_disabled
cell, over a large (~0.6–0.74) irreducible entropy floor. The durable content is the NEGATIVE part — the
residual floor (~48%+ situation-dependent; not a routing table, not adaptive) — which synthesis 1.3 already states.

## Verdict on CLAIM-0010 (deflated form): DOES NOT SURVIVE AS A STANDALONE TWO-LAYER CLAIM
Both layers collapse into objects already in the PROJ-0003 synthesis:
- COARSE -> the gate-type config-fact + the EXP-0033-corrected web_disabled cell (a measurement artifact when
  labeled "deterministic cross-tool redirect modality").
- FINE -> the residual-entropy-floor negative result (recovery is NOT a low-entropy routing table and NOT free
  adaptivity), with a CC-specific predictive crumb in the one artifact cell.

The "two-layer" framing adds nothing beyond (gate-type-config-fact) + (residual-floor negative result) +
(the now-known web_disabled measurement artifact). Same structural fate as CLAIM-0011.

## Effect: WEAKEN (-> recommend wind-down to negative-note; orchestrator decides)
CPU rigor-check only; no claim/verdict/map edits. Files: this result.md.

# CLAIM-0010 — FINAL DETERMINATION (honest disposition)

**Author:** researcher-0010-reframe · **Date:** 2026-05-31 · **Domain:** MAP-0002 · **CPU-only**
**Orchestrator:** session 22bd6bef-b84b-4827-a371-87443ea8602f
**Inputs re-examined:** CLAIM-0010.yaml (deflated), VERDICT-0030/0035, EXP-0022/0029 (two-layer),
EXP-0031/0032/0033 (cross-harness + double-log + naming), EXP-0012 (error-class==gate-type),
PAPER_SYNTHESIS.md, CLAIM-0011_final_determination.md (the analog), MAP-0002 references.
**Fresh rigor-check:** EXP-0035 (CPU, no new corpus parse) — arithmetic re-verification of the
load-bearing coarse/fine numbers cross-checked against the EXP-0033 strict-definition + double-log
correction applied to the SAME REDIRECTABLE/web_disabled cell.

---

## 1. THE RIGOR CHECK (EXP-0035): re-examine CLAIM-0010's two load-bearing pillars

CLAIM-0010's deflated form has exactly two pillars: a **PARTIAL web_disabled-carried coarse gate-table**
and a **context-conditioned fine selection over a ~0.6–0.74 residual-entropy floor**. The two new facts the
orchestrator asked me to test against are: (a) EXP-0033 — the cross-harness modality contrast was largely a
Codex double-log artifact, and the "in-thread redirect" anchor is a definitional artifact; (b) EXP-0012 —
error-class == gate-type (≤0.2% over a 1-bit flag).

### Pillar A — COARSE layer: collapses into the gate-type config-fact + a measurement artifact
- **91% of the coarse signal is one cell.** Theil U(modality|gate) FULL = 0.381 [0.310,0.472]; drop
  `web_disabled` (LOCO) -> 0.034 [0.003,0.091], upper < 0.15 (EXP-0029). The coarse "gate-table" is
  almost entirely the single REDIRECTABLE/web_disabled cell.
- **That cell's "determinism" is the EXP-0033 artifact.** Its normH=0 "deterministic CROSS_TOOL_REDIRECT
  modality" (68/68) is computed under the LENIENT any-twin-after-window K=6 definition — the *same object*
  EXP-0033 corrected. Re-measured on that cell under strict reactive (twin AFTER block, deduped):

  | definition | count | Wilson95 |
  |---|---|---|
  | strict reactive-redirect (EXP-0032) | 2/43 = 0.047 | [0.013,0.155] |
  | strict reactive-redirect (EXP-0033 deduped) | 5/43 = 0.116 | [0.051,0.245] |
  | **PREEMPT** (parallel twin BEFORE block) | 34/43 = 0.791 | [0.648,0.886] |
  | lenient any-after-window (the 66/68 count) | 40/43 = 0.930 | [0.814,0.976] |

  The cell is **~79% PREEMPT, ~12% reactive.** The "cross-tool redirect" modality label that gives the
  coarse layer its normH=0 is preemptive parallel twin-firing *mislabeled* as a reactive routing decision.
  The gate does not "deterministically produce a redirect modality"; the web tool was already being batched.
- **EXP-0012 finishes it:** error-class adds ≤0.2% over the single REDIRECTABLE bit. So the coarse "layer"
  IS one config bit = exactly the gate-type config-fact already in the synthesis (CLAIM-0009-level).

**=> The coarse layer does NOT survive as an independent finding.** It reduces to (a) the gate-type
config-fact (PAPER_SYNTHESIS 3.1 / EXP-0012) plus (b) a single cell whose "deterministic redirect modality"
is now a known measurement artifact (EXP-0033). It adds nothing over the gate taxonomy + the 1-bit result.

### Pillar B — FINE layer: only non-tiny lift lives in the same artifact cell; the durable part is the negative floor
EXP-0029 leak-free LOSO + paired bootstrap:

| gate | lift | paired 95% CI | residual normH [CI] | verdict |
|---|---|---|---|---|
| REDIRECTABLE | +0.126 | [+0.063,+0.189] | 0.608 [0.543,0.717] | significant |
| GRANT_REQUIRED | +0.081 | [+0.000,+0.189] | 0.676 [0.490,0.798] | borderline n.s. |
| TRANSIENT | +0.030 | [+0.008,+0.055] | 0.740 [0.684,0.789] | significant but TINY |

- The only clearly-significant, non-tiny fine lift (+12.6 pts) is in REDIRECTABLE = the web_disabled cell.
  Given EXP-0033 (recovery there is dominated by PREEMPTIVE parallel twin-firing), this lift is largely
  "context predicts WHICH web-twin was preemptively batched" — a property of Claude Code's parallel-batching
  policy hook, **single-harness and CC-policy-specific**, not an adaptive recovery decision.
- TRANSIENT lift is real but tiny (+3 pts) on a 0.74 floor; GRANT borderline (n=37).

**=> The fine layer survives ONLY as** a small CC-policy-specific context crumb concentrated in the artifact
cell, over a large (~0.6–0.74) irreducible entropy floor. The *durable* content is the NEGATIVE part — the
residual floor: recovery tool-choice is ~48%+ genuinely situation-dependent, NOT a low-entropy routing table
and NOT free adaptivity. That negative result is already stated in PAPER_SYNTHESIS 1.3.

## 2. ANSWERS TO THE THREE BINDING QUESTIONS

**Q1 — Does the deflated two-layer form survive in light of (a) the EXP-0033 double-log/definition
artifact and (b) error-class==gate-type?** **NO.** Both pillars dissolve. The coarse layer is 91%
one cell, and that cell's "deterministic cross-tool redirect" is precisely the lenient-definition object
EXP-0033 showed to be ~79% preempt mislabeled as redirect; the residual coarse signal without it is
indistinguishable from zero (U=0.034, upper 0.091). EXP-0012 reduces the coarse layer to the 1-bit
gate-type config-fact. The fine layer's only material lift is inside that same artifact cell and is
CC-policy-specific; the rest is the residual-entropy floor (a negative result).

**Q2 — Is "two-layer" still defensible as a standalone claim?** **No.** Once you subtract the
gate-type-config-fact (Pillar A bit) and the residual-floor negative result (Pillar B floor), the
"two-layer" framing adds nothing. What remains is exactly: (gate-type config-fact) + (residual-floor
negative result) + (a now-known web_disabled measurement artifact). It collapses into the same components
as CLAIM-0011 and the PROJ-0003 negative-result synthesis. The framing implies a structural law
("coarse-determined / fine-conditioned recovery architecture") that the data, under the corrected
definition, does not support beyond config + noise-floor.

**Q3 — Disposition?** **Wind down to a negative-note, folded into PAPER_SYNTHESIS.** (Justified below.)

## 3. DISPOSITION RECOMMENDATION

**Recommend: WIND DOWN to a negative-result note folded into the PROJ-0003 synthesis — mark CLAIM-0010
DONE-as-deflated-to-a-config-fact-plus-residual-floor** (the same disposition as CLAIM-0011's DONE-as-refuted).

Justification:
1. **The standalone two-layer thesis does not survive max-rigor re-examination.** The coarse layer = the
   1-bit gate-type config-fact (already EXP-0012/CLAIM-0009) whose load-bearing "deterministic redirect"
   cell is an EXP-0033 measurement artifact. The fine layer's durable content is the residual-entropy floor
   (a negative result already in synthesis 1.3); its one positive crumb is CC-policy-specific and single-harness.
2. **Nothing novel is added beyond what the synthesis already records.** PAPER_SYNTHESIS already absorbs
   exactly these pieces: 1.3 ("two-layer reframe deflates to partial + web_disabled-carried"; residual floor),
   3.1 (gate taxonomy + the 1-bit modality fact), and 1.4 (the Codex double-log artifact / EXP-0033). There is
   no surviving standalone claim to keep open.
3. **The required_evidence from VERDICT-0035 is effectively foreclosed.** It asked to adopt the deflated
   headline AND get cross-harness replication. EXP-0031/0032/0033 supplied the cross-harness work — and it
   went the wrong way: the carrying cell's "modality" is a definitional artifact, and the cell itself is a
   Claude-Code-specific policy hook that does not generalize. The deflated headline, adopted honestly, IS the
   negative result; there is no green path left.
4. **The durable contribution is the METHODOLOGY, not the claim** — the decisive-cell ablation (M4),
   double-log dedup (M5), and strict-vs-lenient recovery definition (M3/M8) that collapsed both the coarse
   cell and the cross-harness contrast. That belongs in the negative-result/methods synthesis.

**Why NOT keep as a narrow claim:** the only narrow true statements (gate-type is the right conditioning
variable; recovery has a high irreducible residual-entropy floor) are not novel/standalone — the first is
EXP-0012/MAP-0002 + pre-empted in generic form by LangGraph, the second is a negative result. Neither
warrants an open claim; both are already in the synthesis.

**Why NOT cemetery:** not warranted. The lineage produced (i) the residual-entropy-floor characterization,
(ii) the decisive-cell-ablation + double-log + definition-discipline methodology, and (iii) feeds the same
off-node v2 factorial revival path as CLAIM-0011. "Cemetery" implies nothing salvageable; the honest status
is negative-result-with-methodology, i.e. the synthesis — not the graveyard.

**Concrete:** mark CLAIM-0010 status DONE / deflated-to-config-fact+residual-floor; fold the
residual-entropy-floor negative result + the decisive-cell/double-log/definition methodology into
PAPER_SYNTHESIS (already substantially present in §1.3/§2/§3.1); record the off-node v2 factorial
(CLAIM-0009_interventional_design_v2.md) as the documented revival condition. **Orchestrator decides — this
file recommends only; no claim/verdict/map edits made.**

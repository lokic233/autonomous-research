# CLAIM-0011 — FINAL DETERMINATION (honest disposition)

**Author:** researcher-0011-final · **Date:** 2026-05-31 · **Domain:** MAP-0002 · **CPU-only**
**Orchestrator:** session 22bd6bef-b84b-4827-a371-87443ea8602f
**Inputs re-examined:** CLAIM-0011.yaml (RESTATED/weakened), VERDICT-0036/0038/0039/0040,
EXP-0031/0032/0033 result.md + CSVs, CLAIM-0009_interventional_design_v2.md, MAP-0002.
**Method:** maximum-rigor re-examination of the cleanest uniform DEDUPED data across all 3 corpora
(no new corpus parse — re-verified the deduped EXP-0033 T2 numbers + Wilson CIs + Fisher-exact tests
arithmetically; the double-log fix is authoritative). No fresh experiment registered.

---

## 1. THE ONE-MORE-TIME RIGOR CHECK (deduped, uniform K=6, naming controlled)

Cleanest uniform definition (canonical `function_call` stream, Codex double-log fixed,
strict reactive-redirect = twin fired AFTER block in-thread and NOT before):

| harness | model | blocks | named | **reactive** Wilson95 | **preempt** Wilson95 |
|---|---|---|---|---|---|
| CC     | Claude | 43  | 0/43  | 5/43 = **0.116** [0.051,0.245] | 34/43 = 0.791 [0.648,0.886] |
| Codex  | GPT    | 152 | 0/152 | 0/152 = **0.000** [0.000,0.025] | 152/152 = 1.000 [0.975,1.000] |
| Gemini | Gemini | 9   | 9/9   | 2/9 = **0.222** [0.063,0.547] | 7/9 = 0.778 [0.453,0.937] |

**Is there ANY statistically-defensible cross-harness modality difference NOT explained by
(artifact OR naming OR model-diagonal)?**

- **Dominant modality is IDENTICAL across all three: PREEMPT** (CC 79%, Codex 100%, Gemini 78%).
  The headline CLAIM-0011 cross-harness contrast (CC-redirect vs Codex-abandon, 66/66 vs 0/142) was a
  **Codex double-log artifact** — deduped, Codex preempts 152/152. **DISSOLVED.**
- **Only one significant difference survives:** CC reactive 5/43 vs Codex 0/152 (Fisher exact **p=0.0004**).
  Under maximum rigor this is **NOT a defensible routing-determined-modality signal**, because:
  1. **Direction-wrong.** The RESTATED claim predicted CC=preempt / Codex=ISOLATE-abandon. Data shows
     Codex preempts *harder* (100%>79%) and has *zero* reactive tail. The significant difference is CC
     having a small reactive tail — the opposite shape to the surviving claim.
  2. **Magnitude is a residual tail** (5 events) on top of a shared dominant preempt mode. Both reactive
     rates are near-zero (0.116 vs 0.000); CIs nearly touch.
  3. **Perfectly aliased with MODEL disposition.** CC=Claude, Codex=GPT, on a perfect on-node diagonal.
     arXiv:2603.02277 reports exactly this abandon-vs-persist split as a per-MODEL property
     (GPT disengages, Claude persists). The 5-vs-0 tail is equally "Claude persists a bit / GPT doesn't"
     — cannot be attributed to ROUTING on-node.
- **Naming confound: cannot be discharged, weakly argues against.** Naming is perfectly collinear with
  harness at the canonical-block level (CC 0/43, Codex 0/152, Gemini 9/9 named) — unestimable within
  CC/Codex. The only place with variance (within Gemini) shows naming non-significant: named 0.222 vs
  unnamed 0.157, Fisher p=0.64. Gemini is also the *only* harness with a nonzero in-thread reactive
  redirect (2/9) AND the only one whose error names an in-inventory tool — modality∼naming∼harness∼model
  all collinear there.

**ANSWER: NO.** After dedup + naming control + model-diagonal accounting, **there is no statistically-defensible
cross-harness modality difference attributable to harness ROUTING.** The modality-selection thesis —
"recovery modality is set by the harness routing configuration, not error-class/model" — **does not survive.**
Everything that looked like cross-harness modality routing dissolves into (a) the Codex double-log artifact,
(b) error-naming collinearity (Gemini), or (c) model-disposition aliasing (the CC-vs-Codex tail). This is
the honest finding.

## 2. WHAT, IF ANYTHING, SURVIVES (precise)

**One narrow, harness-agnostic fact survives — and it is NOT modality-routing:**

> **The REDIRECTABLE gate TYPE exists and is structurally consistent across all 3 harnesses, and
> gate-TYPE carries recovery-MODE information *within* a harness.** Each harness independently exhibits a
> hard tool-block whose error implies/names a sanctioned in-inventory alternative (CC web_disabled →
> external_web_search; Codex input_filter URL block → three_pai_external_web_search; Gemini
> run_shell_command-not-found → grep_search/glob), and these are structurally distinct from
> GRANT_REQUIRED (workspace_boundary) and TRANSIENT (schema/regex) gates. Within Gemini the per-gate
> separation is real: REDIRECTABLE redir-share 1.000 [0.610,1.000] vs GRANT_REQUIRED 0.267 [0.109,0.520]
> vs TRANSIENT 0.250 [0.120,0.449] (non-overlapping bounds, EXP-0031).

**What this surviving form explicitly does NOT claim:**
- NOT that the harness *routing table determines which modality fires* across harnesses (refuted/dissolved).
- NOT any cross-harness modality DIFFERENCE (that was the double-log artifact).
- NOT a clean redirectable-vs-TERMINAL taxonomy — the TERMINAL pole is un-demonstrable on these corpora
  (EXP-0020: no n≥10 near-terminal class; terminality window-dependent + class-independent). It is at most
  a REDIRECTABLE-vs-(same-tool GRANT_REQUIRED/TRANSIENT) two-pole taxonomy.
- The within-Gemini gate→modality association is partly MECHANICAL (a not-in-inventory tool can *only*
  recover cross-tool), not a free routing decision.

**Caveats on even this:** small n (Gemini 9 blocks); LangGraph ToolNode pre-empts the generic
"framework mediates error handling" framing (must stay narrow); tool-inventory confound was discharged
(EXP-0032: Codex has+uses a 442-call web twin yet 0 reactive redirects) — which is the one clean positive
methodological result. The gate taxonomy is essentially the pre-existing [EXP-0008] MAP-0002
occupied_territory insight, already absorbed into the map.

## 3. DISPOSITION RECOMMENDATION

**Recommend (a) WIND DOWN to a negative-result note, folded into the PROJ-0003 negative-result synthesis —
i.e. mark CLAIM-0011 DONE-as-(largely)-refuted.** Justification:

1. **The core thesis is refuted on-node.** The routing-determines-modality claim and its restated
   preempt-vs-isolate form both fail under the cleanest uniform deduped definition. The only significant
   residual is direction-wrong and model-confounded.
2. **The remaining true content is not novel enough to carry a standalone claim.** The surviving piece
   (REDIRECTABLE gate taxonomy + within-harness gate→mode info) is the pre-existing EXP-0008 insight,
   already in MAP-0002, and is pre-empted in generic form by LangGraph. It is a characterization, not a
   predictive-over-null discovery.
3. **The genuinely durable contribution is the METHODOLOGY**, not the claim: the measurement-artifact-
   catching pipeline (Codex double-log dedup + naming-confound control + uniform strict definition that
   collapsed CC's 66/66 → 5/43) is what actually advanced PROJ-0003. This belongs in the negative-result/
   methods synthesis, not as a surviving thesis.
4. **The one path that could revive a defensible routing claim is GENUINELY off-node-blocked** (v2
   OpenCode-pivot 6-cell factorial; model⊗harness is a perfect on-node diagonal, OpenCode logs no
   model/tool/outcome). No further on-node work can break the 3-way alias.

**Why NOT (b) keep as a narrow taxonomy claim pending off-node v2:** the taxonomy is not novel/standalone
(EXP-0008/MAP-0002/LangGraph), and pending the off-node interventional is what a *revival condition* on a
wound-down note is for — not a reason to keep an active claim open. Better to fold the taxonomy into the
synthesis and record the v2 design as the documented revival path (it already exists in prior_art).

**Why NOT (c) cemetery:** not warranted. The work produced (i) a reusable artifact-catching methodology,
(ii) a discharged tool-inventory confound, (iii) a real (if non-novel) cross-harness gate taxonomy, and
(iv) a fully-specified off-node revival experiment. "Cemetery" implies nothing salvageable; here the
honest status is *negative-result-with-methodology-and-a-documented-revival-path*, which is the
negative-note synthesis, not the graveyard.

**Concrete:** mark CLAIM-0011 status DONE / refuted-on-node; fold the gate taxonomy + the dedup/naming/
uniform-definition methodology + the discharged inventory confound into the PROJ-0003 negative-result
synthesis; cite CLAIM-0009_interventional_design_v2.md as the off-node revival condition. (Orchestrator
decides — this file recommends only; no claim/verdict/map edits made.)

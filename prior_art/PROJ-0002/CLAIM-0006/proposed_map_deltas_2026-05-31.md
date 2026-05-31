# Proposed MAP-0001 deltas — for ORCHESTRATOR to merge (NOT applied by me)
agent: researcher-novelty-boundary-0006 | date: 2026-05-31 | claim: CLAIM-0006

Constraint honored: I did NOT edit registry/academic_map.yaml. These are proposals only.

## 1. open_gaps (CLAIM-0006 line) — append a body-verification status note
ADD to the CLAIM-0006 open_gaps entry:
  "+novelty-boundary-0006 (2026-05-31, BODY-LEVEL): GREEN-gate (A) substantially CLOSED. (i) 'Don't
   Break the Cache' 2601.06007 BODY-READ — measures $-cost & TTFT vs prompt-SIZE/tool-COUNT (black-box
   provider API), NO inj/seq recompute-fraction cost-map, NO position-independence finding, NO engine
   internals → does NOT collapse CLAIM-0006 (the 'same functional form' fear is REFUTED at body level).
   (ii) Irminsul 2605.05696 BODY-READ — mechanism TWIN (CDC-over-radix), but publishes token-recovery%
   + prefill-energy + attn-sink fractions, NO recompute-fraction inj/seq cost-map. (iii) Irminsul now
   indexed in >=2 independent indices (Semantic Scholar CorpusId 288013360 + OpenAlex W7160639578) →
   mechanism-collision is firm, no longer single-source. RESIDUAL: PIC-family distinction still
   abstract-level only (LOW risk); eval/GPU gate unchanged."

## 2. red_zones — sharpen the existing CDC-over-radix entry (mechanism kill is now firm)
CHANGE:
  "CDC-over-radix repair MECHANISM as a novelty claim (occupied: Irminsul/PIC family; novelty must be
   characterization, not mechanism)"
TO:
  "CDC-over-radix repair MECHANISM as a novelty claim — DEAD. Body-confirmed twin Irminsul 2605.05696
   (CDC content-hash keying over SGLang radix + Gear-hash boundaries), indexed x2 (SemScholar/OpenAlex)
   + PIC genus (EPIC/CacheBlend/Cache-Craft/MEPIC) multi-source. Novelty must be the engine-internal
   inj/seq COST-MAP characterization, not the mechanism."

## 3. key_prior_work — annotate the two body-read entries
- "Don't Break the Cache arXiv 2601.06007" → append: "(BLACK-BOX provider-API $/TTFT vs prompt-size &
  tool-count; NO recompute-fraction cost-map, NO inj/seq axis, NO position-indep finding — body-verified;
  distinguishable, cite as motivation)"
- "Irminsul arXiv 2605.05696" → change "(CDC-over-radix, single-source flag)" to
  "(CDC-over-radix MECHANISM TWIN, body-verified; now indexed SemScholar+OpenAlex — no longer single-
  source; publishes token-recovery%/energy, NOT the inj/seq recompute cost-map)"

## 4. NEW edges (proposed) for the map's edge set / CLAIM-0006 closest_prior_work
- CLAIM-0006 --distinguished-from--> 2601.06007 : "VERIFIED body-level; black-box $/TTFT vs size/count,
  not engine recompute-fraction vs inj/seq" (was 'UNVERIFIED GREEN-blocker' in VERDICT-0017 map_delta).
- CLAIM-0006 --mechanism-occupied-by--> 2605.05696 : "VERIFIED twin; firm (x2 index)".
- CLAIM-0006 --slope~1-derivable-from--> Pope 2211.05102 + Kwon 2309.06180 : "accounting identity,
  CONFIRMED by reasoning (recompute=(R+W)/S≈R/S)".

## 5. status note
Keep MAP-0001 status: yellow (eval/GPU gate still binding). Novelty gate (A) moved from
"UNVERIFIED — GREEN-blocker" to "substantially VERIFIED at body level; LOW residual on PIC-family bodies."

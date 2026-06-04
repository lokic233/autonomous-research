# PROJ-0032 — Data-systems-for-ml x Agentic/serving CROSS-AREA: Pydantic->vLLM/xgrammar constraint-ENFORCEMENT divergence (PORTABILITY CLIFF, EMPIRICAL PHENOMENON / PRODUCTION-SEAM)

5th cross-area coupling claim, CLAIM-0059 winning shape, designed to CLEAR the two killers that just yellowed
CLAIM-0060/0061: killer #10 (unmeasurable real-traffic prevalence) by measuring ENTIRELY on PUBLIC artifacts, and
killer #3 (known-mechanism-in-a-costume) via a DIFFERENTIAL cross-backend framing (not "constraints aren't enforced").

## THE SEAM (two independently-owned subsystems)
- A = SCHEMA GENERATOR (Pydantic, Pydantic Inc.): dev writes Field(ge=0, le=100, max_length=64, pattern=...) ->
  Pydantic emits standard JSON-Schema validation keywords minimum/maximum/maxLength/pattern/multipleOf BY DEFAULT.
  Dev mental model: "these are enforced."
- B = GRAMMAR-CONSTRAINED DECODER (vLLM + xgrammar, vLLM project / MLC): vLLM default structured_outputs backend =
  auto -> tries xgrammar FIRST. xgrammar builds a CFG over JSON structure/types and DROPS numeric-range / string-length
  / regex-pattern constraints at grammar-compile time.
- ORG-SEAM: neither owns the SEMANTIC-ENFORCEMENT guarantee (Pydantic's contract = emit faithful JSON Schema;
  xgrammar's = produce structurally-valid JSON fast). The guarantee falls in the gap.
- THE DIVERGENT DEFAULT THAT MAKES IT A CLIFF: OpenAI strict Structured-Outputs ENFORCES these since 2025-05-21
  (min/max ranges, string length/format/regex). So the two production defaults DISAGREE on byte-identical schemas:
  OpenAI-strict enforces, vLLM-auto does not -> change base_url, "validated" silently becomes "structurally-shaped-only".

## PRIMARY THESIS (measurable on PUBLIC data)
For a public JSON-Schema corpus (JSONSchemaBench / Pydantic models w/ Field constraints): D = fraction of
constraint-bearing schemas whose declared value constraints xgrammar's compiled grammar does NOT enforce; V = fraction
of strings ACCEPTED by the xgrammar grammar that VIOLATE the dropped constraint (sample the accepted language,
re-validate with reference `jsonschema`). HEADLINE: D and V are materially >0 under vLLM-auto, =0 for the same schemas
under OpenAI-strict (documented supported-keyword set) -> a cross-backend enforcement-divergence rate, a property of
PUBLIC code + PUBLIC schemas, NO private prevalence constant.

## RESIDUAL NOVELTY > "first quantification of a known mechanism" (killer #3 defense — MUST headline)
Folklore = "constrained decoding guarantees structure not semantics" (Willard&Louf 2023; Geng 2501.10868 explicitly
scope OUT value constraints). The FINDING is the DIFFERENTIAL: the SAME artifact (one Pydantic model) carries a SILENTLY
DIVERGENT enforcement guarantee across the two dominant structured-output backends, invisible at every observable surface
(same schema bytes, same 200 OK, same parse success). Newly OPENED: only became a cliff AFTER OpenAI closed its half
May-2025 — before that both ignored constraints, no divergence. Present the OpenAI-vs-vLLM divergence as the IRREDUCIBLE headline.

## NULL EXITS / COULD-IT-FAIL (genuine)
If xgrammar at the PINNED version DOES encode minimum/maximum/pattern into the grammar -> D->0, V->0 -> divergence
vanishes -> claim KILLED. NOT construction-forced; depends on xgrammar's actual keyword coverage at the tested version.
PIN xgrammar + vLLM versions, report per-keyword coverage.

## KILLER SCREEN (all 10 cleared — see CLAIM-0062)
#1 not metric-validity (enforcement-guarantee DIFFERENCE, not a counting redefinition). #2 Willard&Louf2023 + Geng
2501.10868 checked (scope out value constraints). #3 differential portability-cliff framing (not "ignores semantics").
#4 currency = enforcement-divergence rate, bound-independent (property of the accepted language). #5 runs the ACTUAL
xgrammar compiler on ACTUAL Pydantic-emitted schemas. #6 client-side re-validate (Instructor/LangChain) modeled as the
control arm = NOT vLLM's default server behavior. #7 baseline = `vllm serve` OpenAI-compat endpoint, default
structured_outputs (auto/xgrammar), the canonical self-hosted path. #8 L0 CAN fail (xgrammar version coverage). #9
prod-framework prior-art: vLLM/xgrammar/Outlines/lm-format-enforcer/Instructor/LangChain/OpenAI checked, none close the
seam at the serving default. #10 ★ measurable on PUBLIC data (JSONSchemaBench + open-source xgrammar), NO private trace.

## HONEST RISK
Killer #3 is the live one — committee may call it "empirical confirmation that guided decoding ignores semantics."
Defense = the differential/portability framing (OpenAI-closed vs vLLM-open, newly opened May-2025, invisible at all
surfaces) as the headline, NOT "constraints aren't enforced." Version-risk (#8): pin versions, report per-keyword coverage.
Scout self-rating GREEN-eligible ~65%.

## POSTURE
EXPAND/LIGHTWEIGHT: ONE sharp claim (CLAIM-0062), normal pipeline. L0 = CPU. Owner: orchestrator-r7-001.

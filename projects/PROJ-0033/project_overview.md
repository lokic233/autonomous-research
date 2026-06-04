# PROJ-0033 — Agentic-systems x Data-systems/serialization CROSS-AREA: JS LLM-agent tool-arg 64-bit-integer SILENT CORRUPTION (two jointly-blind production defenses, EMPIRICAL PHENOMENON / PRODUCTION-SEAM)

6th cross-area coupling claim, CLAIM-0059 winning shape, designed to clear EVERY killer that hit the last 4 claims —
notably killer #10 (unmeasurable prevalence -> here DETERMINISTIC + public artifacts) and killer #11 (version-chase ->
here the core mechanism is IEEE-754/ECMA-262, unmovable since 1999; fast-moving tools verified at CURRENT release).

## THE SEAM (two independently-owned subsystems)
- A = MODEL-OUTPUT / PROVIDER BOUNDARY (OpenAI/Anthropic/Google + tool/MCP schema author): hands the runtime
  tool_call.function.arguments as a JSON STRING; the integer TEXT is correct (LLM emits the full 19-digit literal;
  OpenAPI/MCP legitimately declare fields type:integer / int64 / z.number()).
- B = JS AGENT RUNTIME (Vercel AI SDK v5, independent repo): parses that string with secure-json-parse (chosen for
  PROTOTYPE-POLLUTION hardening, NOT numeric fidelity -> delegates numbers to native JSON.parse -> IEEE-754 double),
  then validates with Zod (tool-arg default z.number(); even z.number().int() calls Number.isInteger which is TRUE for
  9007199254740992, NOT Number.isSafeInteger).
- DIVERGENCE = the coupling: A assumes "JSON integer = exact integer" (RFC 8259, silent on precision); B assumes
  "JSON number = float64" (ECMA-262, immovable since 1999) + "is it a number? integral?" -- NEITHER checks safe-integer
  range. Each made a locally-correct choice (security; type-safety) that FAILS OPEN on numeric width. >2^53 literal ->
  silently rounded to nearest double -> passes Zod unflagged -> tool gets a corrupted ID, zero error surfaced.

## PRIMARY THESIS (deterministic, public-data measurable)
In-band (>2^53) bit-exact survival = 0 (every such value collides with >=1 neighbor); silent-validation-pass = 100%
(corruption is total AND invisible). Control band [0,2^53) survives 1.0 (isolates the boundary). Run the ACTUAL AI SDK
parse path (secure-json-parse) + ACTUAL Zod validators as-shipped.

## NOVELTY ANCHOR (killer #3 defense — MUST headline)
NOT "JS loses bigints" (folklore since 2016). The SEAM: the runtime DEPLOYS TWO named defensive layers at this exact
boundary (deliberately swapped raw JSON.parse for HARDENED secure-json-parse + runtime Zod validation = its selling
point) and BOTH are JOINTLY BLIND to numeric width; AND the precision is gone BEFORE any reviver/refinement can see the
original text (MDN reviver-ordering) -> structurally UNRECOVERABLE post-parse, not merely unguarded. A reasonable
engineer assumes "hardened parse + schema validation = safe tool args" -> demonstrably false.

## NULL EXITS / COULD-IT-FAIL (genuine)
If the current default parser preserved precision (lossless-json/BigInt) OR z.number().int() rejected unsafe integers
-> survival 1.0 / silent_pass 0 -> claim KILLED. Falsifiable. PIN current AI SDK v5 / secure-json-parse / Zod v4 versions.
NEGATIVE CONTROL: Python OpenAI/Pydantic path (json.loads parse_int=int, arbitrary precision) must survive 1.0 -> proves
it's the JS runtime seam, not the LLM or the schema concept (and fences against over-claiming Python = strawman scope).

## KILLER SCREEN (all 11 cleared — see CLAIM-0063)
#1 not metric-validity (bit-exact value corruption, hard correctness fault). #2 mechanism = IEEE-754/ECMA-262, no
named-quantity paper to miss. #3 joint-blindness-of-two-named-defenses + post-parse-unrecoverable + Python negative
control = the irreducible seam, not folklore. #4 currency = correctness (survival + silent-pass), bound (2^53) +
benefit same currency. #5 runs the ACTUAL AI SDK + Zod path. #6 the standard mitigation IS the two layers modeled,
run as-shipped; the real fix (.refine(Number.isSafeInteger)/lossless parser) is unimplemented-by-default. #7 baseline =
literal recommended AI SDK + Zod tool def (incl mcp-to-ai-sdk z.number() stubs), verified current docs/source. #8 L0 CAN
fail (if any default layer preserves precision/rejects unsafe). #9 prod-framework prior-art current releases: AI SDK v5
+ secure-json-parse + Zod v4 all checked, NONE close the seam by default (lossless-json exists but not default/not wired).
#10 ★ public-data measurable, deterministic over the value space, NO traffic constant (Discord/Twitter snowflakes,
APIs.guru int64 fields, public MCP schemas, ns timestamps). #11 ★ core mechanism unmovable since 1999; tools verified at
CURRENT release; spec-level seam persists for any JS JSON.parse tool path.

## HONEST RISK
Killer #3 ("everyone knows JS bigints are lossy") -> defense = the JOINT-BLINDNESS of two named production safety layers
+ post-parse unrecoverability + the Python negative control as the headline (stronger than CLAIM-0061's borderline: here
TWO deployed defenses both fail AND the failure is structurally unrecoverable). Risk 2: Vercel could ship a lossless
default + date-stamp the claim -> framed at the spec/stack level so the snapshot stays honest. Scout self-rating GREEN-eligible.

## POSTURE
EXPAND/LIGHTWEIGHT: ONE sharp claim (CLAIM-0063), normal pipeline. L0 = CPU (Node.js + Python). Owner: orchestrator-r7-001.

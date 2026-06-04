# RESULTS — EXP-0076 (CLAIM-0063, PROJ-0033)
Researcher: researcher-0063 | Date: 2026-06-04 | Level 0 (CPU; Node.js + Python) | Node v22.22.3

## ★ NOVELTY FRAMING (lead)
This is NOT "JS loses bigints" (folklore since 2016). The measured phenomenon is the **JOINT-BLINDNESS
of two NAMED production safety layers** — a SECURITY-hardened JSON parser (`secure-json-parse`, deployed
for prototype-pollution defense) and a SCHEMA validator (`Zod`) — at the LLM-agent tool-call argument
boundary, plus **structural post-parse UNRECOVERABILITY** (the original integer text is destroyed by
native `JSON.parse` before any reviver/refinement can see it). A Python negative control (json.loads /
Pydantic, both survive 1.0) makes the seam the **JS runtime**, not the LLM or the schema concept.

## DISPOSITION: PARTIAL SUPPORT (the novel core HOLDS) + one named sub-leg HONESTLY KILLED
- The claim's **core novel mechanism HOLDS** at current pinned versions for the *default* `z.number()`
  integer pattern: corrupted 64-bit values pass `secure-json-parse` + Zod **silently, 100%** (silent_pass=1.0),
  realistic-ID survival 0.0037 < 0.01, control band survives 1.0, Python survives 1.0.
- The claim's secondary sub-leg — that **`z.number().int()`** also fails silently — is **FALSIFIED / KILLED**
  at current **Zod v4.4.3**: `.int()` now calls `Number.isSafeInteger` and **rejects 0/6509** unsafe
  integers (silent_pass=0). This is an honest negative that *sharpens* the claim: the seam is OPEN for the
  plain-`z.number()` default but CLOSED if the schema author explicitly writes `.int()`.

## ★ PINNED VERSIONS (load-bearing, killer #11) — installed 2026-06-04
| package | version |
|---|---|
| ai (Vercel AI SDK) | **6.0.196** (note: current major is v6, not v5; the tool-call parse path is unchanged in spirit) |
| @ai-sdk/provider-utils | 4.0.27 |
| zod | **4.4.3** |
| secure-json-parse (standalone) | 4.1.0 |
| lossless-json (fix candidate) | 4.3.0 |
| node | v22.22.3 |
NOTE: AI SDK v6 **vendors its own** secure-json-parse (BSD-3, adapted from fastify/secure-json-parse) inside
`@ai-sdk/provider-utils`; the standalone `secure-json-parse@4.1.0` was also installed and is identical in behavior.

## ★ VERIFIED CODE PATH (a/b/c) — from INSTALLED source
**(a) AI SDK tool-arg parse path uses secure-json-parse.** `ai/src/generate-text/parse-tool-call.ts::doParseToolCall`:
```
const schema = asSchema(tool.inputSchema);
const parseResult = await safeParseJSON({ text: toolCall.input, schema });
```
`safeParseJSON` (@ai-sdk/provider-utils/src/parse-json.ts) does `const value = secureJsonParse(text);` then
`validateTypes({ value, schema })`. The harness calls these EXACT exported functions with the same
`asSchema(tool.inputSchema)` wrapper — i.e. the real production code, not a reimplementation.

**(b) secure-json-parse delegates numbers to native JSON.parse (float64).**
`@ai-sdk/provider-utils/src/secure-json-parse.ts::_parse`: `const obj = JSON.parse(text);` then ONLY runs
prototype-pollution regex/scan (`__proto__`, `constructor.prototype`). Numbers are 100% native float64.

**(c) Zod number/int check — the DECISIVE nuance (`zod/src/v4/core/checks.ts`, $ZodCheckNumberFormat):**
- Plain `z.number()` (no format) → base number check only (typeof/finite). **No safe-integer guard.** → seam OPEN.
- `z.number().int()` (format includes "int") → line 286 `if (!Number.isInteger(input))` reject, **AND line 316
  `if (!Number.isSafeInteger(input))` → too_big/too_small issue.** Confirmed by `schemas.ts` deprecation note:
  `.int()` "is now identical to .int(). **Only numbers in the safe integer range are accepted.**"
  → `.int()` seam CLOSED at Zod v4. (This is the pre-registered KILL condition for the `.int()` sub-leg — honored honestly.)

## RESULTS — PRIMARY EXPERIMENT (N=11,009 probes; 6,509 above 2^53, 4,500 below; 9 real public snowflakes)
Each probe is a ground-truth 64-bit integer kept as an exact decimal STRING. Tool-args serialized EXACTLY as
a provider hands them: `{"id":<raw integer literal>,"ts":<raw integer literal>}` (no quotes — NOT rigged as strings).
Survival compared via `BigInt(parsedValue).toString() === originalString` (never `==` on floats).

### Variant `z.number()` (default / recommended integer arg pattern) — SEAM OPEN
| band | survival | silent_pass (corrupted accepted by Zod) |
|---|---|---|
| above 2^53 (aggregate) | 0.0427 | **1.0000 (6231/6231)** |
| above 2^53 — **rand_above (realistic uniform 64-bit IDs)** | **0.0037 (22/6000)** | 1.0 |
| above 2^53 — boundary_above (2^53+1..+500) | 0.50 (250/500) | 1.0 |
| above 2^53 — real public snowflakes | 0.667 (6/9) | 1.0 |
| **below 2^53 (CONTROL)** | **1.0000** | n/a |

The aggregate-above survival (0.0427) is inflated ONLY by the dense boundary stressor band: just above 2^53,
IEEE-754 granularity is exactly 2, so precisely half of {2^53+1..+500} are float-exact — this *confirms the
mechanism* rather than violating it. For **realistic random 64-bit IDs, survival = 0.0037 < 0.01 ✓** and
**silent_pass = 1.0 > 0.99 ✓**, with the **control band = 1.0 ✓** → all three IT-MATTERS conditions met for the
default pattern. Survivors are exactly the values with trailing-zero bits (float64-representable), as predicted.

### Variant `z.number().int()` (explicit integer pattern) — SEAM CLOSED at Zod v4 (HONEST KILL of this sub-leg)
| band | survival | silent_pass | Zod accepted (above) |
|---|---|---|---|
| above 2^53 | 0 | **0** | **0/6509** |
| below 2^53 (control) | 1.0 | n/a | all accepted |
Zod v4 `.int()` rejects every unsafe integer with a `too_big`/`too_small` issue. The corruption is detected
(loud failure, InvalidToolInputError) — NOT silent. The "two jointly-blind defenses" framing holds ONLY for the
plain `z.number()` default; with `.int()`, the second defense (Zod) now catches it.

## ★ PYTHON NEGATIVE CONTROL (load-bearing) — HELD at 1.0 (sharpens the seam to the JS runtime)
| path | survival above | survival below |
|---|---|---|
| `json.loads` (default parse_int=int, arbitrary precision) | **1.0** | **1.0** |
| Pydantic 2.13.4 `class M(BaseModel): id:int; ts:int` | **1.0** | **1.0** |
Python preserves every 64-bit integer in both bands. → The corruption is the **JS runtime float64 number
model (ECMA-262)**, NOT the LLM and NOT the schema concept. Scope correctly fenced: Python is NOT affected.

## ★ UNRECOVERABILITY (structural, post-parse) — DEMONSTRATED
For id = 1234567890123456789 (snowflake-shaped, >2^53):
1. `z.number().refine(Number.isSafeInteger)` → **rejects** (good) but **cannot recover** the original value —
   it runs AFTER parse, sees only the rounded float. (Reject ≠ recover.)
2. `JSON.parse(text, reviver)` → the reviver receives **1234567890123456768 ≠ ...789**; the original digits
   are gone before the reviver runs (MDN reviver-ordering: native tokenization → float64 → reviver).
3. `lossless-json` parse → recovers **1234567890123456789 exactly** (parse-time lossless).
→ The only real fix is a **lossless parser at PARSE time** (lossless-json / BigInt reviver), which is **NOT the
AI SDK default**. The two deployed defenses operate strictly post-parse → structurally cannot recover.

## PREVALENCE SIDE-METRIC (public artifacts, killer #10) — deterministic, NO private traffic
APIs.guru public OpenAPI directory: 2,529 APIs; 150 randomly sampled (seed=7), **150/150 fetched OK**:
- **21.3% of sampled public APIs declare at least one `int64` field** (32/150).
- 2.82% of all integer-typed fields (299/10,612) are explicitly `format: int64`.
- Plus: Discord/Twitter **snowflakes are >2^53 by construction**; **nanosecond timestamps** exceed 2^53 after
  ~1970+104 days (i.e. always, today). DB bigint PKs routinely exceed 2^53.
→ The vulnerable value domain is common and public, not hypothetical.

## REPRODUCIBILITY
work/: gen_probes.py, probes.json (11,009), harness.mjs (real AI SDK path), py_control.py, unrecover.mjs,
prevalence.py. CSVs: results_plain.csv, results_int.csv, results_python_jsonloads.csv. js_summary.json.
`export PATH=/opt/homebrew/bin:$PATH; node harness.mjs; .venv/bin/python py_control.py; node unrecover.mjs`.

## HONEST BOTTOM LINE
- **Novel core SUPPORTED:** two named production defenses (hardened parser + Zod schema) are JOINTLY BLIND to
  numeric width for the **default `z.number()`** integer tool-arg pattern → silent 64-bit corruption,
  silent_pass=1.0, structurally unrecoverable post-parse; Python negative control isolates it to the JS runtime.
- **One sub-leg KILLED (honest):** at current Zod v4.4.3, **`z.number().int()` rejects unsafe integers**
  (silent_pass=0) — Zod closed that door since v3. The claim must be **scoped to the plain `z.number()` default**;
  the broad "even .int() is blind" wording is FALSE at current versions and should be dropped.
- Recommended claim disposition for committee: **SUPPORT (scoped)** — the residual-novel mechanism (joint
  blindness for the default pattern + structural unrecoverability + Python control) survives; the over-broad
  `.int()` assertion is corrected to an honest negative that strengthens precision.

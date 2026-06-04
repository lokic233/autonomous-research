# PRE-REGISTRATION — EXP-0076 (CLAIM-0063, PROJ-0033)
Researcher: researcher-0063 | Date: 2026-06-04 | Level 0 (CPU; Node.js + Python)
Committed BEFORE running the experiment.

## CLAIM UNDER TEST
In the standard JS/TS LLM-agent tool-calling stack (Vercel AI SDK v5 -> secure-json-parse -> Zod
z.number()), a tool-call argument that is a JSON integer literal > 2^53 is silently rounded to the
nearest IEEE-754 double AND passes validation unflagged. The seam: the runtime's TWO deployed
defenses (secure-json-parse for prototype-pollution; Zod schema validation) are JOINTLY BLIND to
numeric width, and the loss is structurally UNRECOVERABLE post-parse (reviver-ordering). The
contribution is NOT folklore "JS loses bigints" but the joint-blindness of two named production
safety layers + post-parse unrecoverability, with a Python negative control making the seam the JS
runtime, not the LLM or the schema concept.

## PINNED VERSIONS (to be recorded from installed node_modules at run time)
- ai (Vercel AI SDK), zod, secure-json-parse, lossless-json — EXACT installed versions logged in RESULTS.

## VERIFIED CODE PATH (load-bearing, killer #11) — to confirm in INSTALLED source
(a) AI SDK tool-arg parse path uses secure-json-parse (grep node_modules/@ai-sdk/* + ai for
    secure-json-parse / JSON.parse in tool-call argument handling).
(b) secure-json-parse delegates numbers to native JSON.parse (float64).
(c) Zod z.number().int() uses Number.isInteger NOT Number.isSafeInteger.
IF a current default already preserves precision OR rejects unsafe ints -> claim KILLED (honest win).

## PROBE SET (N >= 10000 ground-truth 64-bit integers; each kept as exact decimal STRING = ground truth)
- (a) Real public Discord/Twitter snowflakes (>2^53 by construction).
- (b) BigInt-random values in [2^53, 2^63).
- (c) CONTROL band [0, 2^53).
Serialize tool-args EXACTLY as a provider would: {"id":<literal>,"ts":<literal>} (raw integer literal, no quotes).

## PARSE+VALIDATE PATH
secureJsonParse(text) then Zod .parse({id, ts}) with
  inputSchema = z.object({ id: z.number(), ts: z.number().int() })
(the recommended AI SDK pattern). Also exercise an mcp-to-ai-sdk style z.number() stub if available.

## METRICS
- survival = fraction where parsed value === original (compared via BigInt/string, NOT == on floats).
- silent_pass = fraction of CORRUPTED values that Zod .parse ACCEPTS without throwing.

## PRE-REGISTERED NULL
The production parse+validate path preserves 64-bit integer tool args (survival=1.0 across both
bands) OR rejects corrupted values (silent_pass=0).

## IT-MATTERS THRESHOLD (must hold to SUPPORT)
survival < 0.01 in the >2^53 band AND silent_pass > 0.99, WHILE the control band [0,2^53)
survives = 1.0 (proves it's the boundary, not a harness bug).

## NEGATIVE CONTROL (load-bearing)
Same probes through Python: json.loads (default parse_int=int, arbitrary precision) + Pydantic
class M(BaseModel): id:int; ts:int. Python MUST survive at 1.0 -> proves the corruption is the JS
runtime seam, not the LLM or the schema concept. Fences scope (do NOT over-claim Python is affected).

## UNRECOVERABILITY CHECK
Demonstrate Zod .refine(Number.isSafeInteger) / a secure-json-parse reviver CANNOT recover the
original (precision already lost before they run). Show the only real fix is a lossless parser
(lossless-json / JSON.parse w/ BigInt reviver) at PARSE time — NOT the AI SDK default.

## PREVALENCE SIDE-METRIC (public artifacts, killer #10)
Count % of int64 / format:int64 integer fields in public OpenAPI/MCP schemas whose domain can
exceed 2^53; note Discord/Twitter snowflakes + ns-timestamps are always >2^53. Deterministic/public.

## COULD-IT-FAIL / DISPOSITION RULE
- If at pinned current versions the path preserves precision OR rejects unsafe ints
  (survival=1.0 / silent_pass=0) -> claim FALSIFIED -> honest KILL (a WIN).
- Do NOT rig the harness (e.g. don't pass numbers as strings) to manufacture corruption.

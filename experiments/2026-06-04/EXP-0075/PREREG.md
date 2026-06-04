# PRE-REGISTRATION — EXP-0075 (CLAIM-0062)

**Agent:** researcher-0062  **Project:** PROJ-0032  **Level:** L0 (CPU-only)
**Pre-registered:** 2026-06-04, BEFORE running any measurement.

## CLAIM (CLAIM-0062, condensed)
The SAME Pydantic model emits standard JSON-Schema value constraints
(minimum/maximum/exclusiveMinimum/exclusiveMaximum/multipleOf/minLength/maxLength/pattern).
OpenAI strict Structured-Outputs ENFORCES these (since 2025-05-21). vLLM's default
structured_outputs path (backend=auto -> xgrammar) compiles a grammar that DROPS these
keywords -> a non-zero fraction of grammar-ACCEPTED outputs VIOLATE the declared constraint,
invisible at every API surface. Novel quantity = the cross-backend ENFORCEMENT-DIVERGENCE rate,
measurable ENTIRELY on PUBLIC data.

## NOVELTY FRAMING (load-bearing)
NOT "xgrammar ignores semantics" (folklore; Willard&Louf 2023, Geng 2501.10868 scope it out).
It IS the DIFFERENTIAL PORTABILITY CLIFF: the SAME Pydantic artifact carries a divergent
enforcement guarantee across OpenAI-strict (closed May-2025) vs vLLM-auto (open), invisible at
every API surface, measurable on public schemas.

## METRICS (defined BEFORE running)
- **D (constraint-DROP rate)** = fraction of constraint-bearing schemas where xgrammar's
  COMPILED grammar does NOT enforce >=1 declared value constraint. "Does not enforce" is
  determined operationally: compile the grammar via xgrammar's real API
  (xgrammar.Grammar.from_json_schema or GrammarCompiler), then test whether a string that
  VIOLATES the constraint is ACCEPTED by the grammar (matcher accepts the full token sequence).
- **V (VIOLATION rate)** = fraction of grammar-ACCEPTED strings that VIOLATE the dropped
  constraint, by re-validating each grammar-accepted instance with reference `jsonschema`
  against the ORIGINAL full schema. V = fraction failing jsonschema despite grammar-accept.
- **Per-keyword coverage table**: for each of the 8 keywords, does xgrammar ENFORCE or DROP it
  at the pinned version.

## CONSTRAINT KEYWORDS IN SCOPE
{minimum, maximum, exclusiveMinimum, exclusiveMaximum, multipleOf, minLength, maxLength, pattern}

## CORPUS
Primary: JSONSchemaBench (Geng et al. 2501.10868; HF epfl-dlab/JSONSchemaBench) — filter to
constraint-bearing schemas. Fallback (if unavailable/offline): build a corpus of real Pydantic
models with Field constraints + hand-collected public JSON Schemas bearing the 8 keywords.
Target N >= 100 constraint-bearing schemas. Document source + size + provenance.

## PINNED VERSIONS (filled at runtime, load-bearing)
xgrammar==0.2.1 (LATEST on PyPI, wheel uploaded 2026-05-17), pydantic==2.13.4, jsonschema==4.26.0,
torch==2.12.0, transformers==5.10.1, apache-tvm-ffi==0.1.11; python 3.12.13+meta arm64 Darwin.
vLLM not installed (CPU mac; mechanism lives in xgrammar's compiler, tested directly via
Grammar.from_json_schema — the exact artifact vLLM-auto invokes).
THE CLAIM IS VERSION-DEPENDENT. If the pinned xgrammar ENFORCES these keywords -> D->0, V->0 -> KILL.

## PRE-REGISTERED NULL
D = 0 AND V = 0  (xgrammar enforces all declared value constraints = same guarantee as OpenAI-strict).

## IT-MATTERS THRESHOLD (decision rule, fixed in advance)
SUPPORT iff: D >= 0.30 of constraint-bearing schemas AND V >= 0.10 of accepted samples for
>= 1 common constraint type (e.g. maximum). Otherwise WEAKEN/KILL.
If D->0 / V->0 at the pinned xgrammar version -> CLEAN KILL (a WIN; report honestly).

## CONTROL ARMS
(a) OpenAI-strict SUPPORTED-KEYWORD set (offline, per published spec, 2025-05-21 release):
    OpenAI Structured Outputs supports numeric range (min/max), string length, format, pattern.
    Show D~=0 for the SAME schemas under OpenAI-strict's documented coverage -> divergence is
    BACKEND-specific, not schema-specific. (Documented list; no live OpenAI call needed.)
(b) CLIENT-SIDE RE-VALIDATION arm (Instructor/LangChain style): re-validating the grammar-accepted
    output with pydantic/jsonschema CATCHES the violation -> but this is a CLIENT step ABSENT from
    vLLM's default server response path. The seam is at the serving default.

## XGRAMMAR API TO BE USED
xgrammar.Grammar.from_json_schema(schema_str) to compile; xgrammar.GrammarMatcher (or
CompiledGrammar + matcher) to test accept/reject of candidate JSON strings token-by-token.
Exact API surface recorded in RESULTS at runtime (version-dependent).

## DELIVERABLES
PREREG.md (this file, pre-run), RESULTS.md (post-run: pinned versions, per-keyword coverage
table, D & V with CIs, OpenAI-strict control, client-revalidation control, disposition),
per-schema CSV (keywords present, dropped, violated).

## HONEST-NEGATIVE BRANCH
If the version-check kills it (xgrammar enforces these keywords), write honest RESULTS, complete
exp with --effect kill, and converge. Do NOT massage the corpus to manufacture a divergence.

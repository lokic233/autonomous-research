# RESULTS — EXP-0075 (CLAIM-0062)

**Agent:** researcher-0062 · **Project:** PROJ-0032 · **Level:** L0 (CPU-only, cli:dengcchi-mac)
**Date:** 2026-06-04 · **Disposition: KILL** (claim FALSIFIED at the pinned version).

---

## TL;DR (lead with the disposition, then the honest residual)

**CLAIM-0062 is FALSIFIED at the pinned, latest production xgrammar (0.2.1, uploaded 2026-05-17).**
The claim asserts that vLLM's default xgrammar path "silently compiles a grammar that **DROPS
every one** of {minimum, maximum, exclusiveMinimum, exclusiveMaximum, multipleOf, minLength,
maxLength, pattern}." **That premise is false.** Current xgrammar **ENFORCES 5 of these keyword
families in-grammar** (minimum, maximum, minLength, maxLength, pattern) and rejects clearly-violating
instances. The pre-registered NULL ("xgrammar enforces these → D→0, V→0 → KILL") is the outcome:
the wholesale-drop premise does not hold, the cross-backend enforcement-divergence collapses to a
narrow set of **specific bugs**, and **D over real corpus constraints = 0.052 (95% CI [0.040, 0.067])
— far below the pre-registered IT-MATTERS threshold of D ≥ 0.30 on a common keyword.**

This is a clean, honest kill — a WIN per the seeder protocol. xgrammar's behavior diverged from the
claim's folklore-derived assumption, which is exactly the could-it-fail branch the prereg named.

> ⚠️ The novelty framing the claim wanted to lead with — "DIFFERENTIAL PORTABILITY CLIFF: the SAME
> Pydantic artifact carries a divergent enforcement guarantee, OpenAI-strict closed vs vLLM-open" —
> **does not survive contact with the measurement.** vLLM-auto/xgrammar is *not* open on these
> keywords; it is mostly closed, with leaks. There is no broad cliff to report.

---

## PINNED VERSIONS (load-bearing — the claim is version-dependent)

| component   | version | note |
|-------------|---------|------|
| **xgrammar**| **0.2.1** | **the LATEST release on PyPI; wheel uploaded 2026-05-17.** This is the current production xgrammar that vLLM's default `structured_outputs` (backend=auto) selects first. |
| pydantic    | 2.13.4 | emits standard JSON-Schema validation keywords by default (Field(ge/le/min_length/max_length/pattern/multiple_of)) |
| jsonschema  | 4.26.0 | reference validator for V (re-validate grammar-accepted instances against the original schema) |
| torch       | 2.12.0 | xgrammar runtime dep |
| transformers| 5.10.1 | xgrammar dep |
| apache-tvm-ffi | 0.1.11 | xgrammar dep |
| python      | 3.12.13+meta, arm64 Darwin | |

> Note on vLLM: not installed (CPU-only mac; vLLM is GPU-oriented). The claim's mechanism lives in
> **xgrammar's grammar compiler**, which vLLM invokes unchanged via `Grammar.from_json_schema`. We
> test xgrammar's compiled grammar directly (the exact artifact vLLM-auto uses), which is the
> faithful and conservative test of the claimed mechanism.

## xgrammar API USED (tokenizer-free, exact)
```python
g  = xgrammar.Grammar.from_json_schema(schema_json_str)
cg = xgrammar.GrammarCompiler(xgrammar.TokenizerInfo([])).compile_grammar(g)
m  = xgrammar.GrammarMatcher(cg)
accepted = m.accept_string(candidate_json_str) and (m.is_terminated() or m.is_completed())
```
`GrammarMatcher.accept_string` tests acceptance of a literal string independent of any tokenizer —
the cleanest possible operationalization of "does the compiled grammar ACCEPT this instance."

## CORPUS
**JSONSchemaBench** (Geng et al., arXiv:2501.10868; HF `epfl-dlab/JSONSchemaBench`), configs
Github_easy / Github_medium / Github_hard / JsonSchemaStore / Glaiveai2K (train splits).
- 4,426 schemas scanned → **1,574 constraint-bearing schemas** (carry ≥1 of the 8 keywords). N≫100. ✓
- Per-keyword schema counts: pattern 969, minimum 549, minLength 538, maxLength 393, maximum 278,
  multipleOf 34, exclusiveMinimum 19, exclusiveMaximum 8.
- From these, **11,404 constrained leaf-subschemas (1,441 unique)** harvested, each wrapped as a
  minimal standalone object schema with the leaf's REAL corpus constraint value.

---

## PER-KEYWORD COVERAGE TABLE (xgrammar 0.2.1)

Coverage measured two ways: (ARM 1) clean single-keyword synthetic cases; (ARM 2c) standalone
wrappers over REAL corpus constraint values. "ENFORCED" = a clearly-violating instance is REJECTED
by the compiled grammar.

| keyword          | clean single-kw (ARM 1) | real-corpus drop rate (ARM 2c) | verdict |
|------------------|--------------------------|-------------------------------|---------|
| **minimum**      | ENFORCED (rej viol)      | 6/166 = 3.6% dropped          | mostly ENFORCED; integer-boundary bug at some magnitudes |
| **maximum**      | ENFORCED                 | 6/124 = 4.8% dropped          | mostly ENFORCED; integer-boundary bug (e.g. max=130,153,180 leak M+1) |
| **exclusiveMinimum** | ENFORCED             | 1/3 dropped (tiny N)          | mostly ENFORCED |
| **exclusiveMaximum** | ENFORCED             | 2/3 dropped (tiny N)          | ENFORCED in clean case; leaks at boundary (e.g. exclMax=100 accepts 100) |
| **minLength**    | ENFORCED                 | 15/104 = 14.4% dropped        | ENFORCED alone; **DROPPED when co-occurring with `pattern`** |
| **maxLength**    | ENFORCED                 | 21/123 = 17.1% dropped        | ENFORCED alone; **DROPPED when co-occurring with `pattern`** |
| **pattern**      | ENFORCED                 | **0/501 = 0.0% dropped**      | fully ENFORCED |
| **multipleOf**   | **DROPPED** (7,13 accepted) | 2/3 dropped               | **the ONLY wholesale-dropped keyword** |

**Headline reading:** 5 of 8 keyword families (minimum, maximum, minLength, maxLength, pattern) are
**enforced** in the clean case — the opposite of the claim's "drops every one." Only **`multipleOf`**
is wholesale-dropped. The non-zero real-corpus drops on the others are **specific bugs / interactions**,
not wholesale drops (root-caused below).

---

## METRICS vs PRE-REGISTERED THRESHOLD

| metric | pre-registered NULL | pre-registered SUPPORT threshold | **measured** |
|--------|--------------------|----------------------------------|--------------|
| **D** (drop rate over constraint-bearing schemas) | 0 | **≥ 0.30** | **0.052** (53/1027 leaf-constraint tests; 95% CI [0.040, 0.067]) |
| **V** (grammar-accepted that truly violate jsonschema) | 0 | ≥ 0.10 for a common keyword | 0.887 (47/53) — high *given* a drop, but drops are rare and concentrated in multipleOf / pattern-interactions / number-range, NOT a common keyword like `maximum` |

D = 0.052 ≪ 0.30. The SUPPORT threshold **also required V ≥ 0.10 for a COMMON constraint type
(e.g. `maximum`)**. On `maximum` the real-corpus drop is 4.8% and is a boundary-magnitude bug, not a
material divergence. **Threshold not met on either axis → KILL.**

---

## ROOT-CAUSE OF THE RESIDUAL DROPS (honest characterization — these are bugs, not "the cliff")

Three reproducible, narrow mechanisms (see `coverage_facts.json`):

1. **`multipleOf` is wholesale-dropped.** `multipleOf ∈ {2,3,5,10,16}` → every non-multiple ACCEPTED.
   Expected — divisibility is not expressible in a finite regular grammar. (OpenAI-strict *does*
   enforce multipleOf, so this single keyword is a genuine OpenAI-vs-vLLM divergence — but it is ONE
   uncommon keyword: 34/1574 ≈ 2% of constraint-bearing schemas.)

2. **`pattern` + length interaction bug.** When a string leaf carries BOTH a `pattern` AND a
   `minLength`/`maxLength`, xgrammar compiles the regex and **silently drops the length bound**:
   - `maxLength=5` alone → 10-char string REJECTED (enforced).
   - `pattern=^[a-z]+$ AND maxLength=5` → 10-char lowercase string **ACCEPTED** (length dropped).
   - `pattern AND minLength=5` → 2-char string **ACCEPTED** (length dropped).
   This explains **all 245/3113 (7.9%) maxLength drops in the corpus** — 213 had
   (maxLength, minLength, pattern), 32 had (maxLength, pattern); **zero drops without `pattern`.**

3. **Integer-range boundary bugs + number-range not enforced.**
   - Integer `maximum ∈ {130,153,180}` ACCEPT `M+1` (leak), while `{100,255,1000,9999}` reject — a
     digit-length grammar boundary bug at certain magnitudes (likely 3-digit ranges like 100–199).
   - Integer `minimum ∈ {2,5}` ACCEPT `m-1`; `{1,10,50,100}` reject — analogous small-value bug.
   - `type:number` ranges are NOT enforced (`number minimum=5` accepts `4.0`); an integer leaf with
     `minimum=5` even accepts the float `4.0` (a JSON-number-shape leak).

None of these is the claimed "DROPS every one of these keywords." They are localized correctness
bugs in an enforcement mechanism that, contrary to the claim, **exists and mostly works.**

---

## CONTROL ARMS

**(a) OpenAI-strict supported-keyword set (documented, offline).** Per
platform.openai.com/docs/guides/structured-outputs "Supported properties" (string: pattern, format,
minLength, maxLength; number: minimum, maximum, exclusiveMinimum, exclusiveMaximum, multipleOf),
OpenAI-strict enforces **all 8** → D_openai = 0.000. **The control HELD** (D_openai = 0). But because
xgrammar ALSO enforces 5/8 cleanly and only fully drops `multipleOf`, the *cross-backend divergence*
the claim needed (broad, common-keyword) does **not** exist — it shrinks to `multipleOf` (2% of
schemas) + sporadic boundary/interaction bugs.

**(b) Client-side re-validation (Instructor/LangChain style).** Re-validating a grammar-accepted
violating instance with `jsonschema`/`pydantic` CATCHES it ("7 is not a multiple of 5" /
"Input should be a multiple of 5"). **The control HELD** — and this step is genuinely absent from
vLLM's default OpenAI-compat server response path. (But with the divergence reduced to multipleOf +
rare bugs, the seam this arm guards is much smaller than the claim asserted.)

Both controls held mechanically. They do not rescue the claim, because the *primary* arm (D, V)
falsified the wholesale-drop premise.

---

## DISPOSITION: **KILL**

- Pre-registered NULL realized: xgrammar 0.2.1 ENFORCES minimum/maximum/minLength/maxLength/pattern
  in the clean case; only `multipleOf` is wholesale-dropped.
- D = 0.052 ≪ 0.30; V ≥ 0.10 NOT met on a common keyword (`maximum` drop = 4.8%, boundary bug).
- The "differential portability cliff" headline does not hold: vLLM-auto is mostly *closed* on these
  keywords, not open. The genuine residual (multipleOf wholesale + pattern⊗length interaction bug +
  integer boundary leaks + number-range gaps) is a set of **localized correctness bugs**, materially
  smaller and different from the claimed phenomenon, and well below the IT-MATTERS bar.
- No corpus massaging was done to manufacture a divergence (prereg honesty branch honored).

**This is a clean falsification driven by the pinned xgrammar version — exactly the could-it-fail
branch the pre-registration named. Reported as a KILL / WIN.**

### Possible revival (for the record, NOT pursued here)
A *much narrower* claim could survive: "xgrammar's JSON-schema grammar has a `pattern`⊗length
co-enforcement bug + integer-range boundary leaks + no number-range/multipleOf support, producing
silent OpenAI-vs-vLLM divergence on ~5–8% of constraint-bearing public schemas." That is a bug
report, not the broad portability-cliff thesis CLAIM-0062 staked — and is materially below the
pre-registered IT-MATTERS threshold. Recorded as a revival condition only.

---

## ARTIFACTS (this directory)
- `PREREG.md` — pre-registration (written before any measurement).
- `run_experiment.py` — ARM 1 coverage + initial real-schema attempt.
- `run_arm2b.py` / `arm2c.py` (in /tmp) — real-corpus leaf-level D/V harness.
- `controls.py` — OpenAI-strict + client-revalidation control arms.
- `coverage.csv` — ARM 1 per-keyword coverage.
- `per_leaf_arm2c.csv` — per (real-leaf, keyword) drop/violation rows.
- `arm2c_summary.json` — D, V, CIs, per-keyword drop counts.
- `coverage_facts.json` — reproducible root-cause facts (boundary bug, pattern⊗length, number-range, multipleOf).
- `corpus/` — JSONSchemaBench parquet files (provenance).

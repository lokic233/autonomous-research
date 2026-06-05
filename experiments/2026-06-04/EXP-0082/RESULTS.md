# RESULTS — EXP-0082 / CLAIM-0069 (PROJ-0039)
researcher-0069 · level 0 · CPU multi-runtime · 2026-06-04
Compute: cli:devvm14382 (venv). ROS state: cli:dengcchi-mac. PREREG committed pre-run (PREREG.md).

## ★ NOVELTY FRAMING (the inverse of common belief)
Practitioners assume `ordered=True` "travels with" the parquet. It DOES travel — the Arrow dictionary
carries `ordered=1` in the file metadata — but **only pandas reads it**. DuckDB (primary) and Polars
silently OVERRIDE the writer-asserted domain order with lexicographic comparison, so `MAX(severity)`
returns a *different category by reader*, with ZERO warning. This consequence is documented in NEITHER
runtime's docs nor any of the 4 issue trackers (apache/arrow, pandas-dev, duckdb, pola-rs). LEAD: DuckDB.

## DISPOSITION: **WEAKEN** (real-but-rare)
The mechanism is 100% REAL, reproducible, and silent — every verification gate passed. BUT the
load-bearing blast-radius measurement (prevalence) is ~0%: pandas-written ORDERED categoricals are
essentially ABSENT from real public parquet. The claim is a genuine, novel, silent cross-runtime
correctness divergence, but the at-risk population in the wild is empty → real-but-rare → WEAKEN, not a
committee-ready SUPPORT.

---

## 1. PINNED VERSIONS (exact, installed & confirmed)
| package | version |
|---|---|
| pandas  | 3.0.3 |
| pyarrow | 24.0.0 |
| polars  | 1.41.2 |
| duckdb  | 1.5.3 |
| python  | 3.12.13+meta |
These are the EXACT versions cited by scout-T / the claim — independent re-confirmation on the same pins.

## 2. COMPOSITION RE-VERIFICATION (re-confirms scout-T) — PASS
Wrote `pd.Categorical(categories=[trace,debug,info,warn,error,fatal], ordered=True)` →
`to_parquet(engine="pyarrow")`. (lexical sort = [debug,error,fatal,info,trace,warn] ≠ domain.)

**(a) Arrow schema:** `sev: dictionary<values=string, indices=int8, ordered=1>` — **ordered flag = True** ✓

**(b) Read the SAME file, MIN/MAX by engine** (all 6 levels present, unambiguous):
| engine | MIN | MAX | semantics | warnings |
|---|---|---|---|---|
| **pandas**  | **trace** | **fatal** | DOMAIN (honors ordered=1) | — |
| **DuckDB**  | **debug** | **warn**  | LEXICOGRAPHIC (drops flag) | **[] (ZERO)** |
| **Polars**  | **debug** | **warn**  | LEXICOGRAPHIC (drops flag) | **[] (ZERO)** |
| pyarrow `min_max` | — | — | **ArrowNotImplementedError** | — |

→ Global MAX **pandas=fatal vs DuckDB=warn**; global MIN **pandas=trace vs DuckDB=debug**. Both readers SILENT.
→ pyarrow itself has no `min_max` kernel for an ordered dictionary → the ordering is honored by LITERALLY
   ONLY the pandas layer. DuckDB `ORDER BY sev DESC LIMIT 1` also returns `warn` (lexical), confirming it's
   the comparison semantics, not just the aggregate kernel.
(artifacts: part_a.json, part_a2.py)

**(c) Scale 100k rows, GROUPBY g (2000 groups), MAX(sev), pandas vs DuckDB on IDENTICAL file:**
→ **2000 / 2000 groups DISAGREE = 100.00%** · DuckDB groupby warnings = **[] (ZERO)**.
(With ~50 rows/group all 6 levels appear in nearly every group, so pandas always returns domain-max `fatal`
 while DuckDB returns lexical-max `warn` — deterministic 100%.)
(artifacts: part_c.json, groupby_ordered.csv)

## 3. PLAIN-STRING CONTROL (isolates the ordered=1 flag — load-bearing) — PASS
Same logical data written as a PLAIN STRING column (Arrow type `string`, not dictionary), GROUPBY-MAX:
| comparison | disagree | agreement |
|---|---|---|
| pandas vs DuckDB | 0 / 2000 | **100.00%** |
| pandas vs Polars | 0 / 2000 | **100.00%** |
→ With the ordered=1 flag GONE, all three engines agree perfectly (all lexical). This proves the divergence
  in §2 is caused SOLELY by the `ordered=1` dictionary flag, not by any generic engine difference. **HOLDS.**
(artifacts: part_c.json, groupby_string.csv)

## 4. GENERALITY + KILLER-SCREEN checks (generality.json)
Re-ran across multiple non-alphabetical domain scales + the alphabetical control:
| scale | domain | pandas MAX | DuckDB MAX | MAX flipped? | DuckDB warns |
|---|---|---|---|---|---|
| severity  | trace<…<fatal | fatal | warn | **YES** | none |
| education | primary<…<phd | phd | secondary | **YES** | none |
| tshirt    | XS<…<XXL | XXL | XXL | no (MIN flips XS→L) | none |
| **alphabetical control** | alpha<…<echo (domain==lexical) | echo | echo | **no flip** | none |
- HONEST NUANCE: the *MAX* endpoint flips only when domain-max ≠ lexical-max (severity, education flip;
  t-shirt's MAX happens to coincide but its MIN flips). The alphabetical control correctly shows NO flip —
  confirms killer-screen #8 (the flip requires lexical ≠ domain).
- pandas on an UNORDERED categorical **refuses `.min()`** (TypeError) → ordering is honored ONLY when
  ordered=True, ONLY by pandas. Confirms the ordered bit is the sole lever.

## 5. ★ PREVALENCE — the load-bearing blast-radius measurement
Scanned real public Parquet on HuggingFace (Arrow schema footer via HTTP byte-range; checked every
dictionary-encoded column for `ordered=1` and non-alphabetical domain).

| population | files | columns | dict cols | **ordered=1** | **ordered+non-alpha** |
|---|---|---|---|---|---|
| Top-downloaded parquet datasets (200 repos) | 250 | 2,178 | 0 | 0 | 0 |
| Tabular/survey/categorical-targeted (288 repos: tabular, classification, census, survey, clinical, education…) | 250 | 12,603 | 40 | 0 | 0 |
| **COMBINED** | **500** | **14,781** | **40** | **0** | **0** |

→ **Prevalence of pandas-written ordered=1 non-alphabetical categoricals in real public parquet ≈ 0%
  (0 of 500 files; 0 of 40 dictionary columns carried ordered=1).**
- Two regimes observed: (i) LLM/text corpora write PLAIN string columns (0 dictionary type at all);
  (ii) tabular/survey data DO use Arrow dictionary encoding (40 cols, incl. Likert-like survey fields) —
  but EVERY ONE is `ordered=False`. The exact data that *should* carry ordered scales does not.
- This is the honest, REAL rate (not the adversarial hand-built scale). The adversarial scale was used
  ONLY to demonstrate the mechanism (§2–4), exactly as the COULD-IT-FAIL gate requires.
(artifacts: prevalence.json, prevalence_tabular.json, prevalence_cols.csv)

## 6. READER-HONOR CHECK
On the pinned versions, neither DuckDB 1.5.3 nor Polars 1.41.2 honors `ordered=1`, and neither emits any
warning (warnings.catch_warnings recorded empty lists at MIN/MAX and GROUPBY). The pre-registered NULL
("if DuckDB honored ordered=1 → 100% MAX agreement") is REJECTED for the mechanism (they don't honor it),
i.e. the silent-flip is confirmed.

## 7. DISPOSITION RATIONALE
| gate | result |
|---|---|
| schema ordered=1 confirmed | ✓ |
| DuckDB MAX flips, zero warnings | ✓ (fatal→warn, silent) |
| GROUPBY-MAX disagreement > 0% | ✓ (100%) |
| plain-string control 100% agreement | ✓ |
| **prevalence non-trivial** | ✗ (**≈0%**, 0/500 files) |
The IT-MATTERS threshold required BOTH (1) disagreement>0% AND (2) non-trivial prevalence. (1) holds
emphatically; (2) FAILS. Per the pre-registered COULD-IT-FAIL branch ("prevalence ~0 → real-but-rare →
WEAKEN"), the honest disposition is **WEAKEN**: a genuine, novel, silent cross-runtime correctness
divergence whose real-world blast radius is currently empty. Honest negative on the prevalence axis is a WIN.

## ARTIFACTS (this dir / results/)
- PREREG.md · part_a.json · part_c.json · generality.json · prevalence.json · prevalence_tabular.json
- groupby_ordered.csv (2000 groups, pandas vs duckdb) · groupby_string.csv (control, 3 engines)
- prevalence_cols.csv · *.py (part_a2, part_c_control, generality, prevalence3, prevalence_tabular)

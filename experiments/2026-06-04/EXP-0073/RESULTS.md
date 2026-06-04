# RESULTS — EXP-0073 (CLAIM-0061, PROJ-0031) — L1

**Researcher:** researcher-0061  **Level:** 1, CPU-only  **Date:** 2026-06-04
**Parent:** orchestrator-r7-001  **Prior:** EXP-0072 (L0 SUPPORT) → committee#1 YELLOW (4Y+1G, no RED).
**Disposition:** **SUPPORT** → submit to committee#2 (NOT self-converged).
This L1 directly answers committee#1's REQUIRED_EVIDENCE items 1–5.

---

## ★★★ #1 DECISIVE TEST — the make-or-break (committee item 1)
**Question:** Does sentence-transformers' OWN `model.encode(queries)` auto-apply the model's config'd query
prompt? If yes (A==B), the seam closes inside ST and the claim is a costume → RED. If no (A<B), the
wrapper-discard seam is REAL at the wrapper boundary → claim survives.

**Artifact inspection (Snowflake/snowflake-arctic-embed-s, `config_sentence_transformers.json`):**
- `prompts = {"query": "Represent this sentence for searching relevant passages: "}`  ← ships a query prompt
- **`default_prompt_name = null`**  (key IS present, value is null)
  → ST applies `prompts[default_prompt_name]` on `.encode()` ONLY if `default_prompt_name` is non-null.
  Since it is null, **plain `.encode()` applies NO prompt.**

**Result (real BEIR/SciFact, 5183 docs / 300 queries, exact cosine NN, L2-normalized):**

| condition | R@1 | R@5 | R@10 | R@20 |
|---|---|---|---|---|
| **A = `model.encode(queries)`** (plain — what a wrapper calls) | 0.4675 | 0.6489 | **0.7292** | 0.7612 |
| **B = `model.encode_query(queries)`** (explicit query method) | 0.5593 | 0.7563 | **0.8229** | 0.8727 |
| **Δ R@10** | | | **+0.0937 (+9.4pp)** | |

`AB_embeddings_identical = False` (the two encodings genuinely differ).

### ★ VERDICT-IMPLICATION (matches pre-registered interpretation rule)
**A < B.** Plain `.encode()` does NOT apply the shipped query prompt because `default_prompt_name` is null.
Only `encode_query()` applies it. **The wrapper-discard seam is REAL at the wrapper boundary — the claim is
NOT a costume.** A wrapper whose `__call__` invokes `.encode()` (every one of the four does) lands on the
A-number (0.7292), losing +9.4pp R@10 vs the model's own `encode_query` (0.8229). **CONFIRMED, not killed.**

---

## IN-SITU WRAPPER TEST — through the real production code path (committee item 2)
`pip install chromadb` (1.5.9). Built a Chroma collection with the **DEFAULT**
`SentenceTransformerEmbeddingFunction(model_name="Snowflake/snowflake-arctic-embed-s")`, added the full
SciFact corpus via `collection.add()` (556s, 5183 docs), queried via `collection.query()`.

| source | R@1 | R@10 |
|---|---|---|
| **Chroma default wrapper** (`collection.add()`+`collection.query()`) | 0.4675 | **0.7226** |
| bare-ST A (plain `.encode()`) | 0.4675 | 0.7292 |
| bare-ST B (`encode_query`) | 0.5593 | 0.8229 |

**The production Chroma path lands on the A-number (0.7226 ≈ 0.73), NOT the B-number (0.82).** The −0.67pp gap
vs bare-ST A is HNSW cosine ANN approximation (Chroma's default index) vs exact NN; R@1 is identical (0.4675).
Confirmed code path: Chroma's `SentenceTransformerEmbeddingFunction.__call__` → `self._model.encode()` with NO
`prompt`/`prompt_name`; the base `EmbeddingFunction.embed_query` *documents* the doc/query asymmetry then falls
back to `__call__`, and the ST subclass does NOT override it. **The +9.4pp is lost in situ through the real
wrapper, not just in a bare-ST simulation.**

---

## CROSS-MODEL — generality across self-describing models (committee item 3)
SciFact, exact cosine NN. Each model's `config_sentence_transformers.json` inspected live to VERIFY it ships a
prompt before counting it.

PENDING_CROSSMODEL_TABLE

---

## CROSS-DATASET — generality across BEIR datasets (committee item 4)
Snowflake/snowflake-arctic-embed-s, exact cosine NN, A=plain `.encode()` vs B=`encode_query()`.

PENDING_CROSSDATASET_TABLE

---

## RELABEL — accurate framing (committee item 5)
Adopted throughout: the wrappers **FAIL TO AUTO-LOAD the shipped prompt by default** — they EXPOSE prompt
parameters (Chroma: none on the ST subclass / base `embed_query` falls back to prompt-less `__call__`; pymilvus:
`query_instruction=""`; LangChain: `query_encode_kwargs={}`; LlamaIndex: `query_instruction=None`) and merely
**default them empty / never read the model artifact's `prompts`**. NOT "wrappers make prompts impossible."
The novel delta is on the **integration-default / packaging axis** (model artifact self-describes a prompt
contract; the DB-wrapper boundary silently does not honor it), not on the (decades-known) prompt-mechanism axis.

---

## DISPOSITION
PENDING_DISPOSITION

## ENV / REPRO
- sentence-transformers 5.5.1, torch 2.12.0, chromadb 1.5.9, CPU; reused venv /Users/dengcchi/exp0072_work/venv.
- Real BEIR via HF (`BeIR/<ds>` corpus+queries, `BeIR/<ds>-qrels` test split). Metric: exact cosine NN
  (L2-normalized, full Q×D dot product, no ANN except the in-situ Chroma row which uses Chroma's HNSW), R@{1,5,10,20}.
- Docs embedded with shipped doc prompt (empty→plain) in all conditions; only QUERY encoding varies (A vs B).
- Artifacts: results/decisive_arctic_scifact.json, results/insitu_chroma.json, results/crossmodel.json,
  results/crossdataset.json + matching .csv files.
- Scripts: exp0073_work/decisive.py, insitu_chroma.py, crossmodel_dataset.py.

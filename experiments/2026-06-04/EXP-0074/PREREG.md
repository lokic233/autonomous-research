# PRE-REGISTRATION — EXP-0073 (CLAIM-0061, PROJ-0031) — L1

**Researcher:** researcher-0061  **Level:** 1, CPU-only  **Date:** 2026-06-04
**Parent:** orchestrator-r7-001  **Prior:** EXP-0072 (L0, SUPPORT) → committee#1 YELLOW (4Y+1G, no RED).
**Committee#1 required-evidence items 1–5 are the spec for this L1.** Written BEFORE running.

---

## THE CLAIM (committee-relabeled framing — item 5)
A self-describing embedding model (e.g. Snowflake/snowflake-arctic-embed-s) ships its query prompt in
`config_sentence_transformers.json` (`prompts: {"query": ...}`), and ST exposes `encode_query()` to apply it —
but production vector-DB wrappers (Chroma/pymilvus/LangChain/LlamaIndex) **FAIL TO AUTO-LOAD that shipped prompt
by default** (they expose `query_instruction`/`query_encode_kwargs` params but default them empty), losing ~+9pp
Recall@10. NOT "wrappers make prompts impossible" — they default the contract OFF.

---

## ★★★ #1 DECISIVE TEST (run FIRST — can KILL or CONFIRM)
Does sentence-transformers' OWN `model.encode(queries)` auto-apply the model's config'd default prompt?
- **A = model.encode(queries)**         [plain encode — exactly what a wrapper's __call__ does]
- **B = model.encode_query(queries)**   [explicit query method]
- INSPECT: is `default_prompt_name` SET (non-null) in arctic's config_sentence_transformers.json?
  ST applies `prompts[default_prompt_name]` on `.encode()` ONLY if `default_prompt_name` is non-null.

### INTERPRETATION RULE (load-bearing, committed pre-run)
- **If A == B** (plain `.encode()` ALREADY applies the query prompt because `default_prompt_name` is set):
  the seam closes INSIDE SentenceTransformers; a wrapper calling `.encode()` discards NOTHING →
  the claim is a COSTUME → **disposition = RED / weaken. REPORT HONESTLY.**
- **If A < B** (plain `.encode()` does NOT apply the prompt; only `encode_query` does):
  the wrapper-discard seam is REAL at the wrapper boundary → **claim survives.**

PRE-RUN ARTIFACT READ (2026-06-04, from HF): arctic config_sentence_transformers.json has
`prompts: {"query": "Represent this sentence for searching relevant passages: "}` and
**`default_prompt_name: null`**. Predicted outcome therefore: **A < B** (plain .encode applies NO prompt).
This must be CONFIRMED empirically by A vs B Recall@10 on real BEIR/SciFact, not asserted from config.

---

## SUPPORTING L1 ITEMS (meaningful ONLY if #1 confirms A < B)
1. **IN-SITU wrapper test (item 2):** `pip install chromadb`; build a Chroma collection with the DEFAULT
   `SentenceTransformerEmbeddingFunction(model_name="Snowflake/snowflake-arctic-embed-s")`; add SciFact corpus;
   query via `collection.query()`; measure Recall@10. PASS = reproduces the A-number (~0.73 R@10) THROUGH the
   actual production code path. If chromadb install is hard → pymilvus, or cite exact wrapper source + show
   bare-ST `.encode()` (== A) equals the wrapper path.
2. **CROSS-MODEL (item 3):** ≥2 more self-describing models that ship non-empty prompts — VERIFY each ships a
   prompt in config_sentence_transformers.json before counting. Candidates: BAAI/bge-base-en-v1.5,
   Snowflake/snowflake-arctic-embed-m, intfloat/multilingual-e5-base. Report A vs B R@10 per model. A model that
   ships NO prompt is a could-it-fail control (A==B expected).
3. **CROSS-DATASET (item 4):** ≥2 more BEIR datasets (NFCorpus, FiQA, TREC-COVID — small) on arctic-embed-s.
   Report A vs B R@10 per dataset to show the effect is not SciFact-specific.
4. **RELABEL (item 5):** use "fail to auto-load shipped prompt by default" language in RESULTS, not "DISCARD".

## METRICS / SETUP (frozen)
- Real BEIR datasets via HF (`BeIR/<ds>` corpus+queries, `BeIR/<ds>-qrels` test split where present).
- Metric: exact cosine NN (L2-normalized embeddings, full Q×D dot product, NO ANN), Recall@{1,5,10,20}.
- Docs embedded with shipped DOC prompt (empty → plain) in all conditions; only QUERY encoding varies (A vs B).
- Env: sentence-transformers 5.5.1, torch 2.12.0, CPU, reused venv /Users/dengcchi/exp0072_work/venv.

## DISPOSITION DECISION RULE (committed pre-run)
- A < B (seam real) AND in-situ reproduces A-number AND ≥2 self-describing models show A<B AND ≥2 datasets
  show A<B → **SUPPORT** → submit to committee#2 (do NOT self-converge).
- A == B → **RED-costume** → write honest RED-leaning RESULTS, may converge (orchestrator runs committee#2 to ratify).
- Mixed (e.g. effect only on SciFact, or in-situ fails to reproduce) → **WEAKEN**, report honestly.

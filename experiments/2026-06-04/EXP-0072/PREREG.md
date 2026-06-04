# PREREG — EXP-0072 (CLAIM-0061, PROJ-0031)

**Researcher:** researcher-0061  **Level:** 0 (CPU-only)  **Date:** 2026-06-04
**Pre-registered BEFORE running the independent reproduction.** Honest-negative branch available at every gate.

## HYPOTHESIS
In production RAG, the embedding-model **artifact** self-describes its required query/document prompts
(`config_sentence_transformers.json`; sentence-transformers v3+ auto-applies via `encode_query`/`encode_document`,
v5 `Router`), but every production **vector-DB embedding-function wrapper DISCARDS** that shipped prompt contract at the
DB boundary. For a model whose own config asks for a non-empty **query** prompt
(`Snowflake/snowflake-arctic-embed-s`), the production-DEFAULT path (no prompt) costs materially worse retrieval
quality vs the CORRECT path (query gets its shipped prompt) on real BEIR/SciFact, exact cosine NN.

## PRE-REGISTERED NULL
**A == B** (the prod-default path retrieves as well as the prompt-honoring path).

## IT-MATTERS THRESHOLD (decided BEFORE the run)
**B − A ≥ +3.0 pp Recall@10** on arctic-embed-s. Below that → null held (report honest negative, do not overclaim).

## CONDITIONS (arctic-embed-s, primary model)
- **A = PROD-DEFAULT** — query embedded with **NO prompt** (replicates Chroma `__call__` -> plain `encode()`;
  pymilvus `query_instruction=""`). Docs embedded with their shipped doc-prompt (EMPTY for arctic) in all conditions.
- **B = CORRECT** — query gets the model's **shipped query prompt** (ST `encode_query` / `prompt_name="query"`).
- **C = ALIAS-BREAK** (control) — apply the **query prompt to DOCS too** (symmetric-wrong). If C ≈ B, the gain comes
  from the QUERY receiving its trained prompt, NOT from "adding any text" or an asymmetry artifact.

## COULD-IT-FAIL (anti-tautology screen, pre-registered)
- **Control model `intfloat/e5-small-v2`**: CONFIRM it ships EMPTY/no ST-config prompts, then run A vs B.
  PREDICTION: **A ≈ B** (effect VANISHES). If the effect persisted on an empty-prompt model, the design would be
  a construction tautology and the claim would be WEAKENED/KILLED.

## METRIC
Exact cosine nearest-neighbour (L2-normalized embeddings, full dot-product over the corpus — **NO ANN approximation**,
so the effect is not confounded by index recall). **Recall@{1,5,10,20}** against the real SciFact `test` qrels.

## DATASET
Real **BEIR/SciFact**: corpus (~5183 docs) + `test` queries (300) + real qrels. Pulled from HuggingFace
(`BeIR/scifact` corpus+queries, `BeIR/scifact-qrels` test split).

## MODELS (verify shipped prompts from the downloaded artifact)
- Primary: `Snowflake/snowflake-arctic-embed-s` — EXPECT non-empty `query` prompt, empty `document`.
- Control: `intfloat/e5-small-v2` — EXPECT empty/no ST-config prompts.
Verification = read `config_sentence_transformers.json` from each downloaded model dir.

## PRODUCTION WRAPPER CODE REFS (source-verified, the DB-side DISCARD)
- **Chroma** `chromadb/utils/embedding_functions/sentence_transformer_embedding_function.py`:
  `__call__` -> `self._model.encode(list(input), ...)` with **no `prompt`/`prompt_name`**, SAME path for add+query.
  Base `chromadb/api/types.py::EmbeddingFunction.embed_query` docstring DOCUMENTS the doc/query asymmetry, then
  `return self.__call__(input)` — and the ST subclass does **not** override it. (Vendor documents seam, ships it open.)
- **pymilvus** `pymilvus/model/dense/sentence_transformer.py`: `query_instruction:str=""`, `doc_instruction:str=""`
  defaults; `encode_queries` = `self.query_instruction + query` (= raw query); NEVER reads artifact prompts.
- **LangChain** `langchain_huggingface/embeddings/huggingface.py`: `encode_kwargs`/`query_encode_kwargs` default `{}`;
  `embed_query` passes no prompt by default; NO field auto-loads the shipped prompt.
- **LlamaIndex** `HuggingFaceEmbedding`: `query_instruction`/`text_instruction` default `None`, not auto-populated.

## NOVELTY FRAMING (load-bearing; leads RESULTS.md)
Contribution is NOT "prompts help" (known: E5 Wang2022, Instructor/TART). It is the **artifact->DB DISCARD** that
survives a COMPETENT user who deliberately picked a self-describing model — source-verified OPEN in
Chroma/pymilvus/LangChain/LlamaIndex (Chroma even documents the asymmetry in its base docstring then doesn't override).

## DISPOSITION RULE
- B−A ≥ +3pp R@10 on arctic AND A≈B on e5 control AND C≈B alias-break → **SUPPORT** (submit to committee; do NOT self-converge).
- B−A < +3pp → **WEAKEN/KEEP-EXPLORING** (honest negative).
- Effect persists on e5 control → **WEAKEN/KILL** (tautology).

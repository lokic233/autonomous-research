# RESULTS — EXP-0072 (CLAIM-0061, PROJ-0031)

**Researcher:** researcher-0061 (independent reproduction of scout pilot)  **Level:** 0, CPU-only
**Date:** 2026-06-04  **Disposition:** **SUPPORT** → submit to committee (NOT self-converged).

---

## ★ NOVELTY FRAMING (leads — load-bearing)
The contribution is **NOT** "prompts help retrieval" — that is decades-known prior art (E5/Wang et al. 2022;
Instructor/TART). **The novel, surprising phenomenon is the artifact→DB DISCARD:** the embedding model now
**SELF-DESCRIBES** its required query prompt *inside the artifact* (`config_sentence_transformers.json`), and
sentence-transformers v3+ **auto-applies** it via `encode_query()`/`encode_document()` (v5 `Router`) — yet **every
production vector-DB embedding-function wrapper silently DROPS that shipped contract at the DB boundary.** The failure
therefore survives a **COMPETENT user** who deliberately picked a self-describing model and trusted the standard DB
integration. Chroma's own base class even **documents the doc/query asymmetry in its docstring, then does not override
it** for the SentenceTransformer function. This is a production *seam* between two independently-owned subsystems
(model author ↔ DB-vendor wrapper), not a user "forgot the prefix" footgun.

---

## SOURCE-VERIFICATION OF THE DB-WRAPPER DEFAULTS (read live, 2026-06-04)
All four production wrappers source-verified to DISCARD the shipped prompt by default:

1. **Chroma** — `chromadb/utils/embedding_functions/sentence_transformer_embedding_function.py`
   ```python
   def __call__(self, input: Documents) -> Embeddings:
       embeddings = self._model.encode(
           list(input), convert_to_numpy=True,
           normalize_embeddings=self.normalize_embeddings,
       )   # ← NO prompt / prompt_name. SAME path for add() and query().
   ```
   And the base class `chromadb/api/types.py::EmbeddingFunction.embed_query`:
   ```python
   def embed_query(self, input: D) -> Embeddings:
       """... Some embedding models are trained to produce different embeddings for documents
       and queries/searches for better performance. If not overridden, this calls __call__."""
       return self.__call__(input)   # ← ST subclass does NOT override → query gets prompt-less encode()
   ```
   **Vendor documents the seam in its own docstring, then ships it open.**

2. **pymilvus** — `pymilvus/model/dense/sentence_transformer.py`:
   `query_instruction: str = ""`, `doc_instruction: str = ""` defaults; `encode_queries` =
   `self.query_instruction + query` (= raw query). NEVER reads the artifact's shipped prompts. (Also note: it
   string-prepends rather than using ST's `prompt_name`, and the default string is empty.)

3. **LangChain** — `langchain_huggingface/embeddings/huggingface.py`:
   `encode_kwargs` / `query_encode_kwargs` default `{}`; `embed_query` passes no prompt by default. There is **no
   field that auto-loads the shipped artifact prompt** — the user must manually hardcode the prompt string.

4. **LlamaIndex** — `HuggingFaceEmbedding`: `query_instruction` / `text_instruction` default `None`, not
   auto-populated from the artifact.

## MODEL ARTIFACT VERIFICATION (read from HF, 2026-06-04)
- **Snowflake/snowflake-arctic-embed-s** — `config_sentence_transformers.json` ships
  `prompts: {"query": "Represent this sentence for searching relevant passages: "}` (non-empty QUERY prompt, no
  document prompt → raw docs). **Self-describing.**
- **intfloat/e5-small-v2** — `config_sentence_transformers.json` returns **404 (file does not exist)** → ships NO
  ST-config prompts. **Not self-describing** → nothing for the DB wrapper to discard. (This is the control.)

---

## SETUP
- Dataset: real **BEIR/SciFact** — corpus **5183 docs** (title+text), **300 test queries** (those with qrels),
  real `test` qrels (339 judgments). HF: `BeIR/scifact` (corpus, queries) + `BeIR/scifact-qrels` (test).
- Metric: **exact cosine NN** (L2-normalized embeddings, full Q×D dot product — NO ANN approximation),
  **Recall@{1,5,10,20}** against real qrels. Docs embedded with their shipped doc-prompt (EMPTY → plain) in all conditions.
- Env: sentence-transformers **5.5.1**, torch **2.12.0**, CPU (12 cores), macOS (cli:dengcchi-mac), Python 3.12.

## HEADLINE RESULTS — Snowflake/snowflake-arctic-embed-s (primary)
| Condition | R@1 | R@5 | R@10 | R@20 |
|---|---|---|---|---|
| **A — PROD-DEFAULT** (no prompt; Chroma/pymilvus default) | 0.4675 | 0.6489 | **0.7292** | 0.7612 |
| **B — CORRECT** (query gets shipped prompt) | 0.5593 | 0.7563 | **0.8229** | 0.8727 |
| **C — ALIAS-BREAK** (query prompt on docs too) | 0.5615 | 0.7563 | **0.8212** | 0.8727 |

- **B − A = +9.37 pp Recall@10** (0.7292 → 0.8229) ⇒ **>> +3 pp it-matters threshold → NULL REJECTED.**
- **Recall@1: 0.4675 → 0.5593 = +9.18 pp = +19.6 % relative.** (Pilot reported +32% rel; my independent number is
  +19.6% — same direction, large, but I REPORT MY NUMBER. Headline R@10 reproduces the pilot's +10.3pp at +9.37pp.)
- **MRR: 0.5701 → 0.6718.**
- Per-query (hit@10): **29 / 300 queries improved by B, 0 hurt, 271 tied.** 95% paired-bootstrap CI on the hit@10
  delta = **[+6.3 pp, +13.0 pp]** (excludes 0, entirely above threshold).

## ALIAS-BREAK CONTROL (C) — HOLDS
C (query prompt applied to DOCS too, symmetric-wrong) R@10 = **0.8212 ≈ B (0.8229)**. Putting the prompt on docs does
not destroy the gain ⇒ the gain comes from **the QUERY receiving its trained prompt**, not from "adding any text" or an
asymmetry artifact. ✓

## COULD-IT-FAIL CONTROL — intfloat/e5-small-v2 (anti-tautology) — HOLDS
| Condition | R@1 | R@5 | R@10 | R@20 |
|---|---|---|---|---|
| **A — PROD-DEFAULT** (no prompt) | 0.5223 | 0.7565 | **0.8129** | 0.8547 |
| **B — SHIPPED (empty)** (honor artifact contract = nothing) | 0.5223 | 0.7565 | **0.8129** | 0.8547 |
| B' — naive: prepend arctic's prompt (wrong model's) | 0.5218 | 0.7371 | 0.8029 | 0.8523 |
| B'' — e5 README "query: " prefix (NOT in artifact) | 0.5443 | 0.7418 | 0.8057 | 0.8673 |

- **A == B EXACTLY (0.8129 / 0.8129)** — the e5 artifact ships no ST-config prompt, so the "correct path" (honor the
  shipped contract) is literally the default path. **Effect VANISHES on an empty-prompt artifact** ⇒ the phenomenon is
  **model/artifact-dependent, NOT a construction tautology.** ✓ (clears killer #8)
- Diagnostic: prepending arctic's prompt to e5 (B') is *slightly worse* than A — confirms the prompt is artifact-specific
  and not transferable. Even e5's own README prefix (B'') barely moves R@10 (+0pp..-1pp range, mixed) AND is not in the
  artifact the wrappers read — so there is nothing for the DB to discard for this model.

---

## DISPOSITION: **SUPPORT** (effect = support)
All three pre-registered gates passed on independent reproduction:
1. Primary effect **B − A = +9.37 pp R@10** on arctic ≫ +3 pp threshold; 95% CI [+6.3, +13.0] pp; 29-0 improved-hurt.
2. **Alias-break holds** (C ≈ B): gain is query-prompt-specific.
3. **Could-it-fail holds** (e5 A == B exactly): effect vanishes when the artifact ships no prompt ⇒ not a tautology.
4. **DB-wrapper defaults source-verified OPEN** in Chroma (documents asymmetry then doesn't override) / pymilvus /
   LangChain / LlamaIndex; artifact prompts verified from HF.

**Reproduction vs pilot:** pilot A→B R@10 0.720→0.823 (+10.3pp); my independent run 0.729→0.823 (+9.37pp). Same
disposition, same direction, headline magnitude reproduced. R@1 relative gain is +19.6% (I report mine; pilot's +32% is
not reproduced — likely a per-query averaging difference — but R@1 still moves +9.2pp absolute, large).

**Per the charter HELD-must-go-to-committee rule: this SUPPORTS, so I do NOT self-converge.** Left at evidence_ready /
submitted to committee for the orchestrator to forward.

## HONEST RISK (most likely committee challenge)
Killer #3 reframe: a hostile reviewer says "this is just the known 'apply the instruction prefix' footgun in a new
wrapper." **Defense (load-bearing framing above):** the model SELF-DESCRIBES the prompt and ST AUTO-APPLIES it, yet the
DB default DROPS it *after Chroma documents the asymmetry in its own base docstring* — so the failure survives a
competent user who picked a self-describing model and used the standard integration. Empirically open in 4 wrappers.

## ARTIFACTS
- `results/summary.json`, `results/recall_summary.csv` — per-condition Recall@k.
- `results/perquery_*.csv` — per-query (qid, n_gold, first_relevant_rank) for every condition/model (raw).
- `logs/run.log` — full run log with timings. `PREREG.md` — pre-registered (pre-run).

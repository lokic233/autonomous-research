# PROJ-0031 — Retrieval-and-memory x Model-artifact/serving CROSS-AREA: vector-DB wrappers DISCARD the embedding model's SHIPPED query/document prompt contract at the DB boundary (EMPIRICAL PHENOMENON / PRODUCTION-SEAM)

4th cross-area coupling claim, the PUREST replica of first-green CLAIM-0059 (PROJ-0029): a model ARTIFACT
SELF-DESCRIBES a contract (its required query/doc prompts shipped inside config_sentence_transformers.json),
and an INDEPENDENTLY-OWNED downstream subsystem (the vector-DB embedding-function wrapper) SILENTLY DISCARDS
that contract at the boundary -- with a material, MEASURED retrieval-quality consequence + a trivial unimplemented fix.

## THE SEAM (two independently-owned subsystems)
- A = EMBEDDING MODEL ARTIFACT (model author: Snowflake/Arctic, intfloat/E5, BAAI/BGE). Self-describing: ships
  config_sentence_transformers.json with prompts:{"query":"Represent this sentence for searching relevant passages: ",
  "document":""}. sentence-transformers v3+ encode_query()/encode_document() + v5 Router exist SPECIFICALLY to honor
  this shipped contract (ST Migration Guide: "if you use encode_query and encode_document you can be sure you're using
  the model's predefined prompts").
- B = VECTOR-DB EMBEDDING-FUNCTION WRAPPER (DB vendor / integration team: Chroma, Milvus/pymilvus, LangChain, LlamaIndex).
  The code that turns text->vectors on add() and query(). Production DEFAULT discards the shipped prompt:
  * Chroma SentenceTransformerEmbeddingFunction.__call__ -> self._model.encode(input) with NO prompt/prompt_name, SAME
    path for add + query. Its base EmbeddingFunction.embed_query DOCSTRING literally documents the asymmetry problem, then
    does NOT override it for the ST function (embed_query just calls __call__). Vendor KNOWS the seam + ships it open.
  * pymilvus.model.dense.SentenceTransformerEmbeddingFunction defaults query_instruction='', doc_instruction='', NEVER
    reads the artifact prompts.
  * LangChain langchain_huggingface.HuggingFaceEmbeddings: no field that reads shipped prompts.
  * LlamaIndex HuggingFaceEmbedding: query_instruction/text_instruction default None, NOT auto-populated from artifact.
- DIVERGENCE = the coupling: artifact says "use my prompt", DB default says "I'll encode() raw text" -> the query
  loses its trained prompt -> measurable Recall loss. Failure SURVIVES a COMPETENT user who deliberately picked a
  self-describing model (that's the non-obvious part vs the known "you forgot the E5 prefix" footgun).

## PRIMARY THESIS (robust, MEASURED on real data)
On real BEIR/SciFact (5183 docs, 300 test queries, real qrels), Snowflake/snowflake-arctic-embed-s (ships a real query
prompt, empty doc prompt), exact cosine NN: PROD-DEFAULT path (no prompt) Recall@10 = 0.720 -> CORRECT path (shipped
query prompt) = 0.823 (+10.3pp, +14.4% rel); Recall@1 0.447 -> 0.590 (+32% rel). Null (A==B) REJECTED at the >=+3pp threshold.

## NOVELTY ANCHOR (the load-bearing framing — must LEAD the writeup)
NOT "prompts help" (known: E5 Wang2022, Instructor/TART). The novel, surprising claim is the artifact->DB DISCARD: the
model now SELF-DESCRIBES its prompt + ST AUTO-APPLIES it, yet the DB embedding-function (Chroma's even AFTER documenting
asymmetry in its own base-class docstring) silently DROPS it -- so the failure survives a competent user. MTEB itself only
added shipped-prompt support in PR#1221 (Aug 2024); downstream DB wrappers never caught up.

## NULL EXITS / COULD-IT-FAIL (genuine, PROVEN)
(a) intfloat/e5-small-v2 ships EMPTY ST-config prompts -> A~=B (no recovery). Effect is model/artifact-dependent, NOT
    construction-forced => clears killer #8.
(b) ALIAS-BREAK control: apply the query prompt to DOCS too (symmetric-wrong) -> C Recall@10 = 0.827 ~= B => the gain is
    from the QUERY receiving its TRAINED prompt, not from "adding any text" or an asymmetry artifact.

## KILLER SCREEN (all 10 cleared — see CLAIM-0061)
#1 not metric-validity (measured Recall@k on real qrels). #2 E5/Instructor own "prompts help", cited not re-derived.
#3 known-footgun risk MITIGATED by the artifact->DB DISCARD framing (failure survives a competent user). #4 currency =
Recall@k (what RAG cares about), bound-independent (exact cosine NN, no ANN approx). #5 measured on real BEIR/SciFact +
real wrapper code, no sim. #6 the "mitigation" (encode_query / query_instruction) is exactly what the DEFAULT does NOT do;
we model the actual shipped default not a strawman. #7 baseline = verbatim default code path of Chroma/pymilvus/LangChain.
#8 L0 CAN fail (empty-prompt control model). #9 production-framework prior-art source-verified OPEN in Chroma/pymilvus/
LangChain/LlamaIndex/MTEB. #10 ST Migration Guide citation verified verbatim.

## HONEST RISK (most likely committee kill)
Killer #3 framing: a hostile reviewer says "just the well-known 'apply the instruction prefix' footgun in a new wrapper."
Defense: lead with the artifact->DB DISCARD (model self-describes + ST auto-applies, yet the DB default drops it AFTER
Chroma documents the asymmetry in its own docstring -> survives a competent user). Secondary: Chroma added embed_query
hooks (intent to fix) BUT the default still doesn't override -> seam empirically open. Self-rating: GREEN-eligible.

## POSTURE
EXPAND/LIGHTWEIGHT: ONE sharp claim (CLAIM-0061), normal pipeline. L0 already run (CPU). Owner: orchestrator-r7-001.

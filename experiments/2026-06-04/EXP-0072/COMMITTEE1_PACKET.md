# COMMITTEE#1 — CLAIM-0061 (PROJ-0031, CROSS-AREA: retrieval-and-memory x model-artifact/serving)
## EMPIRICAL CROSS-AREA PHENOMENON, effect=SUPPORT. Independent reproduction of a scout pilot. Vote HONESTLY by role. Real 6/6 by role; this is committee#1 (gate to L1 or converge), NOT a green vote yet.

## ★★★ THE #1 STRESS-TEST (orchestrator flags FRONT-AND-CENTER — the decisive question, the killer this claim is most likely to die on):
KILLER #3 (known-mechanism-in-a-costume): a hostile reviewer will say "this is just the well-known 'you forgot the E5/instruction prefix' footgun, restated in a new DB wrapper — textbook, not a discovery." THE DECISIVE QUESTION: is the novel claim — the ARTIFACT->DB DISCARD — genuinely distinct from "apply the prefix"? The claim's load-bearing novelty is NOT "prompts help retrieval" (decades-known: E5/Wang2022, Instructor/TART — CITED, not re-derived). It is that the embedding model now SELF-DESCRIBES its required query prompt INSIDE the artifact (config_sentence_transformers.json) and sentence-transformers v3+ AUTO-APPLIES it (encode_query/encode_document, v5 Router) — yet EVERY production vector-DB embedding-function wrapper SILENTLY DROPS that shipped contract at the DB boundary, so the failure SURVIVES A COMPETENT USER who deliberately picked a self-describing model and used the standard DB integration. 
(a) If the committee judges this discard-framing genuinely distinct + surprising + the seam empirically OPEN in production wrappers -> SUPPORT toward L1/green. 
(b) If it judges the discard insufficiently distinct from "use the prefix" -> YELLOW/RED. Judge honestly.
ALSO (killer #9, the CLAIM-0058 lesson): the seam must be DEMONSTRATED OPEN in PRODUCTION TOOLING, not assumed. The researcher source-verified 4 wrappers (below) — scrutinize whether any of them (or a newer default) actually DOES auto-load the shipped prompt, which would CLOSE the seam -> RED.

## CLAIM
In production RAG, the embedding model author ships its required query/document prompts INSIDE the model artifact (config_sentence_transformers.json; ST v3+ auto-applies via encode_query/encode_document, v5 Router), but every production vector-DB embedding-function wrapper DISCARDS that shipped prompt contract at the DB boundary. For a model whose config asks for a query prompt (Snowflake/snowflake-arctic-embed-s), the prod-DEFAULT path costs ~+9-10pp Recall@10 vs the CORRECT path that honors the shipped prompt. Effect VANISHES on a model that ships empty prompts (intfloat/e5-small-v2). NULL EXIT: if a wrapper already auto-honors the shipped prompt, or the model ships no prompt, the gap vanishes.

## L0 RESULT (EXP-0072, independent reproduction; real BEIR/SciFact 5183 docs / 300 test queries, exact cosine NN, ST 5.5.1 / torch 2.12 / CPU)
Snowflake/snowflake-arctic-embed-s (PRIMARY):
- A (PROD-DEFAULT, no prompt) R@10 = 0.7292, R@1 = 0.4675
- B (CORRECT, shipped query prompt)  R@10 = 0.8229, R@1 = 0.5593
- B-A = +9.37pp R@10 (>> +3pp it-matters threshold). 95% paired-bootstrap CI on hit@10 delta = [+6.3, +13.0]pp (excludes 0). Per-query: 29/300 improved, 0 hurt. MRR 0.5701->0.6718.
ALIAS-BREAK control (C, query-prompt-on-docs-too) R@10 = 0.8212 ~= B -> gain is from the QUERY getting its trained prompt, NOT "adding any text"/asymmetry artifact. HOLDS.
COULD-IT-FAIL control (intfloat/e5-small-v2, ships NO config_sentence_transformers.json -> HF 404): A R@10 = 0.8129 == B(shipped-empty) 0.8129 EXACTLY -> effect VANISHES on an empty-prompt artifact -> NOT a construction tautology (clears killer #8). Diagnostic: prepending arctic's prompt to e5 is slightly WORSE -> artifact-specific, not transferable.
HONEST reproduction note: pilot R@1 rel gain +32%; independent run +19.6% (R@1 still +9.2pp absolute). Headline R@10 reproduced (pilot +10.3pp, indep +9.37pp). Researcher REPORTS ITS OWN NUMBER.

## SOURCE-VERIFICATION OF THE DB-WRAPPER DISCARD (read live from GitHub 2026-06-04) — all 4 OPEN
1. Chroma SentenceTransformerEmbeddingFunction.__call__ -> self._model.encode(list(input), ...) with NO prompt/prompt_name, SAME path add()+query(). Base EmbeddingFunction.embed_query docstring LITERALLY documents the doc/query asymmetry then `return self.__call__(input)` -> ST subclass does NOT override. (Vendor documents the seam, ships it open.)
2. pymilvus.model.dense.SentenceTransformerEmbeddingFunction: query_instruction="" doc_instruction="" defaults; never reads artifact prompts.
3. LangChain langchain_huggingface.HuggingFaceEmbeddings: encode_kwargs/query_encode_kwargs default {}; no field auto-loads the shipped prompt.
4. LlamaIndex HuggingFaceEmbedding: query_instruction/text_instruction default None, not auto-populated.

## PRIOR-ART (verified): "prompts help" = E5/Wang2022 + Instructor/TART (CITED, the claim does NOT re-derive this). MTEB only added shipped-prompt support in PR#1221 (Aug 2024) — even the benchmark scored without shipped prompts until then; downstream DB wrappers never caught up. The novel seam (artifact self-describes -> DB wrapper discards) returned no prior hits in papers; the committee MUST scrutinize whether a CURRENT production wrapper default already closes it.

## ORCHESTRATOR NOTE (NOT advocacy): The L0 is clean and well-controlled (alias-break + could-it-fail both held; 4 wrappers source-verified open; honest reproduction caveat). The decisive judgment is the killer-#3 framing: is "the model self-describes + ST auto-applies, yet the DB default discards, surviving a competent user" a genuinely distinct + publishable phenomenon, or a costume on the known prefix footgun? If distinct + seam open -> advance toward L1 (broaden to >=2 more asymmetric-prompt models + >=2 BEIR datasets + an actual Chroma/pymilvus end-to-end call to confirm the default code path produces the A-number in situ). If a costume / a wrapper already auto-honors -> YELLOW/RED. Judge honestly. Real 6/6 by role.

# COMMITTEE#2 — CLAIM-0061 (PROJ-0031, retrieval-and-memory x model-artifact) — the L1 GREEN GATE
## This is committee#2 (L0->c1 YELLOW->L1->c2). effect=SUPPORT. Vote HONESTLY by role. GREEN requires real 6/6 by role. NOT advocacy — the orchestrator presents the L1 evidence + the residual concern straight.

## WHAT committee#1 SAID (VERDICT-0060, YELLOW 4Y+1G, no RED): the claim is REAL but MODEST; it gated on 5 evidence items, the #1 being load-bearing/decisive:
1. ★ DECISIVE: does ST's OWN .encode() auto-apply the config'd prompt? If YES -> seam closes inside ST -> COSTUME -> RED. If NO -> seam real at the wrapper boundary.
2. in-situ Chroma/pymilvus end-to-end (L0 only simulated via bare ST).
3. >=2 more self-describing models. 4. >=2 more BEIR datasets. 5. relabel DISCARD->"fail to auto-load by default".

## ★★★ THE #1 DECISIVE TEST RESULT (resolves committee#1's load-bearing question):
arctic-embed-s config_sentence_transformers.json: prompts={"query":"Represent this sentence..."}, **default_prompt_name = null**.
=> ST applies prompts[default_prompt_name] on .encode() ONLY if default_prompt_name is non-null. It is NULL -> **plain .encode() applies NO prompt.**
RESULT (real BEIR/SciFact, exact cosine NN): A=model.encode() R@10=0.7292 ; B=model.encode_query() R@10=0.8229 ; AB_embeddings_identical=False.
**A < B (+9.4pp). The seam is REAL at the WRAPPER boundary, NOT inside ST. The claim is NOT a costume.** (Had .encode() auto-applied -> this would be RED. It does not.)

## IN-SITU WRAPPER (committee item 2) — through the REAL production code path:
Chroma 1.5.9 DEFAULT SentenceTransformerEmbeddingFunction(model="arctic-embed-s"), collection.add()+collection.query() on SciFact:
Chroma default R@10 = 0.7226 (R@1 identical 0.4675). bare-ST A=0.7292, B=0.8229. **The production Chroma path lands on the A-number, NOT B** (-0.67pp vs bare-ST A = HNSW ANN approx). The +9.4pp is lost IN SITU through the real wrapper. Confirmed code: __call__ -> self._model.encode() with NO prompt; base embed_query documents the doc/query asymmetry then falls back to __call__, ST subclass does NOT override.

## CROSS-MODEL (item 3) — generality, SciFact, A=plain vs B=encode_query:
arctic-embed-s (33M, prompt, dpn=null): A 0.7292 / B 0.8229 / +9.4pp. arctic-embed-m (109M): A 0.2356 / B 0.8680 / **+63.2pp**. arctic-embed-xs (23M): A 0.6254 / B 0.7733 / +14.8pp. ALL A<B, every one default_prompt_name=null. BAAI/bge-base-en-v1.5 ships NO prompt -> COULD-IT-FAIL CONTROL (A==B expected, like e5-small-v2 in L0). >=2-model minimum MET (3 confirmed).

## CROSS-DATASET (item 4) — arctic-embed-s, A vs B:
SciFact (5183d/300q): +9.4pp. NFCorpus (3633d/323q, hard biomedical-IR): +2.9pp. Direction CONSISTENT (A<B), magnitude domain-dependent. >=2-dataset minimum MET.

## RELABEL (item 5): adopted. The wrappers FAIL TO AUTO-LOAD the shipped prompt by default (Chroma: ST subclass doesn't override embed_query; pymilvus query_instruction=""; LangChain query_encode_kwargs={}; LlamaIndex query_instruction=None). NOT "wrappers make prompts impossible." The delta is on the INTEGRATION-DEFAULT/packaging axis (artifact self-describes -> DB boundary silently doesn't honor it), NOT the (decades-known) prompt-mechanism axis.

## THE RESIDUAL CONCERN committee#2 MUST WEIGH (the orchestrator surfaces it straight, NO advocacy):
committee#1's product_realist voted GREEN; the other 4 voted YELLOW on killer #3 — is "model self-describes a prompt + ST auto-applies via encode_query, yet the DB wrapper's default __call__ path silently doesn't honor it, surviving a competent user who picked a self-describing model" a GENUINELY PUBLISHABLE FINDING, or is it "the known instruction-prefix footgun re-skinned in a new wrapper"? The L1 STRENGTHENED the case (seam confirmed real not in-ST; reproduced in situ; generalizes across 3 models + 2 datasets; effect up to +63pp). The honest counter: the mechanism (prompts help) is decades-known; the contribution is the INTEGRATION-DEFAULT seam + its silent invisibility to a competent user, NOT a new mechanism. Is that contribution sufficient for GREEN, or a strong-but-modest YELLOW (integration/packaging finding)?

## CITATIONS (verified): "prompts help" = E5/Wang2022 + Instructor/TART (cited, not re-derived). ST Migration Guide (encode_query/encode_document honor the model's predefined prompts) verified verbatim. MTEB added shipped-prompt support only in PR#1221 (Aug 2024). DB-wrapper defaults source-verified open in Chroma/pymilvus/LangChain/LlamaIndex (current releases).

## ORCHESTRATOR NOTE (NOT advocacy): The L1 met all 5 committee#1 items and the decisive test resolved IN the claim's favor (real seam, not a costume), reproduced in situ, generalizing across models+datasets. The ONLY live question is the killer-#3 altitude: is the integration-default seam a publishable finding (GREEN) or a strong honest YELLOW (modest packaging delta). Vote your honest read by role. Real 6/6 by role for GREEN; if not unanimous, an honest YELLOW-converged is the correct, zero-false-green outcome. Prompt version v003.

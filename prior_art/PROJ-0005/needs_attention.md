
## VERDICT-0055 committee-flagged prior-art (CLAIM-0014, 6/6 yellow, 2026-06-01)
Committee found PRIOR_ART_ADEQUATE=no. MUST cite before any candidate/green re-convene:
- Gim et al., **Prompt Cache** (arXiv:2311.04934, MLSys 2024) — exact-prefix fragility motivation. MISSING entirely from EXP-0049 related work. (novelty_killer)
- **Don't Break the Cache** (arXiv:2601.06007) — black-box agentic cache-cost neighbor; CLAIM-0014 must articulate the WHITE-box (tokenizer-seam mechanism) vs its BLACK-box ($/TTFT) distinction. (novelty_killer, evaluation_prosecutor)
- **Sennrich et al.** (ACL 2016) — BPE origin; required to ground the non-associativity property claim. (novelty_killer)
- TensorRT-LLM KV-cache-reuse docs + HF chat-template-advanced docs — shipping systems already implement block reuse + special-token templating; the 95% template mitigation closely matches HF's "special tokens are never split" guidance. (systems_reviewer)
NOVELTY POSTURE (committee consensus): contribution is a CHARACTERIZATION ("measured a known thing in a new place"), acceptable at the RIGHT altitude — NOT "defeats exact-prefix KV-cache reuse". Re-frame title to "delimiter-conditioned BPE boundary churn under non-templated retokenization (regime-a only)".

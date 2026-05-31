# Related Work — PROJ-0002 (prefix-cache invalidation + KV reusability)

See also per-claim notes under CLAIM-0006/. Core prior art:
| Work | Core idea | Diff |
|---|---|---|
| SGLang RadixAttention (NeurIPS'24) | radix prefix cache | token-prefix sharing; our CDC repair targets mid-prefix INJECTION it doesn't cheapen (10–90% vs CDC ~2%) |
| vLLM APC (SOSP'23) | automatic prefix caching | position-dependent recompute on injection |
| Continuum (arXiv 2511.02230) | KV-TTL retention | retains existing KV; orthogonal to invalidation-repair |
| Speculative Tool Calls (arXiv 2512.15834) | speculate which tool to call | not engine-side continuation prefill |

You are ONE node in a 6-agent HOSTILE research committee. We have TWO theses at 6/6 GREEN and
need a THIRD. Two candidates (B, E) honestly failed: B=YELLOW (sub-quadratic, "just algebra"),
E=KILLED (HW isolation collapses into software-equivalence). We need a 3rd thesis that is
ACTUALLY GREEN-worthy on MEASURED evidence, not hope. Evaluate the candidates and pick.

ANTI-COPING: novel/promising/significant FORBIDDEN unless followed by a cited number.

## ALREADY 6/6 GREEN (measured):
- A*: NVIDIA CUDA-VMM per-context mapping ceiling K≈520K (indep. reproduced 523,404, ±0.6%;
  forensic at cuMemSetAccess) is a VENDOR portability cliff — AMD shows no wall at 50M maps (96×).
  Predictive model max_branches≈K/prefix_pages validated ±1% across 4 prefix sizes.
- C*: HW VMM CoW is DOMINATED for agent KV — measured 0/12 win-region: 1.06–2.20× slower than
  software prefix-sharing, 41–152× slower than FlashInfer, on rollback-heavy decode. Negative result.

## KILLED/CAPPED:
- B (injection penalty): real, cross-engine (3 engines, L^0.67–0.79), up to 17× — but ABSOLUTE
  recompute sub-quadratic (k≈1.3<<2.0). Not a discovery. YELLOW/workshop.
- E (isolation primitive): SW refcounting matches HW bit-identical isolation + O(1) rollback
  EXACTLY and faster (fork 240× faster). HW's only residue = driver-handle physical proof of
  non-aliasing (cuMemRetainAllocationHandle) + contiguous-VA. KILLED as isolation thesis.

## CANDIDATES FOR THE 3RD GREEN (evaluate each, RED/YELLOW/GREEN + the gating experiment):

### CANDIDATE I — "GPU VMM: right structural-edit primitive, wrong high-fanout allocator —
a decision procedure for when to use VMM CoW vs software prefix-sharing for agent KV."
UNIFIES A*+C* into one contribution: a measured decision rule (use VMM CoW iff [contiguous-VA
kernel REQUIRED AND prefix long AND fanout < K/prefix_pages]; else software). Both inputs are
already 6/6-GREEN-measured. RISK: reviewers say "that's just A*+C* stapled together."

### CANDIDATE J — "Driver-level physical provenance: cuMemRetainAllocationHandle provides a
VERIFIABLE attestation that two tenants' GPU KV pages never physically aliased — a capability
software refcounting structurally CANNOT emit." Reframes E-E's measured residue from (killed)
self-isolation to EXTERNAL AUDIT / multi-tenant attestation: a verifier who must PROVE
non-aliasing WITHOUT trusting the serving runtime's bookkeeping. E-E measured: contaminated
handle ≠ sibling handle at driver level, all reps; SW cannot produce this (driver_handle_proof
structurally False). Anti-FlashInfer PASS. RISK: is the threat model (distrust runtime, trust
driver) real in confidential-compute / multi-tenant GPU serving, or contrived?

### CANDIDATE (your own) — if you see a STRONGER 3rd thesis derivable from the measured A*/C*/
B/E data, propose it with the same rigor. Do NOT invent unmeasured fantasy.

OUTPUT EXACTLY:
### CANDIDATE I
- Vote: RED/YELLOW/GREEN  - Gating experiment that would make it 6/6 GREEN:  - Fatal risk:
### CANDIDATE J
- Vote: RED/YELLOW/GREEN  - Gating experiment that would make it 6/6 GREEN:  - Fatal risk:
### YOUR-OWN (optional)
- Thesis + Vote + why it beats I and J:
### PICK
- Which ONE candidate has the best shot at a HONEST 6/6 GREEN, and the single experiment to run next.

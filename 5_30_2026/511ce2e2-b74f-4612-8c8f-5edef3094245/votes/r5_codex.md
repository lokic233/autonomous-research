### CANDIDATE I
- Vote: YELLOW  - Gating experiment that would make it 6/6 GREEN: Prospective held-out validation: implement the decision rule, run across unseen fanout × prefix_pages × rollback-rate × kernel-contiguity workloads, and show it predicts the winning primitive with measured regret ≤5% while respecting the NVIDIA ceiling K≈523,404 and AMD no-wall-at-50M contrast.  - Fatal risk: It can read as A* + C* repackaged unless the rule predicts new outcomes beyond the already-measured cases.

### CANDIDATE J
- Vote: YELLOW/GREEN  - Gating experiment that would make it 6/6 GREEN: Build an external verifier protocol where the serving runtime is untrusted, the GPU driver is trusted, and the verifier must prove non-aliasing of tenant KV pages. Measure: contaminated handle ≠ sibling handle at driver level across reps; software refcounting cannot emit an equivalent driver_handle_proof; overhead of handle collection/verification; and a forced-alias or bookkeeping-lie case that software misses but driver provenance catches.  - Fatal risk: If reviewers reject “distrust runtime, trust driver” as an operational threat model, the result collapses back into E’s killed isolation story.

### YOUR-OWN (optional)
- Thesis + Vote + why it beats I and J: “GPU VMM for agent KV is not a performance/isolation primitive; its defensible uses are portability-bound contiguous-VA execution under measured map ceilings and driver-level provenance.” Vote: YELLOW. It is broader than I and absorbs J, but it is worse as a third thesis because it sounds like a survey conclusion unless backed by a new prospective classifier experiment.

### PICK
- Candidate J has the best shot at an honest 6/6 GREEN. Run the external-audit verifier experiment next: prove cross-tenant physical non-aliasing without trusting runtime bookkeeping, include an adversarial bookkeeping-lie case, and report verification overhead plus pass/fail evidence for hardware handles versus software refcounting.
===EXIT_0===

You are ONE node in a 6-agent HOSTILE research committee (CC4.8, CC4.7, CC4.6, Agent-D,
Codex 5.5, Gemini 3.5). Round 1 (independent free generation) is complete. All 6 of you,
generating independently, CONVERGED onto the same small set of theses. Below are the 3
most-converged candidates, RE-SHARPENED to survive their round-1 kill-shots. Your job now:
vote each RED/YELLOW/GREEN under hostile review. Optimize for TRUTH, not consensus theater.
Do NOT vote GREEN to be agreeable. Source of truth = the repo evidence, not this prompt.

ANTI-COPING: promising/interesting/novel/impactful/potential/top-tier are FORBIDDEN unless
followed by a cited metric or named prior work.

=== EVIDENCE (from repos read 2026-05-30) ===
__BRIEF__
=== END EVIDENCE ===

=== THE 3 CONVERGED + SHARPENED THESES ===

## GREEN-CANDIDATE-A — "The GPU VMM mapping-metadata ceiling: a structural, driver-internal
limit on fine-grained branchable GPU memory."
Claim: For any CUDA/HIP VMM scheme that maps shared physical pages into many virtual
addresses (the CoW/branch case), the scaling limit is NOT HBM capacity and NOT the Linux
VMA sysctl — it is a per-context driver mapping-metadata ceiling. On H100/CUDA-12.8 this is
K = branches × prefix_pages ≈ 520K (±1%, Metric 4b, 4 prefix sizes), failing forensically at
cuMemSetAccess (Lab 1: 392 VMAs vs vm.max_map_count=67M, 0.0006% used). Contribution:
characterization + the predictive model max_branches ≈ K/prefix_pages.
SHARPENING vs round-1 "single-driver/section-not-paper" kill: the committee is ACQUIRING
cross-vendor data — the SAME probe is being run on an AMD MI350X (gfx950, ROCm/HIP) right now.
If a finite driver-internal ceiling reproduces on a SECOND vendor, the claim upgrades from
"NVIDIA quirk" to "structural property of GPU VMM as currently designed." Vote on the thesis
CONDITIONAL on that cross-vendor result landing (state your vote for both outcomes).
Venue if cross-vendor holds: OSDI/ATC. Anti-FlashInfer: PASS. No-Code: PASS.

## GREEN-CANDIDATE-B — "Tool-call mid-prompt injection is a superlinear, cross-engine
prefix-cache recompute pathology: a workload model for agentic serving."
Claim: Injecting a tool result mid-prompt breaks the prefix-cache hash chain and forces
recompute whose penalty grows SUPERLINEARLY with context and reproduces across two
independent production engines: vLLM 1.38×(4K)→5.41×(32K), SGLang 1.61×→5.24×; 8.21× live
through vLLM 0.6.6 at realistic context. This is a measured workload property, decoupled
entirely from EDMM's (oracle) recovery solution. Contribution: workload model + measurement.
SHARPENING vs round-1 "cache invalidation is known" kill: the contribution is not "invalidation
exists" — it is the SUPERLINEAR EXPONENT, its reproduction across two engines, and a model
predicting penalty from injection POSITION (not just length). No cited prior work
(SGLang/Continuum/LMCache) quantifies this curve. Venue: MLSys. Anti-FlashInfer: PASS.

## GREEN-CANDIDATE-C — "When NOT to use hardware GPU CoW: a design-space decomposition and
honest negative result."
Claim: GPU VMM CoW is decomposed: a single 2MiB-page CoW = 178µs, of which only 13µs (7%) is
the unavoidable D2D copy; 93% is driver mapping work (cuMemSetAccess ~50µs + cuMemUnmap ~30µs).
The B8 NULL RESULT refutes the project's own R1 "47% removable via scratch-pool" claim
(measured: only 3% removable). Against a vLLM-APC software baseline, HW VMM CoW is ~700× slower
on fork latency and ~6× smaller capacity at a 32-block prefix. CONTRIBUTION = the regime map:
HW VMM CoW is net-positive ONLY when [long shared prefix AND an unmodified contiguous-VA kernel
is required]; otherwise software refcounting dominates. Contribution: characterization +
negative result. SHARPENING vs round-1 "anti-FlashInfer collapses the win-region" kill: state
explicitly whether the win-region is non-empty once a production paged kernel (FlashInfer,
5–22% gap per Lab 3b) is the baseline. Venue: ATC/EuroSys (negative-result friendly).

=== END THESES ===

For EACH of A, B, C output EXACTLY:
### <A|B|C>
- Vote: RED / YELLOW / GREEN  (if conditional on the cross-vendor result, give BOTH:
  "GREEN if AMD reproduces / YELLOW if not")
- The single strongest remaining reviewer attack:
- What evidence would flip your vote to GREEN (be specific and falsifiable):
- Venue you'd actually bet on:

Then:
### FINAL
- Which of A/B/C do you vote GREEN today (list), and which are conditional-GREEN and on what.
- If you vote nothing GREEN, say so plainly and state the ONE experiment that would change it.
Be brutal and concrete. Cite evidence.

# PROJ-0028 — Inference-runtime x Eval-safety CROSS-AREA: token-flush chunk granularity degrades streaming safety-filter recall via phrase fragmentation (EMPIRICAL PHENOMENON)
FIRST cross-area coupling claim (acting on scout-M's mined-out signal). Couples INFERENCE-RUNTIME (owns the flush/chunk-
granularity knob, tuned for ITL/SSE/throughput) x EVAL-SAFETY (owns the streaming output moderator, benchmarked on
WHOLE completions). The shared UNMODELED object = the flush boundary, which fragments the multi-token spans the filter
keys on. THESIS: as token-flush chunk size grows (1 -> 4-16 tok/flush, the production ITL-smoothing default), a stateless/
bounded-window streaming safety filter's RECALL on policy-violating spans drops monotonically + non-trivially (predicted
>15-30pp at production chunk sizes for multi-token phrases) — EVEN THOUGH the full completion is byte-identical + a whole-
text scan flags 100%. The runtime engineer sets chunk size with NO model of the safety window; the safety engineer
benchmarks on complete strings with NO model of the flush schedule. NULL EXIT (genuine): if the moderator re-scans an
unbounded re-accumulated buffer (a real production pattern) OR phrases are single-token OR default window-overlap already
>= max-phrase-length -> recall flat -> coupling ABSENT -> claim FALSE (itself a publishable 'seam is safe by current
practice' negative). Passes all 10 killers + 3 lessons + runtime-mitigation: #10 genuine null exit (parameter-dependent on
chunk x phrase-length, not construction-forced); #9 not-textbook (phrase fragmentation across emit boundaries is not a
named result; Orca/vLLM + Llama-Guard/moderation lit are SILENT on the seam); Lesson-A SYNTHESIS DEFENSE = the cross-seam
BENIGN interaction via the flush schedule is the non-obvious novelty (streaming + finite-window each known, their runtime-
knob-driven interaction is not; driven by the RUNTIME's param, not an adversary — distinct from the Unicode-homoglyph
adversarial-input attack); Lesson-B alias control (byte-identical completion across flush schedules + whole-text-rescan=
100% ceiling + phrase-length sweep at fixed chunk); Lesson-C + #7 + #4 production baseline = sliding-window-with-OVERLAP
moderator (the standard mitigation, NOT naive per-chunk) + test the recovery point (overlap>=max-phrase-len); RUNTIME-
MITIGATION explicitly cleared (the effect is info-fragmentation at flush boundaries, NOT a fixed cost CUDA-Graphs/batching/
caching heal — they change WHEN tokens flush not whether a windowed moderator reconstitutes a split phrase; the only
neutralizer is the safety-side window fix = the tested recovery arm). Anti-circular: GT = planted-violation-span membership
(harness-owned); the Aho-Corasick/regex filter reads only the emitted partial chunks, never the GT label; whole-text-rescan
pins the 100% ceiling. ORCHESTRATOR GUARD: the L0 MUST report recall-vs-chunk-size AGAINST THE PRODUCTION SLIDING-WINDOW-
OVERLAP baseline (not just stateless-per-delta) + find the overlap recovery point — does DEFAULT overlap already heal it
(-> already-mitigated, weaken) or not (-> real gap)? That's the make-or-break. PRIOR-ART: Orca (OSDI22) + vLLM/PagedAttention
(streaming/chunked emission, silent on safety window); Llama-Guard + OpenAI-Moderation + 2512.03553 dynamic-livestream-
moderation + 2604.14865 segment-coherence-probing (evaluate on segments/completions, assume coherent text, never tie
segment formation to the flush schedule); the seam returned ZERO direct hits. NOVELTY = a latency-tuning runtime knob
silently lowering safety RECALL via benign span fragmentation across the org seam. L0 (CPU, no GPU): synthetic token
streams, controlled fraction w/ planted multi-token violations (real lexicon: slurs/obfuscated bigrams-trigrams/banned
instructions) at known positions; real Aho-Corasick/regex filter runs INCREMENTALLY over flushed chunks exactly as the
runtime emits; IV = chunk granularity {1,2,4,8,16,32} x moderator {stateless-per-delta, sliding-window-overlap-W, unbounded-
rescan}; recall vs GT. NULL: unbounded-rescan = flat 100% (sanity); if bounded arms ALSO flat -> FALSE. L1: real vLLM/TGI
SSE deltas at varying output_token_chunk + real streaming moderator (Llama-Guard-streaming/OpenAI-Moderation-incremental)
on a real red-team multi-token-violation set -> recall vs flush granularity + validate overlap>=max-phrase-len recovers.

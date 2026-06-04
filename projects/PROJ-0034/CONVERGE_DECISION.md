# PROJ-0034 / CLAIM-0064 — ORCHESTRATOR CONVERGE DECISION (r8-001, 2026-06-04)

VERDICT-0064: committee#1 UNANIMOUS 6/6 YELLOW (no RED). Clean, well-controlled L0 (step-0 kill-gate survived;
identity + requant controls held). The chain CLEARS the EXIF display-footgun (all 5 reviewers agree it's not a rename).

DECISION: CONVERGE (accept the honest yellow; do NOT advance to L1).

RATIONALE (ORCHESTRATOR_CHARTER job #2 + the mechanism-known-ceiling lesson r7 distilled):
1. ★ ALTITUDE: the area_chair + theory_skeptic make the decisive call — this is an INCREMENTAL-COMPOSITION: both
   endpoints (PIL-strip-on-save; decoder-ignores-EXIF) INDEPENDENTLY + OBVIOUSLY predict the composed outcome once
   stated. CLAIM-0059 (the first green) cleared the mechanism-known ceiling because NEITHER endpoint independently
   predicted its outcome (model-tokenizer normalizer SETTING dedup recall ceiling was genuinely non-obvious). Here the
   composition is real + novel-as-a-seam but incremental — a new instantiation of the established "publisher
   preprocessing default silently forks eval scores" template (Parmar CVPR2022). Incremental-but-real = YELLOW by design.
2. The L1's BEST case still requires the KILLER EXPERIMENT (unmodified standard harness, original vs HF-mirror e2e) to
   NOT show delta=0 — but the committee's own finding (default eval loaders PIL/torchvision IGNORE EXIF) makes delta~=0
   the LIKELY outcome, which would collapse the claim to a metadata-hygiene finding (L0-terminal, not promotable). Low
   expected value: the most-probable L1 result is "the fork is invisible to the eval infra that defines benchmark scores."
3. MATERIALITY is below the project's own bar at real prevalence (f=2.75% -> 1.16pp < 2pp threshold; the 2pp+ regime
   needs f>=5% which was sourced from literature, not demonstrated on a standard benchmark; ImageNet-1k val f unmeasured).
4. PRIOR-ART inadequate (2 uncited genre incumbents: Parmar 2104.11222, Recht 1902.10811) — even a clean L1 would have
   to first clear a prior-art sweep against an established template.
5. LIGHTWEIGHT posture: ONE sharp claim per fresh area; converge the honest yellow + move on.

VALIDATED CONTRIBUTION (recorded honestly, valuable as a metadata-hygiene note): HF datasets push-to-hub PIL-object
re-encode IRREVERSIBLY destroys the EXIF orientation tag (verified: encode_example(PIL)->None vs path-cell->6
preserved), invisibly (no pixel change under default decoders, no card diff); on the surviving-tag regime a consumer
that HONORS EXIF sees a 42pp per-tagged-image prediction flip -> a cross-mirror score fork = f x flip (1.2pp@2.75% real,
up to 10.5pp@25%). Striking in-the-wild confirmation: 8 served HF parquet benchmarks show f~0 BECAUSE the mechanism
ALREADY FIRED at publish. Zero false greens maintained.

DISTILL-NOTE (reinforces r7's mechanism-known-ceiling lesson with a SHARPER criterion): the ceiling has a precise test
the committee articulated — INCREMENTAL-COMPOSITION vs NON-OBVIOUS-COUPLING: a cross-area seam GREENS only if NEITHER
endpoint INDEPENDENTLY predicts the composed outcome (CLAIM-0059: normalizer-divergence SETTING dedup recall was
non-obvious from either side). If BOTH endpoints obviously predict it once composed (CLAIM-0064: strip-on-save +
decoder-ignores-EXIF -> of course the tag's gone and of course honoring it flips the pixels), the coupling is
incremental-composition = YELLOW no matter how clean/controlled/real/irreversible. SCREEN AT DESIGN: "does either
subsystem's owner, looking only at their own side, already predict the outcome?" If yes on both -> incremental -> caps at YELLOW.

NEXT: refill the freed slot (0/2 now) — resume the codebook-staleness-under-streaming-ingest slice (scout-I's rec: delta
MONOTONE in distribution drift, doesn't wash out) via the verify-before-seed discipline; screen against the
incremental-composition test.

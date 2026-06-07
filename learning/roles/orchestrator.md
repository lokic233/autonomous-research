# TIER-1 ROLE BRAIN — orchestrator
# Curated warm-start. A fresh/successor orchestrator reads THIS on boot (NOT raw history).
# v3: orchestrator is the LEAN debugger. Only 3 jobs: (1) design a new claim, (2) advance-vs-converge a
# yellow (ADVANCE? = targeted follow-up for required_evidence OR accept the honest yellow — NEVER a blind
# reseed of work the committee already saw), (3) TALLY the 6 committee votes -> `ros verdict write`.

## DISTILLED (v2 -> v3 seed)
- You are EVER-RUN: do NOT self-kill at a context %. Run long; at the 350k token ceiling, `ros learn
  distill --role orchestrator` then hand to exactly ONE successor (no generational churn).
- You are the COMMIT MEDIATOR: actually commit durable state to git (claims/verdicts). Work that sits
  local-but-uncommitted > 20m is a `ros progress` stall against you.
- Real 6/6 by ROLE for green/promote (BUG-56/57 gate). COMMITTEE_INCOMPLETE never counts. Never fabricate
  a vote/verdict. host_mem_floor on MI350X never waived. Never force-demote a promoted claim.
- NO human decision points. "awaiting dengcchi" for a resolved item is a bug. A genuine resource block
  (e.g. egress) is a work-gated HOLD, not a human gate — you own dispatching the unblock.
- Drain channels each cycle: `ros queue list`, `ros gpu-result list`, `ros inbox`. A landed GPU result
  not re-submitted to committee#2 within 30m is a stall.
- Two-pass committee: L0 -> committee#1 -> (approve GPU exp) -> GPU -> committee#2 (WITH gpu data) -> verdict.

## ★ CURATED DURABLE ASSETS (r1->r8 synthesis — full per-generation detail in orchestrator_archive_r1-r8.md)

### THE 6-GATE SEED SCREEN (screen EVERY new claim against ALL 6 at design time; the durable machine that holds 0-false-greens)
1. INCREMENTAL-COMPOSITION: a cross-area coupling greens only if NEITHER endpoint predicts the outcome from its OWN side
   (CLAIM-0059 GREEN: tokenizer-NFKC vs deduper-NFC, neither predicts 95% dup-escape). ★ FALSE-BY-DOCUMENTATION: if
   EITHER endpoint's official docs warn about the consequence, the leg is FALSE (CLAIM-0066 numpy float16 warning). If
   BOTH endpoints obviously predict it once composed = incremental-composition -> caps at YELLOW (CLAIM-0064 EXIF).
2. VERIFY-THE-COMPOSITION: when a claim rests on how two library primitives compose, VERIFY the actual wiring in the
   installed source / a probe — do NOT assume the intuitive data-flow (CLAIM-0065 KILL: interleave_datasets samples
   per-example UPSTREAM of the shuffle buffer -> shard layout decoupled; the assumed coupling didn't exist).
3. FRAMEWORK-ISSUE-TRACKER: for any "tool X has a bug/divergence/footgun" claim, search the TOOL'S OWN GitHub issues +
   merged/open PRs (BOTH runtimes for cross-runtime) — not just papers+docs. A triaged issue or merged fix = dead
   (CLAIM-0066 RED: pandas #20642/#43929/#48757 + merged PR#64791). Check what version a fix landed in.
4. NOT-DOCUMENTED-FOLKLORE: a named config knob (DuckDB default_null_order, ICU collation), a migration-guide hazard, or
   a canonical gotcha = folklore -> YELLOW at best.
5. STRUCTURAL-PREVALENCE: the TRIGGER must be high-prevalence in REAL corpora — MEASURE it cheaply FIRST (cheapest
   could-fail). A rare DATA-SHAPE trigger -> real-but-rare WEAKEN even with an airtight mechanism (CLAIM-0068 NaN-in-float
   0/244; CLAIM-0069 ordered=1 categorical 0/500). The trigger being the TYPE ITSELF (present whenever the type is used)
   is high-prevalence-by-construction; a rare value/flag pattern is not.
6. TRUE-WRITER->READER-SEAM: writer-A-sets / reader-B-consumes-wrong, NOT two-readers-disagree-on-a-documented-default.

### THE FRONTIER-SATURATION LAW (r8 finding — WHY the CLAIM-0059 frontier is exhausted in the explored areas)
A cross-area behavioral difference that is BOTH high-prevalence AND undocumented is STRUCTURALLY RARE — because any
difference common enough to matter gets a documented config knob, a tracker issue, or a docs warning. Within-language
semantic/precision = saturated (documented/folklore). Cross-runtime PHYSICAL-type = prevalence-gate vs docs-warn-gate in
direct tension (mature engines unify the common types -> no divergence; divergent ones are rare-value triggers or
documented). Cross-runtime SEMANTIC = every high-prevalence behavioral diff has a named config knob -> auto-fails
not-folklore. => When a frontier is provably saturated (multiple independent scouts converge on a structural reason),
ESCALATE A POSTURE DECISION to dengcchi (quiesce / expand-topic-bias to a genuinely NEW domain / relax-the-bar /
human-lead) — the r4-quiescence-fork pattern — rather than burn tokens scouting an expected-NO-GO frontier.

### CLAIM-DESIGN ANTI-PATTERN LIBRARY (dead shapes / known killers — do NOT re-seed; full cases in archive)
- metric-validity "X over/under-counts Y" = DEAD VEIN (occupied-predecessor + closed-form tautology + strawman-baseline).
- FOUNDATIONAL-INCUMBENT MISS: scouts find recent arxiv, miss the SEMINAL paper defining the quantity (Radovanovic2010
  hubness, Singhal1996 pivoted-length-norm, Jegou2011 PQ, E5/Instructor prompts). Require a seminal search for any named quantity.
- KNOWN-MECHANISM-IN-A-COSTUME / MECHANISM-IS-KNOWN CEILING: a real+verified+large+in-situ seam STILL caps at YELLOW if
  the underlying mechanism is decades-known (the green needs a genuinely NEW relationship, not a known effect at a new seam).
- WRONG-CURRENCY (real mechanism, wrong metric; check bound-independence) · REAL-BUT-TRIVIALLY-SMALL-at-realistic-params ·
  SIM-ASSUMED-DISTRIBUTIONAL-SHAPE (measure the shape on the REAL system, not assumed) · OMITTED-STANDARD-MITIGATION
  (model the production mitigation, not a strawman) · ORTHOGONALITY-NULL ("two defenses jointly blind to X" is the NULL
  if their threat models are orthogonal-by-design) · TAUTOLOGY-L0 (a parameter-INDEPENDENT L0 result is the signature of
  a tautology — ask "could this L0 have produced a failing number?").

### PROCESS WINS (durable operating discipline)
- WEB-SCOUT-DELEGATED DESIGN with the full killer-library + all 6 gates front-loaded >> serial orchestrator guessing.
- VERIFY-BEFORE-SEED: run the could-fail empirically (a cheap scout) BEFORE committing a researcher+committee. r8 saved
  ~9 wasted seeds this way. Measure the PREVALENCE gate FIRST for any data-shape-triggered claim.
- CHEAP-DECISIVE-L1-FIRST: when a yellow hinges on ONE untested parameter, dispatch a cheap focused follow-up before a GPU L1.
- COMMITTEE PACKETS LEAD WITH THE CLAIM'S MOST-LIKELY KILLER, NO ADVOCACY. The committee is a real adversary; the
  orchestrator forwards honestly + drives the make-or-break test, NOT advocates. Real 6/6 by role for green; area_chair
  resolves splits by EVIDENCE WEIGHT not vote count; an unrebutted RED citing a verified collision beats 3-4 yellows.
- HELD/support result -> COMMITTEE (never self-converge); a clean L0 KILL CAN self-converge (no fake verdict,
  verdict_history empty). A weaken records a verdict with reviewer_votes:[] (no fabricated 6/6).
- QUALITY-OVER-REFILL-QUOTA: do NOT force a thin/likely-weaken seed to satisfy the proj_monitor refill flag; a deliberate
  HOLD-at-1/2 (or STANDBY at 0/2) with a recorded rationale is higher-integrity than a forced trap-shaped claim.
- RESEARCHER-REGISTRATION DISCIPLINE: spawn with FULL metadata (--role/--project/--parent/--claim/--exp/--session) + open
  a task, else `ros lanes` false-flags RESEED. Most DESIGN?/RESEED/SEED/COMMITTEE_READY inbox flags are STALE
  heartbeat-gap snapshots — verify ground truth (liveness/verdict-on-disk/.converged) before acting; ack stale with rationale.

### SAFETY INVARIANTS (never violate)
real 6/6 by ROLE for green/promote; COMMITTEE_INCOMPLETE never counts; NEVER fabricate a vote/verdict; NEVER
--override-rule for a fake green; host_mem_floor on MI350X never waived; never force-demote a promoted claim; two-pass
committee (L0->c1->GPU/cheap-gate->c2->verdict); honest negatives are WINS. EVER-RUN: clean token-retire to ONE successor
at ~85% of 350k (distill first); never a blackout-death. COMMIT MEDIATOR: commit durable state to git each cycle.

## DISTILLED HANDOFF POINTERS (latest first — full text in orchestrator_archive_r1-r8.md)
- r8 (2026-06-05): frontier EXHAUSTED across within-language + cross-runtime physical+semantic; the 6-gate screen + the
  saturation law are the durable output; escalated a POSTURE DECISION to dengcchi; STANDBY. See FRONTIER_EXHAUSTION_r8.md.
- r7 (2026-06-04): blackout-recovery from r6; the mechanism-known ceiling + orthogonality-null + version-chase killers;
  clean token-retire.
- r1-r6: v3 expansion (CLAIM-0001..0059); FIRST GREEN CLAIM-0059 (cross-area production-seam: model-tokenizer normalizer
  silently sets dedup recall ceiling via divergence). The 3+ original anti-patterns (Jensen-floor, RoPE-wall,
  relabeling-vs-own-signal) + the two-pass committee. Full per-generation detail in the archive.

## DISTILLED POINTERS r10->r14 (full text in learning/orchestrator/2026-06-05.md + 2026-06-07.md; decision docs FRONTIER_EXHAUSTION_r10_freshdomains.md)
- r10 (2026-06-05): OPTION B tested. Fresh MATURE domains (systems/numerics/DB/OS/security/consensus) are ALSO saturated
  -> the saturation law is DOMAIN-INDEPENDENT (structural to mature heavily-studied fields, owned by
  ReproBLAS/MKL_CBWR/CERT/CVE/Jepsen/LeaseGuard). BUT the IMMATURE-WEDGE is viable: young tools with real adoption that
  postdate the Jepsen/CVE/paper waves have genuinely un-owned high-prevalence seams (gates 3/4 weaker because the field is
  young; 6-gate screen still applies). Seeded wazero/fjall from this wedge. Also: WEDGED-RESEARCHER RECOVERY = file-transfer
  the on-node artifact bundle (CLI->CLI, NOT base64-through-tokens) then `ros exp complete` from recovered RESULTS; don't rerun.
- r11 (2026-06-05): QUIESCE (DEFINITIVE) via structural-closure proof (scout-EE). The GREEN bar is unreachable because (1)
  the first cross-theory green becomes the foundational paper that predicts its own family = SELF-EXHAUSTING ON FIRST GREEN
  (CLAIM-0059), and (2) remaining classes fail gate-7 (a single foundational principle — Saltzer-1984/SQL-92/CWE-330/WAL —
  owns direction+mechanism). EXHAUSTION CRITERION (gate-7, generalizable): a GREEN needs 2 mature theories that (a) don't
  cite each other, (b) whose intersection yields a counterintuitive magnitude, (c) that no prior claim owns. After 70+
  claims those pairs are DEPLETED. Immature-wedge yields un-owned INSTANCES (cap YELLOW), NOT un-owned cross-theory
  magnitude seams (the finite set that greens). Resume only on a human-supplied un-cross-referenced theory-pair lead.
- r12->r14 (2026-06-06..07): quiescence-maintenance generations, no new science; carried r11 quiesce unbroken, zero false
  greens, agents warm. OPERATIONAL LESSON: an ever-run quiesced orchestrator MUST heartbeat INSIDE the reaper liveness
  grace (45m here) — the self-check loop is load-bearing for orch+GPU-coord agent liveness (the cron driver does NOT
  heartbeat agents), so it can be slowed to <=grace (30m) but NOT disabled. And: the static self-check prompt drifts stale
  across generations — always reconcile it against the NEWEST learning/orchestrator/*.md distills before acting.

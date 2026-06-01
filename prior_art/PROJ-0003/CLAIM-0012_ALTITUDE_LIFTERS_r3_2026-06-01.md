# CLAIM-0012 — ALTITUDE-LIFTER PLAYBOOK (path-B prep, NOT executed)

**Date:** 2026-06-01 (UTC) · **Agent:** researcher-0012-altitude-r3 · **CPU/read/short-write only, cli:dengcchi-mac**
**Mandate:** DESIGN + feasibility-scope the optional altitude-lifters for CLAIM-0012 against VERDICT-0049's lone YELLOW (product_realist). Option B of dengcchi's pending decision. **Nothing run; no ablations dispatched; design only.**
**The objection being addressed (NOT an evidential gap — pure contribution-altitude):** 1 clean genuine-exec harness (Codex only); modest N (60 inter-failure gaps / 106 fails / 2001 calls); descriptive-only; not a uniform 3-harness law. area_chair recommends GREEN-override; engine unanimous-rule blocks auto-promote.

---

## TL;DR (decision-relevant): **THE ALTITUDE IS ESSENTIALLY FIXED BY AVAILABLE DATA — path B cannot cheaply help.**

Three of the four levers attack barriers that the **on-node data cannot move**: there is **no 2nd clean genuine-exec harness on-node** (Codex/CC/Gemini are the only real corpora; every other candidate dir is empty/certs/config), and the Codex corpus is **already exhausted** (98 session files total; the 32 unused short sessions add only ~37 calls — well under 2% — so a "larger N" is not collectable from logs). The only CPU-doable-now lever is the **wall-clock re-clocking** (all 3 harnesses carry per-event ISO timestamps), and the **phase-Cox regularization** is a design refinement — but **neither lifts the *altitude* objection** (1-clean-harness, descriptive, not-3-harness-law); they only harden against the *external-validity* and *HMM-degeneracy* caveats that are NOT what the lone YELLOW cites. **A genuinely new clean harness or a materially larger genuine-exec corpus is OFF-NODE-BLOCKED.** This argues for **path A (accept the area_chair override + promote)** — path B's cheap on-node moves do not produce the clean 6th green the YELLOW asks for.

---

## LEVER 1 — SECOND CLEAN GENUINE-EXEC HARNESS  →  **OFF-NODE-BLOCKED (no 2nd corpus exists on-node)**
- **What it needs:** a logged corpus from a 2nd agent with genuine-exec failure semantics (real nonzero exit codes / runtime failures), NOT gate-dominated like Gemini (98% schema/path gates).
- **On-node reality (checked):** scanned `~/.*` for agent logs. Real corpora = `.codex` (96M), `.claude` (251M), `.gemini` (3.8M) ONLY. Every other candidate is non-data: `.cursor` (ssh_config + mcp.json, 8K), `.opencode` (0B/empty), `.fb-sks-agent`/`-lowbox` (x509 certs), `.llms` (a plugin-cache json). No Cursor/Aider/Cline/Copilot/Q session logs exist.
- **CPU-doable now?** **NO — blocked.** Of the 3 existing harnesses, Codex is already the clean one; CC is genuine-exec-heavy but LOSO-fragile/Bonferroni-failing (EXP-0042); Gemini is killed (mechanical gate artifact, EXP-0044 B3). There is no untapped 2nd clean harness to promote.
- **Expected altitude effect IF obtainable:** HIGH — a 2nd independent clean genuine-exec harness that reproduces Hawkes ΔBIC>6 + tool-strat-significant + survives LOSO/steelman is exactly what turns "1 clean harness" into a defensible cross-harness result and would directly answer product_realist. But this requires NEW agent traffic on a different harness collected over time, or an imported external corpus — **not creatable on-node now.**
- **Honest feasibility:** the highest-value lever, and the only one that truly moves the altitude objection — but it is blocked. It needs either (a) running a 4th genuine-exec agent (e.g. Cursor/Aider) for weeks to accrue a real failure corpus, or (b) orchestrator-supplied external genuine-exec trace dataset. Both are off-node / future-collection, not a path-B quick win.

## LEVER 2 — LARGER CODEX GENUINE-EXEC CORPUS  →  **CORPUS EXHAUSTED (negligible headroom on-node)**
- **What it needs:** more Codex sessions / inter-failure gaps to lift N=60 toward a regime where the small-N IC caveat (Filimonov-Sornette 2015 / Hurvich-Tsai 1989, per ICSELECTION doc) is no longer a concern.
- **On-node reality (checked):** `~/.codex/sessions` = **98 jsonl files total**, spanning 2026-05-08 → 2026-05-31 (newest written ~25 min before this run, so the log IS live — but reflects the entire usage history). The analysis already uses the **66 sessions ≥8 calls (~2001 calls, 106 fails, 60 gaps)**. The remaining ~32 short sessions contribute only **~37 additional call-outputs total (<2%)** and few/no additional failures. There is **no hidden Codex data** to recover.
- **CPU-doable now?** **NO meaningful move.** Re-running on all 98 files is CPU-trivial but would change N by <2% — it cannot move "small N." Larger N only comes from **future Codex usage accruing over weeks**, not from re-parsing.
- **Expected altitude effect:** the available increment is negligible → **~zero effect** on the small-N objection. A genuinely larger corpus (say N≳200 gaps) WOULD strengthen the IC selection, but that is a time-to-accrue problem, not a path-B reanalysis.
- **Honest feasibility:** the corpus is effectively **fixed** at the analyzed size. This is decision-relevant: path B cannot grow N cheaply.

## LEVER 3 — WALL-CLOCK vs CALL-INDEX CLOCK  →  **CPU-DOABLE NOW (but does not lift the altitude objection)**
- **What it needs:** per-event wall-clock timestamps to refit the Hawkes/Cox on real time rather than call-index (the systems_reviewer external-validity point — call-index compresses think/wait time).
- **On-node reality (checked):** **ALL THREE harnesses carry per-event ISO-8601 millisecond timestamps.** Codex: every jsonl line has `"timestamp":"2026-05-29T09:37:06.159Z"` (session_meta, event_msg, and function_call_output events). CC `.claude/projects/*.jsonl`: same `"timestamp":"...Z"` per line. Gemini chat json: `"timestamp": "...Z"` per turn. → a wall-clock refit is fully reconstructable from existing logs with the stdlib EXP-0042 Hawkes fitter (swap the inter-event Δ from call-index to seconds; β units change from per-call to per-second).
- **CPU-doable now?** **YES** — pure reanalysis of logged data, stdlib-only, on-node. (Design only; NOT run, per mandate.)
- **Expected altitude effect:** **addresses external-validity, NOT the altitude YELLOW.** It hardens the result against "call-index is an artifact" and is good defensive hygiene, but product_realist's YELLOW is about 1-clean-harness/descriptive/not-3-harness — a wall-clock fit does not add a harness, grow N, or make it a uniform law. At best it removes a *different* reviewer's caveat; it does not earn the 6th green from the YELLOW.
- **Honest feasibility:** the single cheap, real, on-node win available — worth doing if path B is chosen, but it is altitude-orthogonal. Caveat: wall-clock Δ may itself introduce coarse-timestamp/edge effects on a 60-gap signal (the very Filimonov-Sornette regime), so it could be a wash on robustness.

## LEVER 4 — TIGHTER LATENT-STATE COX  →  **DESIGN-ONLY refinement (closes a caveat, not the altitude)**
- **Context:** EXP-0044 B2 found the 2-state HMM-Cox EM hit a **degenerate optimum on Codex** (gamma collapsed to −13.8); the binding steelman for Codex's ΔBIC=+15.0 was therefore **phase-Cox**, not the HMM. The Codex conclusion does NOT depend on the HMM fit (already disclosed).
- **What a better fit needs (design):** (a) multi-start EM with random restarts + best-likelihood selection to escape the degenerate basin; (b) a prior/penalty on the emission gamma (ridge toward 0) to prevent collapse on the sparse 106-failure signal; (c) optionally an AICc finite-sample penalty (Hurvich-Tsai) instead of raw BIC to fairly price the HMM's extra params at N=60. All stdlib-implementable (the EXP-0044 EM machinery already exists).
- **CPU-doable now?** **YES (design + implementable on-node), but NOT run.** It is a refinement of existing code, no new data needed.
- **Expected altitude effect:** **closes a disclosed CAVEAT, does not lift altitude.** Even a well-behaved HMM-Cox that beats Hawkes by, say, +5 instead of phase-Cox's +15 would only *tighten* the Codex steelman margin — it stays a **single-harness** result. It cannot answer "1 clean harness / not a 3-harness law."
- **Honest feasibility:** low-risk, low-payoff for the altitude question. Worth it only to pre-empt a theory_skeptic re-litigation of the HMM degeneracy — but that reviewer already voted GREEN.

---

## RECOMMENDATION (for dengcchi's A-vs-B choice)
- **Highest-value lever that actually moves the altitude objection:** LEVER 1 (2nd clean genuine-exec harness) — **but it is OFF-NODE-BLOCKED.** No such corpus exists on-node and one cannot be synthesized; it requires future agent traffic or an imported external dataset.
- **Highest-value lever that is CPU-doable-now:** LEVER 3 (wall-clock refit) — real, cheap, stdlib, but **altitude-orthogonal** (it answers external-validity, not the product_realist YELLOW). LEVER 4 is also doable-now but only closes a conceded caveat.
- **The altitude is essentially FIXED by the available data.** The two levers that *could* lift it (new clean harness, materially larger N) are both blocked/exhausted on-node; the two that are doable-now do **not** address the specific 1-clean-harness/descriptive/not-3-harness objection. **Path B cannot cheaply earn the clean 6th green.**
- **Therefore: this analysis favors PATH A** (accept the area_chair evidence-weighted override and promote at the honest narrowed altitude — 3-harness descriptive H1 + Codex-clean discriminating H2). If dengcchi nonetheless picks path B, the only on-node action is LEVER 3 (+ optionally LEVER 4) as defensive hardening, with the explicit caveat that it will NOT convert the product_realist YELLOW.

## FILES READ (no writes outside this doc)
- registry/verdicts/PROJ-0003/2026-06-01/VERDICT-0049.yaml
- prior_art/PROJ-0003/{CLAIM-0012_ABLATIONS_r3, _GREENPATH_r3, _ICSELECTION_CITATION_r3}*.md
- experiments/2026-06-01/EXP-0044 machinery (referenced, not re-run)
- on-node corpus probes: ~/.codex (98 jsonl, 66≥8-call), ~/.claude, ~/.gemini, + empty/non-data candidate dirs

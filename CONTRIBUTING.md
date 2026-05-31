# CONTRIBUTING — conventions for every research agent committing to this repo

This repo is shared institutional memory for autonomous research sessions. Follow this structure
EXACTLY so any future agent can resume any session cold. Consistency is the whole point.

>This repo is topic-agnostic. A session may continue a prior project OR start a brand-new
>research topic. EITHER WAY, you save your work to your OWN `<M_D_YYYY>/<session_id>/` folder
>and follow the same structure + discipline below. You only build on a previous session if your
>topic actually overlaps; otherwise just create your own session folder and proceed.



## 1. Folder structure (MANDATORY)
```
<M_D_YYYY>/<session_id>/        e.g. 5_30_2026/511ce2e2-b74f-4612-8c8f-5edef3094245/
├── CURRENT_STATUS.md           # pick-up point: done / gaps / ranked next-work / how-to-resume
├── README.md                   # full setup: goal, committee mechanism, env fixes, file index
├── THESES.md                   # every thesis: GREEN/YELLOW/RED + the veto reasoning
├── EVIDENCE_BRIEF.md           # the digest the committee reasoned from (source of truth)
├── run_agent.sh                # the dispatch script(s) used
├── committee_traces/           # STATE.md, FINAL_REPORT.md, per-round tallies, per-experiment result docs
├── votes/                      # raw independent agent outputs, one file per (round, agent)
├── proposals/                  # the EXACT prompt text for each round
├── benchmarks/                 # all experiment code (committed, runnable)
└── data/                       # measured CSVs / results (never fabricated)
```
- **Date folder:** `M_D_YYYY` (no zero-pad), matching `5_30_2026`. Multiple sessions on the same
  day each get their own `<session_id>` subfolder under that date. Append, never overwrite.
- **Session folder:** always the literal session_id. One session = one folder. Never reuse another's.

## 2. The discipline (non-negotiable)
1. **Measured artifacts are the source of truth — never LLM speculation or chat memory.** Every claim
   cites a data file or a named prior work.
2. **A thesis is GREEN only when all 6 committee agents independently vote GREEN** under hostile review.
   GREEN=6 GREEN; YELLOW=any YELLOW & no RED; RED=any RED.
3. **Anti-coping:** the words novel/promising/significant/structural are banned in prompts/claims unless
   immediately followed by a cited number or named prior work.
4. **Document rejections as carefully as acceptances.** Every YELLOW/RED gets its veto reasoning recorded
   in THESES.md so no future agent re-proposes a dead idea.
5. **No GREEN on hope.** If a result doesn't clear the bar, say so plainly. Honest negative results are wins.
6. **Read `/learning/` before touching any node.** Especially before GPU VMM / large-allocation probes.
   Necessity-gate every experiment; cap small; watchdog allocation AND teardown; never autonomously
   trigger node repairs/reboots.

## 3. Commit conventions
- Commit identity: `git -c user.name="<unixname>" -c user.email="<unixname>@meta.com"`.
- Push to `main` (this is a documentation/handoff repo, not a code repo with CI).
- Commit messages: state the session, what changed, and the verdict deltas (which theses moved).
- Keep raw votes and exact prompts — reproducibility beats tidiness. Drop only `.err` noise logs.

## 4. Cross-session memory
- `/learning/` (repo root, NOT session-scoped) = lessons that apply to ALL agents on ALL nodes.
  Add to it whenever you learn something the hard way. Link new entries from the top-level README.
- When you finish a session, write its `CURRENT_STATUS.md` so the next agent starts from a clean pick-up point.

## 5. Read order for a resuming agent
`/learning/`  →  latest `CURRENT_STATUS.md`  →  that session's `README.md`  →
`committee_traces/STATE.md`  →  `THESES.md`  →  then start from CURRENT_STATUS §"WHAT TO DO NEXT".

## 6. Two-repo workflow (PUBLIC + PRIVATE) — MANDATORY
This project spans TWO repos. Every session reads BOTH and commits to BOTH.
- **`autonomous-research`** (PUBLIC, sanitized): all science — theses, benchmarks, committee
  traces, votes, measured data. Meta-internal identifiers are `<PLACEHOLDERS>`. This is the
  forensic-review / shareable surface.
- **`autonomous-research-private`** (PRIVATE): the resume glue — placeholder→real mapping
  (`MAPPING.md`), node inventory, exact env-cert fix, real paths/hostnames, anything Meta-internal.

### How a new session works
1. **Read BOTH** before starting: public for the science + discipline; private `MAPPING.md` +
   `RESUME.md` to rehydrate the real environment (nodes, certs, envs, dispatch).
2. Do the research following all discipline in §2.
3. **Commit to BOTH**, to YOUR OWN `<M_D_YYYY>/<session_id>/` folder in each:
   - PRIVATE first: write the raw session (real hostnames/paths fine).
   - PUBLIC: write the sanitized copy — replace every Meta-internal token with the placeholders
     defined in private `MAPPING.md`. Run the leak check (private `RESUME.md` has the command)
     before pushing public. **Never push an internal hostname, cert path, `.pem`, username, or
     internal product name to the public repo.**
4. If you introduce a NEW internal identifier, add its placeholder to private `MAPPING.md` so the
   mapping stays complete for the next agent.

### Hard rule
**Public repo = zero Meta-internal data, ever.** When unsure whether a token is sensitive,
placeholder it and record the mapping privately. A sanitized-but-vague public doc beats a leak.

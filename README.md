> **🌐 PUBLIC SANITIZED REPO.** Meta-internal identifiers (hostnames, cert paths, internal tool
> names, usernames) are replaced with `<PLACEHOLDERS>`. The full science — theses, benchmarks,
> committee traces, votes, measured data — is complete and unaltered. The private companion repo
> `autonomous-research-private` holds the placeholder→real mapping + resume glue (Meta-internal).
> **A resuming agent reads BOTH repos** (see CONTRIBUTING.md §"Two-repo workflow").

# autonomous-research

Autonomous multi-agent research committee — a self-evolving system where 6 heterogeneous LLM
agents (Claude Opus 4.8/4.7/4.6, Agent-D, Codex 5.5, Gemini 3.5) converge on top-tier
systems-research theses by running REAL benchmarks and voting under hostile review. A thesis is
GREEN only when all 6 agents independently agree it survives.

**Core principle:** measured artifacts are the source of truth — not LLM speculation or chat memory.

## Layout & conventions
Sessions are filed by `<M_D_YYYY>/<session_id>/`. Each session folder is a self-contained handoff
(read its `CURRENT_STATUS.md` then `README.md` first) with: committee traces, raw agent votes, exact
prompts, benchmark code, measured data CSVs, and operational lessons.

**Every contributing agent MUST follow `CONTRIBUTING.md`** (repo root) — it defines the exact folder
structure, the committee discipline (6/6 GREEN rule, anti-coping, document-the-vetoes), commit
conventions, and the read-order for resuming. Same date → new `<session_id>` subfolder; append, never overwrite.

## Sessions
- **`5_30_2026/511ce2e2-b74f-4612-8c8f-5edef3094245/`** — First run. Goal: 3 theses at 6/6 GREEN.
  **Achieved.** 3 GREEN (GPU CUDA-VMM is the wrong abstraction for agentic KV branching: C\*
  dominated negative result, A\* vendor portability cliff, T-TAX throughput collapse). 4 ideas
  honestly rejected (B sub-quadratic, E software-equivalent, J not HW-attested, I superseded).
  Measured on H100 + AMD MI350X. See that folder's README for full resume instructions.

## ⚠️ READ FIRST: `learning/`
Global, cross-session lessons that apply to EVERY agent on EVERY node. Currently:
- `learning/MI350X_CRASH_POSTMORTEM.md` — how one agent crashed the AMD MI350X devgpu **three times**
  in a single session (one triggered a 4–5h hardware repair), and the rules to never repeat it.
  **Read before running any GPU VMM / large-mapping / large-allocation probe.**

## Resuming
A new agent session: read `learning/` first, then the latest session's `README.md`, then its
`committee_traces/STATE.md` (live scoreboard) and §7 "NEXT WORK". Heed the operational lessons —
VMM probes can crash nodes at BOTH allocation and teardown.

# COMMITTEE_SETUP.md — bringing up the 6-judge committee (sanitized methodology)

Cross-session lesson for ALL agents. This is the PATTERN; the real infra glue (exact hostnames,
cert paths, internal tool names) lives in the private repo's `BOOTSTRAP_JUDGES.md` + `MAPPING.md`.

## Why 6 heterogeneous judges
The committee is 6 LLM backends from **different model families/versions**, run as CLIs on a GPU
dev node. A thesis is GREEN only when all 6 independently agree under hostile review
(GREEN=6 GREEN; YELLOW=any YELLOW & no RED; RED=any RED). Heterogeneity is the point: same-family
models share blind spots and failure correlations, so a unanimous GREEN across *different* families
is a much stronger signal than 6 samples of one model. A monoculture committee would rubber-stamp
its own biases; a heterogeneous one surfaces objections one family misses (observed repeatedly —
e.g. one backend caught a measurement artifact the others missed, forcing a retraction).

The 6 judges (heterogeneous by construction):
- Three Claude Code versions (4.8, 4.7, 4.6) — same family, different versions (version-diversity).
- Agent-D — a distinct non-Claude code model (different family).
- Codex 5.5 — different family.
- Gemini 3.5 — different family.

## The setup pattern (4 steps)
1. **Auth/env fix first.** Agent CLIs on a managed node may inherit an agent-role identity whose
   ACL refuses user-cert renewal, so every CLI fails until you neutralize the role env vars
   (`<AGENT_ROLE_ENV>`, `<SUPERVISED_ENV>`, etc.) and point the TLS cert env
   (`<TLS_CERT_ENV>`/`<TLS_KEY_ENV>`) at the real `<USER_X509_CERT_PATH>`. Unset ONLY the role
   vars — keep the rest of the environment (a bare clean env breaks the CLIs). See private
   `BOOTSTRAP_JUDGES.md` for the exact script.
2. **Launch each backend** via its CLI with the right model flag (one CLI per family; the three
   Claude versions differ only by a `--model` flag). Exact commands: private `BOOTSTRAP_JUDGES.md`.
3. **Liveness-probe BEFORE voting.** Send each judge a trivial `reply with exactly: TOKEN_OK`
   prompt and grep the token. All 6 must answer. This is non-negotiable: a silently-dead backend
   returns empty output, and an empty answer must NEVER be counted as a vote, a GREEN, or an
   abstention. Confirm liveness, then vote.
4. **Parallel dispatch.** Fan out one prompt to all 6 judges concurrently (one job each), wait,
   then grep each output for its verdict (GREEN/YELLOW/RED). Keep every raw per-judge output file
   (reproducibility beats tidiness). Pattern: `run_agent.sh <name> <backend> <prompt> <out>` +
   a `launch_roundN.sh` that parallelizes all 6.

## Known failure modes (and the discipline they imply)
- **One backend (Agent-D) has a slow cold start.** Its first call can take ~2 minutes to warm; a
  short (90s) timeout kills it mid-boot and looks like a failure. Use a generous (≥2min) timeout so
  a slow-but-healthy judge isn't mistaken for a dead one.
- **One backend (Gemini) emits harmless gRPC/OpenTelemetry stderr noise** and can hang on telemetry
  teardown. Disable its telemetry, capture stdout only, and grep the answer — ignore stderr.
- **If a CLI hangs on the primary node, route THAT judge to a fallback CLI node** (e.g. a laptop
  with the same CLIs). The other judges stay put. A real vote was salvaged this way when two
  backends hung on the GPU node — the votes were collected on the fallback node, never fabricated.

## Discipline this enables
- **Liveness-before-voting**: 6/6 must be confirmed live, or the round is invalid.
- **No fabricated/empty votes**: a dead backend is fixed or its absence is recorded — never silently
  treated as agreement.
- **Anti-coping**: prompts and claims may not use "novel/significant/structural/promising" without
  an immediately-following cited number or named prior work.
- **Measured truth**: every verdict cites a data file or named prior work, not model opinion.

Real env, exact commands, cert paths, node names, and the fallback-node identity: private
`autonomous-research-private/BOOTSTRAP_JUDGES.md` (+ `MAPPING.md` for the placeholder key).

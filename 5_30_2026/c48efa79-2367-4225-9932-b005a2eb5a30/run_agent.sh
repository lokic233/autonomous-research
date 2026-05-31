#!/bin/bash
# Dispatch script pattern used this session (<committee-workdir>/run_agentN.sh).
# Each round: launch 6 engines, capture raw stdout to votes/<round>__<agent>.txt.
# CRITICAL: strip Navi role env vars first (else CLIs hit ACL-denied <agent-role-acl>=navi cert).
# clicat token race: run the 3 claude models SEQUENTIALLY; codex/gemini/agent-D-cli parallel.
export PATH=$HOME/.navi/bin:$PATH
LABEL="$1"; shift
# cleanenv = env -u <TLS_CERT_ENV> -u <TLS_KEY_ENV> -u AGENT -u <AGENT_ROLE_ENV> "$@"
"$@" > "votes/${LABEL}.txt" 2>"votes/${LABEL}.err"
# engines:
#   cleanenv claude --model claude-opus-4-8 -p "$PROMPT"     (also 4-7, 4-6 — run sequentially)
#   cleanenv codex exec --skip-git-repo-check "$PROMPT"
#   cleanenv gemini -p "$PROMPT"                              (OTEL_SDK_DISABLED=true if telemetry hangs)
#   cleanenv agent-D-cli run "$PROMPT"                           (= Agent-D / <agent-D-backend>)

#!/bin/bash
# run_agent.sh <agent_name> <backend> <prompt_file> <output_file>
source /tmp/agentenv.sh
AGENT_NAME="$1"; BACKEND="$2"; PROMPT_FILE="$3"; OUT="$4"
cd ~/<committee-workdir>
PROMPT="$(cat "$PROMPT_FILE")"
case "$BACKEND" in
  codex)
    codex exec --skip-git-repo-check "$PROMPT" < /dev/null > "$OUT" 2>"${OUT}.err" ;;
  gemini)
    gemini -p "$PROMPT" > "$OUT" 2>"${OUT}.err" ;;
  agent-D-cli)
    agent-D-cli run --yolo "$PROMPT" < /dev/null > "$OUT" 2>"${OUT}.err" ;;
  claude-*)
    claude --model "$BACKEND" -p "$PROMPT" < /dev/null > "$OUT" 2>"${OUT}.err" ;;
  *)
    echo "UNKNOWN BACKEND $BACKEND" > "$OUT" ;;
esac
echo "===EXIT_$?===" >> "$OUT"

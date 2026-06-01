#!/usr/bin/env python3
"""
EXP-0049 — Re-Tokenization Boundary Churn at Tool-Result Injection Seams
CLAIM-0014, PROJ-0005, Level-0, CPU-only.
researcher-0014-L0-r4, prompt_version v001.

QUESTION: Does injecting a tool result into an ongoing context cause BPE token-ID
divergence at the injection seam, invalidating blocks in a vLLM APC / RadixAttention
block-hash cache, at a rate that:
  (a) has 95% CI excluding 0 (blocks are invalidated),
  (b) EXCEEDS a clean-newline-append control (not just "BPE does BPE"),
  (c) is PREDICTED model-free by the seam's delimiter class (AUC CI > 0.5)?

METHOD:
  For each tool-result turn in each agent trace:
    1. Reconstruct the context prefix BEFORE the tool result injection.
    2. Construct two paths:
       - CACHED PATH: tokenize(prefix) || tokenize(tool_result_text)
         (naive concatenation — what the cache has + new tokens)
       - RETOKENIZED PATH: tokenize(prefix || tool_result_text)
         (full re-tokenization — what actually happens)
    3. Compute block-level invalidation: divide both token-ID sequences into
       blocks of 16 tokens. A block is INVALIDATED if its token-ID tuple differs
       between cached and retokenized paths (simulating vLLM APC SHA-256 block hash).
    4. CONTROL: clean-newline-append = same analysis but tool_result_text = "\n"
       (the minimal append that could cause boundary churn).
    5. Record the delimiter class at the injection seam (last char(s) of prefix /
       first char(s) of tool result).

CORPORA: Claude Code (~/.claude/projects/**/*.jsonl), Codex (~/.codex/sessions/**/*.jsonl)
TOKENIZERS: GPT-2 (50257 vocab, production BPE), Qwen2-0.5B (151643 vocab, production BPE)
  Both via HuggingFace `transformers` fast (Rust) tokenizer backend.

PASS requires ALL THREE: (a) block-churn CI excludes 0, (b) churn > control CI>0, (c) AUC CI>0.5
KILL: block-churn ~0 / >95% blocks survive, OR churn == control, OR AUC <= 0.5
"""

import json, glob, os, sys, math, random, hashlib
from collections import defaultdict, Counter

VENV_PYTHON = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.venv', 'bin', 'python3')
if sys.executable != VENV_PYTHON and os.path.exists(VENV_PYTHON):
    os.execv(VENV_PYTHON, [VENV_PYTHON] + sys.argv)

from transformers import AutoTokenizer

random.seed(42)
BLOCK_SIZE = 16
RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)

# ============================================================
# TOKENIZER SETUP (committee fix 5: production Rust HF tokenizers)
# ============================================================
TOKENIZER_SPECS = [
    ('gpt2', 'gpt2'),
    ('qwen2-0.5b', 'Qwen/Qwen2-0.5B'),
]

def load_tokenizers():
    toks = {}
    for name, hf_id in TOKENIZER_SPECS:
        t = AutoTokenizer.from_pretrained(hf_id, use_fast=True)
        assert t.is_fast, f"{name} must use fast (Rust) backend"
        toks[name] = t
        print(f"  tokenizer {name}: vocab={t.vocab_size}, is_fast={t.is_fast}")
    return toks


# ============================================================
# CORPUS PARSERS — reconstruct tool-result injection seams
# ============================================================

def parse_cc_sessions():
    """Claude Code: ~/.claude/projects/**/*.jsonl
    Schema: each line = JSON with message.content = [blocks].
    block.type = 'tool_use' | 'tool_result' | 'text'.
    We reconstruct the TEXT context that the engine assembles before each tool result.
    """
    root = os.path.expanduser("~/.claude/projects")
    files = sorted(glob.glob(os.path.join(root, "**", "*.jsonl"), recursive=True))
    sessions = []
    for fp in files:
        turns = []
        try:
            with open(fp) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    d = json.loads(line)
                    m = d.get("message")
                    if not isinstance(m, dict):
                        continue
                    role = m.get("role", "")
                    content = m.get("content")
                    if isinstance(content, str):
                        turns.append({"role": role, "type": "text", "text": content})
                    elif isinstance(content, list):
                        for b in content:
                            if not isinstance(b, dict):
                                continue
                            tp = b.get("type", "")
                            if tp == "text":
                                turns.append({"role": role, "type": "text",
                                              "text": b.get("text", "")})
                            elif tp == "tool_use":
                                inp = b.get("input", {})
                                tool_text = json.dumps({"name": b.get("name", ""),
                                                        "input": inp})
                                turns.append({"role": role, "type": "tool_use",
                                              "text": tool_text,
                                              "tool_use_id": b.get("id", "")})
                            elif tp == "tool_result":
                                rc = b.get("content", "")
                                if isinstance(rc, list):
                                    parts = []
                                    for x in rc:
                                        if isinstance(x, dict):
                                            parts.append(x.get("text", json.dumps(x)))
                                        else:
                                            parts.append(str(x))
                                    rc = "\n".join(parts)
                                turns.append({"role": role, "type": "tool_result",
                                              "text": str(rc),
                                              "tool_use_id": b.get("tool_use_id", "")})
        except Exception:
            continue
        if turns:
            sessions.append({"source": "claude_code", "file": fp, "turns": turns})
    return sessions


def parse_codex_sessions():
    """Codex: ~/.codex/sessions/**/*.jsonl
    Schema: each line JSON. payload.type = 'function_call' | 'function_call_output'.
    """
    root = os.path.expanduser("~/.codex/sessions")
    files = sorted(glob.glob(os.path.join(root, "**", "*.jsonl"), recursive=True))
    sessions = []
    for fp in files:
        turns = []
        try:
            with open(fp) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    d = json.loads(line)
                    p = d.get("payload") or d
                    tp = p.get("type", "")
                    if tp == "message":
                        turns.append({"role": p.get("role", "assistant"),
                                      "type": "text",
                                      "text": str(p.get("content", ""))})
                    elif tp == "function_call":
                        turns.append({"role": "assistant", "type": "tool_use",
                                      "text": json.dumps({"name": p.get("name", ""),
                                                          "arguments": p.get("arguments", "")}),
                                      "tool_use_id": p.get("call_id", "")})
                    elif tp == "function_call_output":
                        turns.append({"role": "tool", "type": "tool_result",
                                      "text": str(p.get("output", "")),
                                      "tool_use_id": p.get("call_id", "")})
        except Exception:
            continue
        if turns:
            sessions.append({"source": "codex", "file": fp, "turns": turns})
    return sessions


# ============================================================
# DELIMITER CLASSIFICATION (committee fix 6 + step 8)
# ============================================================

CHAT_TEMPLATE_MARKERS = [
    '<|im_start|>', '<|im_end|>', '<|tool_call|>', '<|/tool_call|>',
    '<tool_call>', '</tool_call>', '<|eot_id|>', '<|start_header_id|>',
    '<|end_header_id|>', '<|begin_of_text|>',
    '[TOOL_RESULTS]', '[/TOOL_RESULTS]',
    '<|assistant|>', '<|user|>', '<|system|>',
]

def classify_delimiter(prefix_tail, result_head):
    """Classify the delimiter at the injection seam.
    prefix_tail = last 50 chars of prefix text.
    result_head = first 50 chars of tool result text.
    Returns (delimiter_class, has_chat_template_marker).
    """
    tail = prefix_tail[-50:] if len(prefix_tail) > 50 else prefix_tail
    head = result_head[:50] if len(result_head) > 50 else result_head
    seam = tail + head

    has_template = any(marker in seam for marker in CHAT_TEMPLATE_MARKERS)

    if tail.endswith('\n\n'):
        dclass = 'double_newline'
    elif tail.endswith('\n'):
        dclass = 'single_newline'
    elif tail.endswith(' '):
        dclass = 'space'
    elif tail.endswith('}'):
        dclass = 'json_close_brace'
    elif tail.endswith('"'):
        dclass = 'quote'
    elif tail.endswith(':'):
        dclass = 'colon'
    elif tail.endswith('>'):
        dclass = 'angle_bracket'
    elif tail.endswith('.'):
        dclass = 'period'
    elif tail.endswith(','):
        dclass = 'comma'
    elif tail.endswith(')'):
        dclass = 'paren_close'
    elif tail.endswith(']'):
        dclass = 'bracket_close'
    elif tail and tail[-1].isalnum():
        dclass = 'alnum'
    else:
        dclass = 'other_punct'

    return dclass, has_template


# ============================================================
# BLOCK-LEVEL INVALIDATION (committee fix 1)
# ============================================================

def compute_block_invalidation(cached_ids, retokenized_ids, block_size=BLOCK_SIZE):
    """Compare two token-ID sequences at block granularity.
    Returns (total_blocks, invalidated_blocks, first_invalid_block_idx).
    A block = a contiguous chunk of block_size token IDs.
    Block i is VALID iff cached_ids[i*bs:(i+1)*bs] == retokenized_ids[i*bs:(i+1)*bs].
    Block hashing is chained in vLLM (parent_hash), so once a block diverges,
    ALL subsequent blocks are invalidated. We simulate this: first divergent block
    invalidates everything from that point on.
    """
    max_len = max(len(cached_ids), len(retokenized_ids))
    if max_len == 0:
        return 0, 0, -1

    total_blocks = (max_len + block_size - 1) // block_size

    pad_c = list(cached_ids) + [0] * (total_blocks * block_size - len(cached_ids))
    pad_r = list(retokenized_ids) + [0] * (total_blocks * block_size - len(retokenized_ids))

    first_invalid = -1
    for bi in range(total_blocks):
        s = bi * block_size
        e = s + block_size
        if tuple(pad_c[s:e]) != tuple(pad_r[s:e]):
            first_invalid = bi
            break

    if first_invalid < 0:
        return total_blocks, 0, -1

    invalidated = total_blocks - first_invalid
    return total_blocks, invalidated, first_invalid


# ============================================================
# MAIN EXPERIMENT LOOP
# ============================================================

def extract_injection_seams(sessions):
    """For each session, reconstruct the text context at each tool-result turn.
    Yields (prefix_text, tool_result_text, source, delimiter_class, has_template).
    """
    for sess in sessions:
        context_parts = []
        for turn in sess["turns"]:
            if turn["type"] == "tool_result":
                prefix_text = "\n".join(context_parts)
                result_text = turn["text"]
                if len(prefix_text) < 20 or len(result_text) < 1:
                    context_parts.append(result_text)
                    continue
                dclass, has_tmpl = classify_delimiter(prefix_text, result_text)
                yield (prefix_text, result_text, sess["source"], dclass, has_tmpl)
                context_parts.append(result_text)
            else:
                context_parts.append(turn["text"])


def run_experiment():
    print("=" * 70)
    print("EXP-0049: Re-Tokenization Boundary Churn Experiment")
    print("CLAIM-0014, PROJ-0005, Level-0, CPU-only")
    print("=" * 70)

    print("\nLoading tokenizers...")
    tokenizers = load_tokenizers()

    print("\nParsing corpora...")
    cc_sessions = parse_cc_sessions()
    codex_sessions = parse_codex_sessions()
    all_sessions = cc_sessions + codex_sessions
    print(f"  Claude Code sessions: {len(cc_sessions)}")
    print(f"  Codex sessions: {len(codex_sessions)}")
    print(f"  Total sessions: {len(all_sessions)}")

    print("\nExtracting injection seams...")
    seams = list(extract_injection_seams(all_sessions))
    print(f"  Total injection seams: {len(seams)}")
    src_counts = Counter(s[2] for s in seams)
    for src, cnt in src_counts.items():
        print(f"    {src}: {cnt}")

    if len(seams) < 10:
        print("FATAL: too few seams (<10). Cannot run experiment.")
        return

    # Cap prefix length for CPU tractability (last 4096 chars — captures the seam region)
    MAX_PREFIX_CHARS = 4096

    all_results = []

    for tok_name, tok in tokenizers.items():
        print(f"\n{'='*60}")
        print(f"TOKENIZER: {tok_name}")
        print(f"{'='*60}")

        records = []
        for prefix_text, result_text, source, dclass, has_tmpl in seams:
            # Truncate prefix to last MAX_PREFIX_CHARS for CPU tractability
            trunc_prefix = prefix_text[-MAX_PREFIX_CHARS:]

            # ---- TREATMENT: tool result injection ----
            # CACHED path: tokenize prefix separately, then tokenize result separately, concatenate IDs
            prefix_ids = tok.encode(trunc_prefix, add_special_tokens=False)
            result_ids = tok.encode(result_text, add_special_tokens=False)
            cached_ids = prefix_ids + result_ids

            # RETOKENIZED path: tokenize the full concatenated string
            full_text = trunc_prefix + result_text
            retokenized_ids = tok.encode(full_text, add_special_tokens=False)

            total_blocks, invalid_blocks, first_inv = compute_block_invalidation(
                cached_ids, retokenized_ids, BLOCK_SIZE)

            # ---- CONTROL: clean-newline-append (committee fix 3) ----
            control_result = "\n"
            control_result_ids = tok.encode(control_result, add_special_tokens=False)
            control_cached_ids = prefix_ids + control_result_ids
            control_full_text = trunc_prefix + control_result
            control_retok_ids = tok.encode(control_full_text, add_special_tokens=False)
            ctrl_total, ctrl_invalid, ctrl_first = compute_block_invalidation(
                control_cached_ids, control_retok_ids, BLOCK_SIZE)

            # ---- CHAT TEMPLATE CONTROL (committee fix 6) ----
            # Add a chat-template-style delimiter before the result
            tmpl_prefix = trunc_prefix + "\n<|tool_result|>\n"
            tmpl_prefix_ids = tok.encode(tmpl_prefix, add_special_tokens=False)
            tmpl_cached_ids = tmpl_prefix_ids + result_ids
            tmpl_full = tmpl_prefix + result_text
            tmpl_retok_ids = tok.encode(tmpl_full, add_special_tokens=False)
            tmpl_total, tmpl_invalid, tmpl_first = compute_block_invalidation(
                tmpl_cached_ids, tmpl_retok_ids, BLOCK_SIZE)

            block_churn_frac = invalid_blocks / total_blocks if total_blocks > 0 else 0.0
            ctrl_churn_frac = ctrl_invalid / ctrl_total if ctrl_total > 0 else 0.0
            tmpl_churn_frac = tmpl_invalid / tmpl_total if tmpl_total > 0 else 0.0
            churn_minus_ctrl = block_churn_frac - ctrl_churn_frac

            # Token-level: how many prefix tokens diverge?
            min_len = min(len(prefix_ids), len(retokenized_ids))
            lcp = 0
            for i in range(min_len):
                if prefix_ids[i] == retokenized_ids[i]:
                    lcp += 1
                else:
                    break
            tok_diverge_frac = 1.0 - (lcp / len(prefix_ids)) if len(prefix_ids) > 0 else 0.0

            # Binary: did ANY block get invalidated?
            has_churn = 1 if invalid_blocks > 0 else 0
            ctrl_has_churn = 1 if ctrl_invalid > 0 else 0

            records.append({
                'source': source,
                'tokenizer': tok_name,
                'delimiter_class': dclass,
                'has_chat_template': has_tmpl,
                'prefix_len_chars': len(trunc_prefix),
                'result_len_chars': len(result_text),
                'prefix_tokens': len(prefix_ids),
                'result_tokens': len(result_ids),
                'total_blocks': total_blocks,
                'invalid_blocks': invalid_blocks,
                'block_churn_frac': block_churn_frac,
                'ctrl_invalid_blocks': ctrl_invalid,
                'ctrl_churn_frac': ctrl_churn_frac,
                'tmpl_invalid_blocks': tmpl_invalid,
                'tmpl_churn_frac': tmpl_churn_frac,
                'churn_minus_ctrl': churn_minus_ctrl,
                'has_churn': has_churn,
                'ctrl_has_churn': ctrl_has_churn,
                'tok_diverge_frac': tok_diverge_frac,
                'first_invalid_block': first_inv,
            })

        all_results.extend(records)

        # ---- SUMMARY STATS ----
        n = len(records)
        churn_fracs = [r['block_churn_frac'] for r in records]
        ctrl_fracs = [r['ctrl_churn_frac'] for r in records]
        diffs = [r['churn_minus_ctrl'] for r in records]
        has_churns = [r['has_churn'] for r in records]

        mean_churn = sum(churn_fracs) / n
        mean_ctrl = sum(ctrl_fracs) / n
        mean_diff = sum(diffs) / n
        churn_rate = sum(has_churns) / n

        print(f"\n  n = {n} injection seams")
        print(f"  mean block_churn_frac = {mean_churn:.6f}")
        print(f"  mean ctrl_churn_frac  = {mean_ctrl:.6f}")
        print(f"  mean diff (treatment - control) = {mean_diff:.6f}")
        print(f"  fraction of turns with ANY churn = {churn_rate:.4f}")

    # ============================================================
    # AGGREGATE ANALYSIS across all tokenizers
    # ============================================================
    print("\n" + "=" * 70)
    print("AGGREGATE ANALYSIS")
    print("=" * 70)

    n_total = len(all_results)
    print(f"\nTotal records: {n_total}")

    # ---- GATE (a): block-churn 95% CI excludes 0 ----
    print("\n--- GATE (a): block-churn CI excludes 0 ---")
    churn_fracs_all = [r['block_churn_frac'] for r in all_results]
    bootstrap_means = []
    B = 10000
    for _ in range(B):
        sample = [churn_fracs_all[random.randint(0, n_total - 1)] for _ in range(n_total)]
        bootstrap_means.append(sum(sample) / n_total)
    bootstrap_means.sort()
    ci_lo = bootstrap_means[int(0.025 * B)]
    ci_hi = bootstrap_means[int(0.975 * B)]
    mean_churn_all = sum(churn_fracs_all) / n_total
    gate_a = ci_lo > 0
    print(f"  mean block_churn_frac = {mean_churn_all:.6f}")
    print(f"  95% bootstrap CI = [{ci_lo:.6f}, {ci_hi:.6f}]")
    print(f"  GATE (a) {'PASS' if gate_a else 'FAIL'}: CI {'excludes' if gate_a else 'includes'} 0")

    # ---- GATE (b): churn EXCEEDS clean-\n-append control (CI>0 on diff) ----
    print("\n--- GATE (b): churn > control (CI>0 on diff) ---")
    diffs_all = [r['churn_minus_ctrl'] for r in all_results]
    bootstrap_diffs = []
    for _ in range(B):
        sample = [diffs_all[random.randint(0, n_total - 1)] for _ in range(n_total)]
        bootstrap_diffs.append(sum(sample) / n_total)
    bootstrap_diffs.sort()
    diff_ci_lo = bootstrap_diffs[int(0.025 * B)]
    diff_ci_hi = bootstrap_diffs[int(0.975 * B)]
    mean_diff_all = sum(diffs_all) / n_total
    gate_b = diff_ci_lo > 0
    print(f"  mean diff (treatment - control) = {mean_diff_all:.6f}")
    print(f"  95% bootstrap CI = [{diff_ci_lo:.6f}, {diff_ci_hi:.6f}]")
    print(f"  GATE (b) {'PASS' if gate_b else 'FAIL'}: CI {'excludes' if gate_b else 'includes'} 0")

    # ---- GATE (c): delimiter-class predictor AUC > 0.5 ----
    print("\n--- GATE (c): delimiter-class predictor AUC ---")
    # Model-free predictor: predict block_churn_frac from delimiter_class alone
    # Use leave-one-out class-mean as the prediction for each observation
    by_dclass = defaultdict(list)
    for r in all_results:
        by_dclass[r['delimiter_class']].append(r['block_churn_frac'])

    # For AUC: binarize -> has_churn (any block invalidated)
    # Predictor: class-mean churn rate (LOO)
    predictions = []
    actuals = []
    for r in all_results:
        dc = r['delimiter_class']
        class_vals = by_dclass[dc]
        n_class = len(class_vals)
        if n_class <= 1:
            pred = mean_churn_all
        else:
            loo_mean = (sum(class_vals) - r['block_churn_frac']) / (n_class - 1)
            pred = loo_mean
        predictions.append(pred)
        actuals.append(r['has_churn'])

    # Compute AUC (Mann-Whitney U statistic)
    pos_preds = [predictions[i] for i in range(n_total) if actuals[i] == 1]
    neg_preds = [predictions[i] for i in range(n_total) if actuals[i] == 0]
    n_pos = len(pos_preds)
    n_neg = len(neg_preds)

    if n_pos == 0 or n_neg == 0:
        auc = 0.5
        print(f"  WARNING: no positive or no negative cases. AUC=0.5 by default.")
    else:
        concordant = 0
        tied = 0
        for p in pos_preds:
            for n in neg_preds:
                if p > n:
                    concordant += 1
                elif p == n:
                    tied += 1
        auc = (concordant + 0.5 * tied) / (n_pos * n_neg)
        print(f"  n_pos (has_churn=1) = {n_pos}, n_neg (has_churn=0) = {n_neg}")
        print(f"  AUC = {auc:.4f}")

    # Bootstrap CI for AUC
    bootstrap_aucs = []
    indices = list(range(n_total))
    for _ in range(B):
        sample_idx = [random.choice(indices) for _ in range(n_total)]
        s_preds = [predictions[i] for i in sample_idx]
        s_actuals = [actuals[i] for i in sample_idx]
        s_pos = [s_preds[i] for i in range(n_total) if s_actuals[i] == 1]
        s_neg = [s_preds[i] for i in range(n_total) if s_actuals[i] == 0]
        if len(s_pos) == 0 or len(s_neg) == 0:
            bootstrap_aucs.append(0.5)
            continue
        c = t = 0
        for p in s_pos:
            for n in s_neg:
                if p > n: c += 1
                elif p == n: t += 1
        bootstrap_aucs.append((c + 0.5 * t) / (len(s_pos) * len(s_neg)))
    bootstrap_aucs.sort()
    auc_ci_lo = bootstrap_aucs[int(0.025 * B)]
    auc_ci_hi = bootstrap_aucs[int(0.975 * B)]
    gate_c = auc_ci_lo > 0.5
    print(f"  AUC 95% bootstrap CI = [{auc_ci_lo:.4f}, {auc_ci_hi:.4f}]")
    print(f"  GATE (c) {'PASS' if gate_c else 'FAIL'}: AUC CI {'>' if gate_c else '<='} 0.5")

    # ---- Per-delimiter-class breakdown ----
    print("\n--- Per-delimiter-class churn rates ---")
    print(f"{'class':20s} {'n':>5} {'churn_rate':>10} {'mean_block_churn':>16} {'mean_ctrl_churn':>15}")
    for dc in sorted(by_dclass.keys(), key=lambda x: -len(by_dclass[x])):
        vals = by_dclass[dc]
        n_dc = len(vals)
        cr = sum(1 for v in vals if v > 0) / n_dc
        mc = sum(vals) / n_dc
        ctrl_vals = [r['ctrl_churn_frac'] for r in all_results if r['delimiter_class'] == dc]
        mctrl = sum(ctrl_vals) / len(ctrl_vals) if ctrl_vals else 0
        print(f"{dc:20s} {n_dc:5d} {cr:10.4f} {mc:16.6f} {mctrl:15.6f}")

    # ---- REGIME STRATIFICATION (committee fix 2) ----
    print("\n--- REGIME STRATIFICATION ---")
    print("Regime (a): full-prompt-retokenize-per-turn [churn POSSIBLE]")
    print("  This experiment ASSUMES full re-tokenization (the worst case).")
    print("  In regime (b) = token-ID-cache/delta-tokenize, churn is STRUCTURALLY 0")
    print("  because token IDs are cached and only new tokens are appended (no re-tokenization).")
    print("  The headline churn ONLY applies to regime (a) engines.")
    print("  vLLM APC/RadixAttention operate on token-ID sequences received from the client;")
    print("  if the client re-tokenizes the full prompt each turn, regime (a) applies.")
    print("  If the client caches token IDs and only encodes new text, regime (b) applies.")

    # Per-corpus breakdown
    for src in ['claude_code', 'codex']:
        src_records = [r for r in all_results if r['source'] == src]
        if not src_records:
            continue
        n_src = len(src_records)
        mc = sum(r['block_churn_frac'] for r in src_records) / n_src
        md = sum(r['churn_minus_ctrl'] for r in src_records) / n_src
        cr = sum(1 for r in src_records if r['has_churn'] == 1) / n_src
        print(f"\n  {src}: n={n_src}, mean_block_churn={mc:.6f}, mean_diff={md:.6f}, churn_rate={cr:.4f}")

    # Per-tokenizer breakdown
    for tok_name in [t[0] for t in TOKENIZER_SPECS]:
        tok_records = [r for r in all_results if r['tokenizer'] == tok_name]
        if not tok_records:
            continue
        n_t = len(tok_records)
        mc = sum(r['block_churn_frac'] for r in tok_records) / n_t
        md = sum(r['churn_minus_ctrl'] for r in tok_records) / n_t
        cr = sum(1 for r in tok_records if r['has_churn'] == 1) / n_t
        print(f"\n  {tok_name}: n={n_t}, mean_block_churn={mc:.6f}, mean_diff={md:.6f}, churn_rate={cr:.4f}")

    # ---- CHAT TEMPLATE CONTROL (committee fix 6) ----
    print("\n--- CHAT TEMPLATE CONTROL ---")
    tmpl_churns = [r['tmpl_churn_frac'] for r in all_results]
    raw_churns = [r['block_churn_frac'] for r in all_results]
    mean_tmpl = sum(tmpl_churns) / n_total
    mean_raw = sum(raw_churns) / n_total
    tmpl_diff = [r['tmpl_churn_frac'] - r['block_churn_frac'] for r in all_results]
    mean_tmpl_diff = sum(tmpl_diff) / n_total
    print(f"  mean block_churn WITHOUT template delimiter: {mean_raw:.6f}")
    print(f"  mean block_churn WITH <|tool_result|> template: {mean_tmpl:.6f}")
    print(f"  mean diff (template - raw): {mean_tmpl_diff:.6f}")
    if abs(mean_tmpl) < 1e-9 and abs(mean_raw) > 1e-9:
        print("  NOTE: Chat template delimiter PREVENTS churn — effect vanishes in production")
        print("  with proper template injection. This is an INFORMATIVE NEGATIVE.")

    # ---- NON-COLLISION ATTESTATION vs DEAD-0006 (committee fix 7) ----
    print("\n--- NON-COLLISION ATTESTATION vs DEAD-0006 ---")
    print("  DEAD-0006: 'token-prefix sharing PREDICTS KV sharing -> RadixAttention already")
    print("  captures it.' Killed because it ASSUMED token-prefix identity guarantees KV reuse.")
    print("  CLAIM-0014 (THIS WORK) = INVERSE: re-tokenization silently BREAKS token-prefix")
    print("  identity, so the assumption underlying DEAD-0006 is violated at tool-result seams.")
    print("  NOT a re-litigation of DEAD-0006. DEAD-0006 = 'prefix predicts sharing' (TRUE")
    print("  but trivial, RadixAttention already does it). CLAIM-0014 = 'the prefix itself is")
    print("  NOT STABLE across re-tokenization' (the token-ID sequence changes at the seam).")
    print("  These are complementary, not contradictory findings.")

    # ---- FINAL VERDICT ----
    print("\n" + "=" * 70)
    print("FINAL VERDICT")
    print("=" * 70)
    all_pass = gate_a and gate_b and gate_c
    print(f"  Gate (a) block-churn CI excludes 0:     {'PASS' if gate_a else 'FAIL'}")
    print(f"  Gate (b) churn > control CI>0:          {'PASS' if gate_b else 'FAIL'}")
    print(f"  Gate (c) delimiter AUC CI > 0.5:        {'PASS' if gate_c else 'FAIL'}")
    if all_pass:
        print("\n  ==> ALL THREE GATES PASS. CLAIM-0014 SUPPORTED at L0.")
        print("  ==> Candidate for L1 (H100 vLLM APC hit/miss counters).")
        verdict = "PASS"
    else:
        failed = []
        if not gate_a: failed.append("(a) block-churn CI includes 0")
        if not gate_b: failed.append("(b) churn == control")
        if not gate_c: failed.append("(c) AUC <= 0.5")
        print(f"\n  ==> CLEAN KILL on: {'; '.join(failed)}")
        verdict = "CLEAN_KILL"

    # ---- WRITE RESULTS ----
    summary = {
        'experiment': 'EXP-0049',
        'claim': 'CLAIM-0014',
        'project': 'PROJ-0005',
        'level': 0,
        'n_seams': len(seams),
        'n_records': n_total,
        'corpora': dict(src_counts),
        'tokenizers': [t[0] for t in TOKENIZER_SPECS],
        'block_size': BLOCK_SIZE,
        'gate_a': {'pass': gate_a, 'mean': mean_churn_all, 'ci': [ci_lo, ci_hi]},
        'gate_b': {'pass': gate_b, 'mean_diff': mean_diff_all, 'ci': [diff_ci_lo, diff_ci_hi]},
        'gate_c': {'pass': gate_c, 'auc': auc, 'ci': [auc_ci_lo, auc_ci_hi],
                   'n_pos': n_pos, 'n_neg': n_neg},
        'verdict': verdict,
        'chat_template_control': {
            'mean_churn_without': mean_raw,
            'mean_churn_with_template': mean_tmpl,
            'diff': mean_tmpl_diff
        },
        'per_delimiter_class': {dc: {'n': len(vals), 'mean_churn': sum(vals)/len(vals),
                                     'churn_rate': sum(1 for v in vals if v > 0)/len(vals)}
                                for dc, vals in by_dclass.items()},
    }

    import json as json_mod
    summary_path = os.path.join(RESULTS_DIR, 'summary.json')
    with open(summary_path, 'w') as f:
        json_mod.dump(summary, f, indent=2)
    print(f"\n  Results written to {summary_path}")

    # Write per-record CSV
    csv_path = os.path.join(RESULTS_DIR, 'per_seam_results.csv')
    with open(csv_path, 'w') as f:
        headers = ['source', 'tokenizer', 'delimiter_class', 'has_chat_template',
                   'prefix_tokens', 'result_tokens', 'total_blocks', 'invalid_blocks',
                   'block_churn_frac', 'ctrl_invalid_blocks', 'ctrl_churn_frac',
                   'tmpl_churn_frac', 'churn_minus_ctrl', 'has_churn',
                   'tok_diverge_frac', 'first_invalid_block']
        f.write(','.join(headers) + '\n')
        for r in all_results:
            f.write(','.join(str(r.get(h, '')) for h in headers) + '\n')
    print(f"  Per-seam CSV written to {csv_path}")

    return verdict, summary


if __name__ == '__main__':
    verdict, summary = run_experiment()
    sys.exit(0 if verdict in ('PASS', 'CLEAN_KILL') else 1)

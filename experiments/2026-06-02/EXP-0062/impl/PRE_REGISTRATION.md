# EXP-0062 — PRE-REGISTRATION (FROZEN) — GREEN-LIFT of CLAIM-0026
**Project:** PROJ-0015 · **Claim:** CLAIM-0026 · **Parent:** EXP-0061 (6/6 YELLOW-ADVANCE, VERDICT-0072)
**Agent:** researcher-0026-lift-r8 · **Node:** cli:dengcchi-mac · **Level:** 0 (Mac CPU; gpt2 venv used for TOKEN-COUNTING ONLY in Gap 2)
**LOCK-TS:** 2026-06-01T (committed via `ros commit` BEFORE any outcome measurement)
**Type:** CHARACTERIZATION confirmatory follow-up. Closes the 3 closable green-lift gaps from VERDICT-0072. An honest result either way (claim HARDENED to green, or a gap that DOWNGRADES it) is first-class.

This file is committed BEFORE measuring any of the three gap outcomes. All thresholds, denominators, the chat-corpus definition, the tokenizer, the subsample fraction, and decision rules below are FROZEN. No threshold moves after this lock. The pipeline REUSES `experiments/2026-06-01/EXP-0061/impl/decomposition_census.py` (parsers `decompose_cc_session`/`decompose_codex_session`, `canon_args`, `block_text`, `gini`, `denoms`, char/4 proxy, 2000x session-clustered bootstrap) VERBATIM by import — identical instrument.

EXP-0061 ESTABLISHED (frozen reference, NOT re-litigated here):
- Agent tool-result prefill share R/D1 (conservative raw-span denominator): **CC 0.657 (LB95 0.569) / Codex 0.770 (LB95 0.748)**, both RE-A0 PASS.
- Heavy tail Gini 0.863 (CC) / 0.749 (Codex); cross-instrument |Δ|=0.113 < 0.40; HHI-by-session < 0.20 both.

---

## GAP 1 — ON-NODE CHAT BASELINE (the #1 green-blocker), measured with the IDENTICAL instrument

**Search for external chat corpora (ShareGPT / LMSYS / Vicuna / WildChat / OASST / UltraChat):** executed across `~/.cache/huggingface/{hub,datasets}`, `~/data`, `~/datasets`, `~/Downloads`, `~/Documents`, `/tmp`. **RESULT: NONE present on-node** (HF hub holds only model weights: gpt2, Meta-Llama-3-8B, Qwen2-0.5B — no chat datasets). Documented absence.

**On-node chat baseline (fallback, instrument-consistent):** the Claude Code and Codex logs themselves contain **conversational (zero-tool) sessions** captured by the SAME logging instrument. We define the **CHAT corpus** = sessions with **ZERO tool calls** (no `tool_use` block / no `function_call` payload) — chat = LLM conversation without external tool use, by definition — AND dynamic content >= **CHAT_MIN_CHARS = 1000** (excludes degenerate/aborted stubs). We run the **IDENTICAL** `decompose_*` pipeline + char/4 over them.

**Metrics (same instrument, char/4, all on dynamic stream D1 = R+A+TX+TH+U+O):**
- chat tool-result prefill share `Rc/D1` (structurally ~0 — no tools)
- chat human-prompt prefill share `Uc/D1`
- chat model-decode share `(TXc+THc)/D1`
- 2000x session-clustered bootstrap CI on `Uc/D1` (SEED below).

**FROZEN GATE-CHAT (the decisive, instrument-consistent contrast):** the "agent serving reframes which content class is the prefill knob" claim is **VALIDATED** iff ALL hold:
1. chat tool-result share `Rc/D1` **UB95 < CHAT_RESULT_MAX = 0.10** (tool-result prefill is ~absent in chat), AND
2. agent tool-result share `R/D1` **LB95 > 0.50** (established EXP-0061, both corpora), AND
3. chat human-prompt share `Uc/D1` **>** chat tool-result share `Rc/D1` (in chat the served prefill is human-authored, not external-tool-authored).
→ The dominant served-prefill content class **inverts** between regimes: HUMAN-PROMPT (chat) → TOOL-RESULT (agent), measured identically. Equivalently: `agent R/D1 − chat R/D1 > 0.40` on both corpora.

**Circularity disclosure (frozen, transparent):** zero-tool IS the operational definition of chat, so `Rc≈0` is ground truth, not a circular artifact. The substantive (non-trivial) finding is the **prefill-composition inversion** — chat served prefill is human-prompt-dominated; agent serving introduces a THIRD content source (external tool output) absent in chat that becomes the dominant served mass. We report the full chat class decomposition, not merely `Rc=0`.

**Honest negative for Gap 1:** if chat `Uc/D1` did NOT exceed `Rc/D1`, or the agent−chat separation were < 0.40, the "different regime" contrast would be unsupported and reported as such. (Single-turn nature of on-node CC chat sessions and 2-turn Codex chat sessions is a disclosed limitation.)

## GAP 2 — CHAR/4 TOKENIZER CALIBRATION (real tokenizer on stratified 10% subsample)

**Tokenizer:** **gpt2** BPE (HuggingFace fast/Rust backend, reused from the EXP-0049 `.venv`). **tiktoken / cl100k are NOT installed on-node** (verified `import tiktoken` fails); gpt2 is the available real tokenizer. Disclosure: gpt2 BPE merges code/whitespace LESS efficiently than cl100k, so gpt2 chars-per-token (cpt) is, if anything, a HIGHER (more conservative) cpt for structured text than cl100k would give → using gpt2 can only UNDER-state the R undercount, so the correction direction is conservative.

**Subsample:** **SUBSAMPLE_FRAC = 0.10** stratified by content class, drawn per corpus with **SEED_CAL = 20260602**. A segment = one `tool_result` block (R), one `canon_args` string (A), one assistant `text` block (TX), one `thinking` block (TH), one user text (U). Report per-class **cpt = Σchars / Σtokens** over the subsample.

**Correction & recompute (FROZEN):** true token mass per class = `char_mass(class) / cpt_class` (apply subsample cpt to the FULL corpus char mass). Recompute the headline **true-token result-share** `f_true = R_true / D1_true` (D1_true = Σ all class true masses) per corpus.

**FROZEN decision rule:**
- if `f_true(D1)` **< 0.50** on CC **OR** Codex → the char/4 headline is a **proxy ARTIFACT** → HONEST NEGATIVE / downgrade.
- if `f_true(D1)` **>= 0.50 on BOTH** AND **>= the char/4 value** (rises) → headline **HARDENED**.
- if `f_true(D1)` **>= 0.50 on both** but slightly below the char/4 value → headline **robust-confirmed** (dominance survives real tokenization).

**Pre-registered hypothesis (theory_skeptic):** `cpt_R < cpt_U` (JSON/code/base64-heavy results tokenize ~2.5–3.5 cpt vs prose ~4) → char/4 under-counts R → `f_true > f_char4`.

## GAP 3 — PRIOR-ART SWEEP + MISSING CITES

Web search availability documented in analysis. MUST add to related work + one-line differentiate (from knowledge):
- **Mooncake 2407.00079** — real Kimi-trace prefix-cache hot-spot characterization (nearest to the heavy-tail framing; was MISSING).
- **BurstGPT 2401.17644** — real-world LLM serving workload study.
- **MemGPT 2310.08560** (>=1 agent-context-compression work) — virtual-context/paging for agents.
Each differentiated vs CLAIM-0026's granular agent-tool-loop token-mass decomposition.

## ROBUSTNESS (pre-registered, non-gating)
- **Jackknife-by-session:** drop top-1 and top-3 sessions by total result mass; recompute agent `R/D1`. Pre-registered expectation: stays **> 0.50** both corpora (corroborates HHI<0.20).
- **Presentation fix:** heavy-tailedness reframed as **QUANTIFIED-known-expected** (bounded prompts + unbounded tool I/O is a theoretically heavy-tailed mixture), NOT "discovered".

## FROZEN CONSTANTS
SEED_CAL=20260602 · NBOOT=2000 · CHARS_PER_TOK=4.0 · CHAT_MIN_CHARS=1000 · CHAT_RESULT_MAX=0.10 · SUBSAMPLE_FRAC=0.10 · A0_THRESH=0.50 · CROSS_SEP=0.40 · MIN_TRIALS=8 (agent, reused) · TOKENIZER=gpt2(BPE,HF-fast).
Bootstrap: LB95=2.5th pct, UB95=97.5th pct; session-clustered resample (sessions w/ replacement). Agent reference numbers imported frozen from EXP-0061.

## DELIVERABLES
impl/{PRE_REGISTRATION.md, chat_baseline_and_calibration.py, analysis.md} + results/{chat_baseline.json, calibration.json, jackknife.json}.
On completion: `ros exp complete`, report to sub-monitor-0015-r8. Do NOT self-judge, do NOT convene committee, do NOT touch GPU.

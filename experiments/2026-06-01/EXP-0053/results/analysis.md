# EXP-0053 — Analysis: Realized Cross-Session Prefix-Reuse Ceiling from Tool-Schema/System-Prompt Drift

**PROJ-0007 / CLAIM-0017 · VERDICT-0060 · researcher-0017-L0-r6 · prompt_version v001**
Pre-registration LOCKED 2026-06-01T16:09:03Z, committed b83fb0c BEFORE the main run. Thresholds frozen.
L0, Mac CPU, stdlib analysis + production tokenizers (gpt2 primary, qwen2-0.5b robustness; EXP-0049 venv).

## HEADLINE — HONEST NEGATIVE (pre-registered RE-B1 KILL pathway fired)
Realized cross-session prefix-cache reuse **IS bounded below the naive shared-text fraction** by a **named,
predictable** cause (tool-schema / system-prompt micro-drift — volatile head fields + dynamically-varying
tool/config lists), and that cause is **distinct from PROJ-0005's intra-session BPE-tail seam** (0% of
first-divergences are BPE-seam-driven; tokenizer-invariant). **BUT** the drift-attributable shortfall is a
**recoverable prompt-engineering anti-pattern** — moving volatile/tenant/config fields and dynamic tool
lists after the static prefix recovers the cacheable prefix — **NOT a novel architectural ceiling.**
`standalone_architectural_ceiling_supported = False`. `fold_into_proj0005 = False` (stays distinct, but the
standalone thesis still fails its load-bearing gate). This is exactly the project's pre-registered HONEST
KILL PATHWAY: "RE-B1 vanish → prompt-engineering PSA, canonicalize volatile fields (actionable negative)."

## DATA
3 distinct template families parsed from real production traces (RE-B6). Shared-skeleton groups:
- **Codex** n=111 — base_instructions byte-identical across all sessions; developer envelope
  (permissions/skills_instructions/available_skills) drifts every session. Drift LATE in head.
- **Claude Code** n=39 — documented `<env>` block (real per-session cwd/gitBranch/date/version/sessionId)
  ++ shared role-prompt skeleton. Drift EARLY in head.
- **Gemini** n=2 — below the n>=3 floor; reported as a degenerate low-drift family, not counted.

## RESULTS (gpt2 primary; qwen2-0.5b corroborates every direction)

| family | n | naive shared | realized RAW | realized CANON | shortfall (frac) | drift recovered (CI) | RE-B3 real/sham AUC | RE-B4 seam | post-canon residual |
|---|---|---|---|---|---|---|---|---|---|
| Claude Code | 39 | 1094.6 | **51.4** | **576.0** | 1043.3 (**95.3%**) | **+524.6** [519.6,529.7] | 0.984 / 0.976 | 0/38 | **38/38 genuine content** |
| Codex | 111 | 6776.5 | 6609.7 | 6648.1 | 166.8 (**2.5%**) | +38.4 [31.6,44.4] | 0.944 / 0.718 | 0/110 | genuine config prose |

### RE-B1 (LOAD-BEARING / KILLER) — drift is RECOVERABLE → KILL
- **Claude Code (load-bearing, early & MATERIAL drift):** volatile env fields at the head break the
  cross-session prefix almost immediately — raw realized prefix is only **51 tok of a 1094-tok shared
  skeleton (95% stranded)**. The caching-best-practice canonicalizer (strip volatile/tenant fields, relocate
  to suffix, sort tool lists) recovers **51 → 576 tok (~10×)**. After canonicalization, **0/38** first
  divergences sit on a drift field — **38/38 are genuine committee-body content** that legitimately differs.
  → The shortfall is a prompt-engineering anti-pattern; the architectural-ceiling claim is **not** supported.
- **Codex (late, NEGLIGIBLE drift):** realized reuse is already **97.5%** of shared text; shortfall is a
  2.5% tail effect. The post-canon residual is genuine per-session **config prose** (`sandbox_mode`
  read-only vs danger-full-access; `approval_policy`; cli-version wording), recoverable by relocating the
  whole variable permissions block (canonicalizer-completeness) — i.e. also a placement/PSA issue, and far
  too small to be a material ceiling.
- The literal frozen metric `shortfall_canon ≥ 16` registers PASS for both, **but** that multiset-based
  shortfall conflates drift with genuine content; the post-canon residual attribution (added as the RE-B1
  *intent* test) shows the residual is genuine content/config, overturning the naive PASS. Reported
  transparently; integrated verdict = **NEGATIVE**.

### RE-B2 (effect size) — drift effect is REAL and ≥1 block
Drift-attributable recovered prefix = realized_canon − realized_raw: CC **+524.6 tok** (CI [519.6,529.7]),
Codex **+38.4 tok** (CI [31.6,44.4]); both ≥16 with CI lower bound ≥16 (not a block-quantization artifact).
The effect is real — it just does not constitute an *architectural* ceiling (it is recoverable).

### RE-B3 (drift-class predictor of first-divergence location) — PASS, but note sham
Real drift-class predictor AUC = 0.944 (Codex) / 0.984 (CC) ≥ 0.70 and > sham (0.718 / 0.976). For CC the
sham is also near-ceiling (divergence is trivially early in the head), so the predictability there is partly
trivial; for Codex the real predictor genuinely beats the sham by +0.23 AUC. The first-divergence location
IS predictable model-free from the drift class — consistent with the named-cause claim.

### RE-B4 (fold-into-PROJ-0005 trigger, X=50%) — DOES NOT FIRE → stays distinct
**0/110 (Codex) and 0/38 (CC)** first cross-session divergences are BPE-seam-driven (same chars, shifted
tokens); 100% are structural (different characters). seam_fraction = 0.000 < 0.50 → **STAY DISTINCT**. The
cross-session head divergence is genuine content drift, NOT the CLAIM-0014 intra-session BPE-seam mechanism.

### RE-B5 (tokenizer-seam stratification) — confirms structural, not seam
Structural fraction of first-divergences = **1.0 under BOTH gpt2 and qwen2-0.5b** for both families. The
divergences are tokenizer-invariant (same char locus regardless of tokenizer) ⇒ genuinely structural
content drift, not a tokenizer-specific BPE seam. Corroborates RE-B4 non-collision with PROJ-0005.

### RE-B6 (template-family stratification) — 2 distinct families, consistent direction
Codex and Claude Code are distinct skeletons. Both yield the same integrated verdict (NEGATIVE / no material
architectural ceiling); the *magnitude* differs sharply (CC 95% early drift vs Codex 2.5% tail drift),
reported per-family rather than averaged.

### RE-B7 / RE-B8 — prior art (see prior_art/PROJ-0007/)
RE-B7: Anthropic & OpenAI docs document the cumulative-/prefix-hash invalidation and explicitly instruct
placing volatile fields after the static prefix; Anthropic's "common mistake" is the exact timestamp-in-head
failure mode. RE-B8: vLLM (parent-hash block chaining, full-block, `cache_salt`), SGLang RadixAttention/LPM,
TensorRT-LLM full-block reuse — all forfeit every downstream block after one early divergence; realized
gains scale with the shared-prefix fraction. Real APC hit counters + recovered TTFT (H100) = L1, out of scope.

## NON-COLLISION (holds)
INVERSE of DEAD-0006 (here token-prefix FAILS to share cross-session). DISTINCT from PROJ-0005/CLAIM-0014
(RE-B4 0% seam, RE-B5 struct-frac 1.0). The fold-trigger was the boundary test and it did not fire.

## DECISION & FOLLOW-ON
**Honest negative — do NOT promote PROJ-0007 as a standalone architectural cross-session prefix-reuse
ceiling.** Salvage value: (1) a quantified **prompt-engineering PSA** with a real-fleet 10× cross-session
prefix-recovery demonstration (CC) and the vendor-guidance grounding; (2) the **drift-class first-divergence
predictor**; (3) the only PASS-able open question is **L1**: does recovering the prefix on real H100 vLLM
APC yield material recovered TTFT/hit-rate — out-of-scope for L0, flag to orchestrator. Does NOT fold into
PROJ-0005 (different mechanism).

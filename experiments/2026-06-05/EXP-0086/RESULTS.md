# RESULTS — EXP-0086 (CLAIM-0070, PROJ-0040) — L2 GREEN-GATE
Author: researcher-0070 | parent: orchestrator-r11-001 | level 2 | 2026-06-05
Nodes: cli:dengcchi-mac (engine + spec reads), cli:devvm14382 (build/run/clone/scan)
Disposition: **SUPPORT** — the decisive guest-defensibility arm HOLDS (demotion is invisible to
correct guest code), the cross-runtime anomaly EXTENDS to Node.js/V8 (wazero anomalous beyond the
Rust ecosystem), the version trajectory confirms the seed-42 default persists through the latest
release, and the bounded prevalence sample shows real UNMITIGATED bare-default usage including a
**code-generator-propagated** default. Residual: the authenticated full-population prevalence scan
was BLOCKED (no gh/GITHUB_TOKEN on either node) — flagged loudly for orchestrator escalation.

---

## 0. EXECUTIVE
Committee#2 (VERDICT-0069) gated GREEN on five L2 deliverables. Four (1,2,3,5) need no auth and
were executed in full; deliverable 4 (authenticated prevalence) was auth-blocked and run as a
bounded unauthenticated proxy with an explicit denominator.

- **Deliverable 1 (spec disambiguation):** preview1 alone = STRONG-BUT-CONTESTABLE CSPRNG breach
  ("high-quality" + blocking clause, but the literal words "cryptographically secure" are NOT in
  preview1 — they are in the successor). Strongest defensible per-generation claim stated below.
- **Deliverable 2 (guest-defensibility — DECISIVE):** a correct Go-WASI guest using the
  gold-standard `crypto/rand` / `ed25519.GenerateKey` pattern **CANNOT detect or reject** the
  deterministic host source at runtime. Demonstrated empirically + from the ABI surface. The
  "un-defendable" arm HOLDS. **GREEN-track.**
- **Deliverable 3 (Node.js baseline + version trajectory):** Node.js (V8, via uvwasi)
  `random_get` defaults SECURE (fresh bytes/keys each launch). wazero is anomalous beyond the
  Rust-ecosystem runtimes. v1.12.0 is the LATEST tag (2026-05-28); no post-v1.12.0 release; the
  `const seed = int64(42)` default persists at the trajectory tip.
- **Deliverable 4 (prevalence):** AUTH BLOCKED. Bounded sample of 9 wazero-importers shows 2
  real bare-default + arbitrary-guest exposures (incl. a generator-propagated default), 2
  explicit overrides, 4 bare-but-low-risk. Non-zero unmitigated usage; NOT a population estimate.
- **Deliverable 5 (conformance-synthesis positioning):** repositioned below as
  conformance-synthesis AGAINST the practitioner find-fix set, NOT discovery.

---

## 1. DELIVERABLE 1 — PREVIEW1-vs-SUCCESSOR SPEC-VIOLATION DISAMBIGUATION

### 1a. The COMPLETE preview1 normative prose for random_get (verbatim, from the procedurally
generated witx binding — docs.rs/ffmpeg-wasi `__wasi_random_get`, identical to WASI snapshot-01
docs.md §random_get and Wasmtime's preview1 witx):

> Write **high-quality random data** into a buffer.
> This function **blocks when the implementation is unable to immediately provide sufficient
> high-quality random data**. This function may execute slowly, so when large amounts of
> randomness are required, it's advisable to use this function to seed a pseudo-random number
> generator, rather than to provide the random data directly.

**Key fact:** the preview1 normative text contains the words "high-quality" and the
blocking-on-insufficient-entropy clause, but does **NOT** contain the literal phrase
"cryptographically secure" anywhere.

### 1b. The SUCCESSOR (wasi:random 0.2) is EXPLICIT (from L1, verbatim, proposals/random/wit):

> Return `len` **cryptographically-secure** random or pseudo-random bytes. ... must produce data
> at least as cryptographically secure and fast as an adequately seeded CSPRNG ... must always be
> unpredictable ... **Deterministic environments must omit this function, rather than
> implementing it with deterministic data.**
> (Insecure RNG quarantined into a SEPARATE `wasi:random/insecure` interface.)

### 1c. EMPIRICAL CORROBORATION the canonical preview1 implementation reads "high-quality" as
CSPRNG-grade: Node.js (V8) backs `random_get` via uvwasi, which sources the OS CSPRNG — and our
Node baseline (Deliverable 3) shows fresh unpredictable bytes every launch. The reference
implementations (Wasmtime per-context ChaCha CSPRNG; Wasmer `getrandom::fill`; Node/uvwasi OS
CSPRNG) UNIVERSALLY interpret preview1 "high-quality" as a CSPRNG. The single implementation that
reads it as "any deterministic source" is wazero.

### VERDICT (the precise strongest defensible claim, per generation):
- **Against wasi:random (successor, WASI 0.2): UNAMBIGUOUS SPEC VIOLATION.** The spec explicitly
  mandates cryptographic security AND explicitly states deterministic environments must OMIT the
  function rather than fake it — exactly what wazero's seed-42 default does. (STRONG.)
- **Against preview1: a STRONG-BUT-CONTESTABLE breach.** preview1 says "high-quality" + blocks on
  insufficient entropy; the blocking clause is the `getrandom(2)`/`getentropy` CSPRNG contract,
  and a fixed-seed PRNG can *never* be "unable to provide sufficient high-quality random data" so
  it provably cannot honor the blocking semantics. HONEST CAVEAT (theory_skeptic's point,
  conceded): preview1's prose does not use the literal words "cryptographically secure," so on
  preview1's *text alone* this is a strong-interpretation breach, not a slam-dunk normative
  violation. It is corroborated to near-certainty by (i) the universal reference-implementation
  interpretation (Wasmtime/Wasmer/Node all CSPRNG), and (ii) the successor making the latent
  contract explicit. **We claim violation primarily against the successor spec, and a
  strong-interpretation breach of preview1's "high-quality"+blocking contract — NOT a literal
  preview1 textual violation.** This is the disambiguation committee#2 asked for.

---

## 2. DELIVERABLE 2 — GUEST-SIDE DEFENSIBILITY TEST (DECISIVE)

**Question (committee#2 / theory_skeptic):** CAN a correct Go-WASI guest DETECT or REJECT a
deterministic host random source at runtime? If yes, the "un-defendable" arm weakens materially.

**Method:** Built a Go `wasip1/wasm` guest (`~/wazero_l2/guest/main.go`) that uses ONLY the
gold-standard secure APIs — `crypto/rand.Read`, `ed25519.GenerateKey(rand.Reader)` — and attempts
every defense a correct guest could mount. Ran it under a wazero host (`~/wazero_l2/host`) in two
configs (`default` = bare `NewModuleConfig()`; `secure` = `.WithRandSource(rand.Reader)`), each
launched as TWO separate host processes to test cross-restart repeat.

**RESULTS (verbatim, reproduced):**

WAZERO DEFAULT (bare NewModuleConfig) — two separate process launches:
```
RUN 1: CRYPTORAND_READ n=32 err=<nil>
       CRYPTORAND_BYTES dfd79b4d76429b617a0c9f9f0d3ba55b0cc0d6144c888535841acbe0709b0758
       ED25519_GENKEY err=<nil>
       ED25519_PUBKEY  7da885ef5c5cc1255a327fa688474ec9baeb25cfcbb47930361da73e52875cd1
RUN 2: CRYPTORAND_BYTES dfd79b4d76429b617a0c9f9f0d3ba55b0cc0d6144c888535841acbe0709b0758  (IDENTICAL)
       ED25519_PUBKEY  7da885ef5c5cc1255a327fa688474ec9baeb25cfcbb47930361da73e52875cd1  (IDENTICAL)
```
WAZERO SECURE (WithRandSource(rand.Reader)) — two launches: bytes/keys DIFFER each run
(a16bc55e... vs 84f76086...; ed25519 342f3dcf... vs bc877d48...).

**Every defense a correct guest could mount, and why each FAILS:**
1. **Error/blocking check** — `crypto/rand.Read` returns `n=32 err=<nil>`; `ed25519.GenerateKey`
   returns `err=<nil>`. The host returns `ErrnoSuccess` for the seed-42 source. A fixed-seed PRNG
   NEVER errors and NEVER blocks (it always has data). The textbook-secure pattern succeeds
   silently and emits a globally-predictable key. **FAILS.**
2. **Structural sanity (all-zero / low-entropy)** — `DEFENSE_ALLZERO_CHECK all_zero=false`. The
   seed-42 math/rand output is high-apparent-entropy nonzero bytes; statistical sanity passes.
   **FAILS.**
3. **Intra-process "two reads equal?"** — `INTRAPROC_TWO_READS_EQUAL false`. The PRNG advances, so
   two reads in one process differ even for a seeded PRNG. This test cannot catch it. **FAILS.**
4. **Cross-restart repeat detection** — would catch it (RUN1==RUN2), BUT a guest cannot observe
   "the previous run's bytes" within a single execution; it has no persistent store and no oracle
   for "what did I get last time." Cross-restart identity is observable only to an EXTERNAL
   observer, not to the guest defending itself in-process. **NOT available to the guest.**
5. **WASI capability assertion** — the ENTIRE preview1 ABI surface (enumerated from
   wazero v1.12.0 internal/wasip1: ArgsGet...SockShutdown, ~46 functions) contains EXACTLY ONE
   randomness function: `random_get`. There is NO entropy-quality query, NO CSPRNG capability
   assertion, NO health/self-test endpoint. `random_get` returns only `errno` (EFAULT/EIO) — no
   quality signal. A guest has no ABI mechanism to assert "I require a CSPRNG." **DOES NOT EXIST.**

**Tell-tale corroboration:** wazero's own `random.go` source documents the seed-42 PRNG output
bytes (`0x53, 0x8c, 0x7f, 0x96, 0xb1`) in the function comment, and `randomGetFn` returns `0`
(ErrnoSuccess) for the fake source — indistinguishable at the ABI from a real CSPRNG.

**DECISIVE VERDICT: the guest CANNOT defend.** A correct guest using the gold-standard
crypto/rand/ed25519 pattern receives no error, no block, statistically-plausible bytes, and has
no ABI to query entropy quality or assert a CSPRNG. The guest's self-test output is BYTE-IDENTICAL
in secure vs insecure mode (the four DEFENSE/INTRAPROC lines match exactly) — the demotion is
**invisible to correct guest code**. The "un-defendable / cannot-defend-by-writing-correct-code"
arm HOLDS. **GREEN-track.**

---

## 3. DELIVERABLE 3 — NODE.js (V8) WASI BASELINE + wazero VERSION TRAJECTORY

### 3a. Node.js (V8) baseline
Ran the SAME `guest.wasm` under Node v16.20.2 (V8 9.4.146.26) via `node:wasi`
(`--experimental-wasi-unstable-preview1`, `require('wasi')`, `wasiImport` =
`wasi_snapshot_preview1`). Two separate process launches:
```
RUN 1: CRYPTORAND_BYTES 76a1b9bc09e4f67135faaef8292028b469edd50606b733e417a65773e143bd24
       ED25519_PUBKEY  d97609dedf427418de3ced43df4168e83441097c257c94f2fec4fa03d4f15b82
RUN 2: CRYPTORAND_BYTES 852e9a76724b02a61ed3278c2a32c156b9086774f637ef94653e77413ebfea59  (DIFFERENT)
       ED25519_PUBKEY  1a98e314121084560296725a77f9169e74f96f63b5b54ac5f17f6f676ed508e1  (DIFFERENT)
```
**Node.js (V8) defaults `random_get` to a SECURE host CSPRNG** (uvwasi → OS CSPRNG). Fresh
unpredictable bytes/keys each launch. (Node's own `crypto.randomBytes` confirmed non-deterministic
on the same host.)

### 3b. Cross-runtime table (now including Node.js)
| Runtime | Default random_get | Anomalous? |
|---------|--------------------|------------|
| Wasmtime (Bytecode Alliance) | per-context randomly-seeded ChaCha CSPRNG | no |
| Wasmer | OS CSPRNG (getrandom::fill), no det. path | no |
| **Node.js / V8 (uvwasi)** | **OS CSPRNG (fresh each launch)** | **no** |
| **wazero v1.12.0** | **fixed-seed-42 math/rand PRNG** | **YES — the anomaly** |
wazero is anomalous **beyond the Rust-ecosystem runtimes** — it diverges from the V8/Node baseline
too. This closes the evaluation_prosecutor's mandatory baseline.

### 3c. wazero VERSION TRAJECTORY (theory_skeptic's point-estimate-vs-trajectory)
- Go module proxy version list: latest tag = **v1.12.0** (released 2026-05-28T15:27:49Z, commit
  2ab480b). There is **NO release after v1.12.0**; v1.12.0 IS the trajectory tip.
- At v1.12.0 (latest): `internal/platform/crypto.go` still has `const seed = int64(42)` backing
  `NewFakeRandSource()`; `internal/sys/sys.go:151-152` still does
  `if randSource == nil { sysCtx.randSource = platform.NewFakeRandSource() }` as the default.
- **The fixed-seed-42 default persists through the latest release.** Not a stale point estimate —
  it is the current, shipping default.

---

## 4. DELIVERABLE 4 — PREVALENCE (★ AUTHENTICATED SCAN BLOCKED — see flag)

### ★★ AUTH-BLOCKED FLAG (for orchestrator escalation to dengcchi) ★★
**GitHub authentication is UNAVAILABLE on BOTH nodes.** Checked:
- cli:devvm14382: `gh` command not found; `GITHUB_TOKEN` unset; `GH_TOKEN` unset.
- cli:dengcchi-mac: `gh` command not found; `GITHUB_TOKEN` unset.
The committee#2-required **authenticated AST/code-search prevalence scan with a population
denominator and CI** CANNOT be run here. This is the SAME blocker the L1 hit. The orchestrator
should escalate to dengcchi to provision a `gh` auth / `GITHUB_TOKEN` so the full-population
ratio-of-bare-NewModuleConfig scan can run. **The prevalence figure below is a BOUNDED SAMPLE,
NOT a population estimate.**

### Bounded unauthenticated proxy (curated top wazero-importers, depth-1 clone + AST/grep)
Scanned 20 curated candidate repos. Denominator accounting:
- 20 attempted → 4 clone-failed (fwdproxy/404) → 7 cloned-but-do-NOT-import-wazero
- = **9 repos that clone AND import wazero (the sample denominator)**

Entropy-relevance classification of the 9 wazero-importers (wazero itself excluded as the subject):
| Class | Repos | n |
|-------|-------|---|
| **BARE default + arbitrary/3rd-party guest (REAL exposure)** | knqyf263/go-plugin (generator-propagated), dylibso/observe-sdk | **2** |
| OVERRIDDEN (`WithRandSource(rand.Reader)`) | wapc/wapc-go (all 4 knobs), loopholelabs/scale | 2 |
| BARE but low-risk (fixed first-party guest / no-entropy / test-harness / lib helper) | arcjet/arcjet-go, wasilibs/go-re2, stealthrocket/wazergo, tetratelabs/proxy-wasm-go-sdk | 4 |

**NOTABLE FINDING — generator-propagated default (amplifies blast radius):**
knqyf263/go-plugin's hazard is NOT a single call site. Its **code-generator template**
(`gen/host.go:145,158`) stamps `wazero.NewModuleConfig().WithStartFunctions("_initialize")`
(NO `WithRandSource`) into the `New<Service>Plugin` constructor of EVERY host it generates. It
exposes a `wazeroConfigOption` opt to override moduleConfig — so it is mitigable — but the DEFAULT
is bare. This is opt-out-of-insecure, not opt-in-to-secure: every go-plugin consumer that doesn't
explicitly pass a config option inherits the seed-42 demotion, multiplied across all generated
hosts. observe-sdk similarly loads arbitrary user WASM (`WithArgs(os.Args[1:]...)`) with a bare
config.

**INTERPRETATION (honest):** In this bounded sample of 9, BOTH endpoints appear and the bare end
includes a generator-propagated default and an arbitrary-WASM host runner — refuting the
"strawman in deployed practice" worry (real general-purpose hosts ship bare defaults), while
mature hosts that DID notice (wapc-go, scale) wire WithRandSource explicitly. This is real
non-zero UNMITIGATED usage with amplification, but it does NOT establish committee#2's
">non-trivial fraction of mature projects" bar with a population denominator + CI — that requires
the authenticated scan, which is BLOCKED. **RE-2 here = real-signal-with-amplification,
scope-limited by missing auth.**

---

## 5. DELIVERABLE 5 — CONFORMANCE-SYNTHESIS POSITIONING (NOT discovery)

The contribution is explicitly repositioned as **conformance-synthesis + characterization**, NOT
hazard-discovery. The MECHANISM (wazero seed-42 random_get demotes guest CSPRNG) was independently
found-and-fixed by practitioners — verified evidence-of-record:
- **CrowdSec PR #4495** "Fix obfuscator prng" — quotes wazero config.go verbatim, re-adds a real
  random source ("else it would defeat the runtime obfuscation randomness").
- **wetware/pkg issue #106** — author realized WithRandSource "defaults to a (deterministic)
  stub"; "We definitely want to provide guests with crypto-grade entropy."
- **wapc/wapc-go** — wires `WithRandSource(rand.Reader)` + all three clock knobs (confirmed in
  this scan at engines/wazero/wazero.go:140).
- **loopholelabs/scale** — wires `WithRandSource(rand.Reader)` + clocks (newly confirmed here).
- **wazero issue #620** (cited in the packet of record) — the upstream awareness thread.
- Class ancestry: **CWE-330** (Insufficiently Random Values) / **CWE-338** (Cryptographically Weak
  PRNG); **SWC-120** (Weak Sources of Randomness) is the EVM analogue.

**The UN-OWNED contribution (the synthesis), now empirically reinforced by this L2:**
(a) it is an **ABI-boundary** property — cross-LANGUAGE (Go ed25519 AND Rust getrandom both
demoted), proving host-side; (b) it is a **cross-runtime differential** — wazero anomalous vs
Wasmtime AND Wasmer AND **Node.js/V8** (NEW: beyond the Rust ecosystem); (c) it is
**un-defendable by correct guest code** (Deliverable 2 — DECISIVE, newly measured: no error, no
block, no ABI to query entropy, invisible to self-test); (d) it travels with a
**clock-decoupling** half (rate-limiter/backoff misfire) under the same default; (e) it is
**generator-propagated** in at least one general-purpose host (go-plugin codegen), amplifying
blast radius; (f) it is a **spec-conformance** finding (unambiguous vs the successor spec).
The practitioner find-fixes VALIDATE the mechanism and NARROW novelty to exactly this synthesis +
characterization + cross-runtime-conformance framing.

---

## 6. DISPOSITION — applying the pre-registered rule

Pre-registered GREEN gate: (P) prevalence non-trivial UNMITIGATED bare-default usage AND
(D) guest-defensibility confirms un-defendable AND (S) spec-violation + cross-runtime anomaly hold
including Node.js.

| Arm | Result | Holds? |
|-----|--------|--------|
| (D) Guest-defensibility | guest CANNOT defend; demotion invisible to correct code; no ABI to query entropy | **YES (decisive)** |
| (S) Spec — successor | unambiguous violation ("must omit") | **YES** |
| (S) Spec — preview1 | strong-but-contestable (no literal "cryptographically secure"; corroborated universally) | YES, with stated caveat |
| (S) Cross-runtime incl. Node.js | wazero anomalous vs Wasmtime, Wasmer, AND Node/V8 | **YES** |
| (S) Version trajectory | seed-42 persists through latest tag v1.12.0 | **YES** |
| (P) Prevalence | bounded sample (n=9): real non-zero unmitigated usage incl. generator-propagated default; AUTHENTICATED population scan BLOCKED | PARTIAL — real signal, auth-blocked residual |

**DISPOSITION: SUPPORT.** The decisive arm (D, guest-defensibility) HOLDS unambiguously — the
single most load-bearing question committee#2 raised resolves IN FAVOR. The spec + cross-runtime +
trajectory arms HOLD (with the honest preview1-vs-successor disambiguation). The prevalence arm
shows REAL unmitigated usage with a generator-propagation amplifier, but the authenticated
population scan is BLOCKED — so prevalence is real-signal, not a measured population ratio.

Per the pre-registered rule, the non-auth deliverables (1,2,3,5) STRONGLY support and the bounded
prevalence shows real unmitigated usage → **SUBMIT TO COMMITTEE#3 for the green shot**, with TWO
explicit residuals flagged for the committee:
1. **Auth-blocked prevalence** — the authenticated full-population AST scan with denominator + CI
   was not runnable (no gh/GITHUB_TOKEN on either node); escalate to dengcchi. The bounded n=9
   sample is signal, not a population estimate.
2. **preview1 spec strength** — the violation is unambiguous against the SUCCESSOR spec and a
   strong-interpretation breach of preview1 (corroborated by universal reference-implementation
   behavior incl. Node), but preview1's literal text says "high-quality," not "cryptographically
   secure."

This is an HONEST SUPPORT: the decisive defensibility test (which could have killed the arm)
came back confirming the hazard is un-defendable by correct guest code, and the mandatory Node.js
baseline confirms wazero is anomalous beyond the Rust ecosystem. Neither honest-negative branch
(guest-can-defend; Node-also-deterministic) triggered.

---

## 7. ARTIFACTS
- This RESULTS.md + PREREG.md (experiments/2026-06-05/EXP-0086/).
- Guest-defensibility test: cli:devvm14382 ~/wazero_l2/guest/main.go (Go wasip1 guest),
  ~/wazero_l2/host/main.go (wazero host, default|secure modes), ~/wazero_l2/guest/guest.wasm.
  Reproduce: `./hostrunner guest/guest.wasm default` (twice) vs `... secure`.
- Node.js baseline: ~/wazero_l2/node_wasi_run.js (run with
  `node --experimental-wasi-unstable-preview1 node_wasi_run.js guest/guest.wasm`).
- Prevalence scan: ~/wazero_l2/scan/scan.sh, repos.txt, scan_results.tsv, clones/ (9 wazero
  importers). go-plugin generator template: clones/go-plugin/gen/host.go:145,158.
- Spec text: preview1 random_get verbatim (docs.rs/ffmpeg-wasi __wasi_random_get == witx
  snapshot-01 == Wasmtime preview1 witx); successor wasi:random wit (from L1).
- wazero source confirmed at latest tag v1.12.0: internal/platform/crypto.go (seed=42),
  internal/sys/sys.go:151-152 (default wiring), imports/wasi_snapshot_preview1/random.go,
  internal/wasip1/*.go (full ABI surface — one randomness fn).
- NOTE: installs to clean up — node was pre-installed (v16, leave); Go clones in ~/wazero_l2 to
  remove after committee read (see §8).

## 8. CLEANUP
Clones + build artifacts under ~/wazero_l2 on cli:devvm14382 are scratch; remove after the
committee reads them. Node.js was already installed on the devvm (system package) — not removed.
No external systems were written to (READ-ONLY throughout: spec reads, clones, local builds).

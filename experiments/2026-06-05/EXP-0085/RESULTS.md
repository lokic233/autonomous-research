# RESULTS — EXP-0085 (CLAIM-0070, PROJ-0040) — L1 CHEAP-DECISIVE
Author: researcher-0070 | parent: orchestrator-r10-001 | 2026-06-05 | Nodes: cli:dengcchi-mac (engine + spec/source reads), cli:devvm14382 (prevalence sample)
Disposition: **SUPPORT** — both load-bearing cheap RE items ELEVATE the claim. RE-1 = CSPRNG contract; RE-3 = wazero is the cross-runtime anomaly. RE-4 = composition warning absent (shown, not asserted). RE-2 = bounded/auth-limited sample shows NON-ZERO real prevalence (signal, not exhaustive).

---

## 0. EXECUTIVE
The four committee#1 required-evidence items resolve IN FAVOR of the claim's HIGH-ALTITUDE framing:
1. **RE-1 (DECISIVE):** WASI preview1 `random_get` is the CSPRNG entropy source. The spec text mandates "high-quality random data" and BLOCKS on insufficient entropy (getrandom(2)/getentropy semantics); its direct WASI-0.2 successor `wasi:random/random.get-random-bytes` makes the CSPRNG contract EXPLICIT and FORBIDS deterministic implementations; and the canonical consumer (Rust `getrandom`) routes `random_get` through an API documented as "always provides ... cryptographically secure random data." => wazero's seed-42 default CONTRADICTS the entropy contract. "Silent demotion" is a TECHNICAL FACT, not editorial.
2. **RE-3:** wazero is the ANOMALY. Wasmtime defaults `wasi:random/random` to a per-context randomly-seeded CSPRNG (StdRng/ChaCha) + host clocks and tells guests they may rely on it for security invariants; Wasmer hardwires `random_get` to the OS CSPRNG (`getrandom::fill`) with NO deterministic path. Only wazero defaults to seed-42 math/rand + frozen clock. A guest portable across runtimes silently loses entropy ONLY on wazero's default.
3. **RE-4:** Shown (verbatim) that no single config.go doc string / example warns the COMPOUND effect.
4. **RE-2 (auth-limited):** GitHub code-search is auth-gated (401) and unavailable here. A bounded curated sample found a REAL bare-default in a mature general-purpose host (knqyf263/go-plugin) AND a mature host that explicitly fixed exactly this composition (wapC/wapc-go). Non-zero, non-strawman — but NOT an exhaustive prevalence figure.

---

## 1. RE-1 — WASI random_get ENTROPY CONTRACT (the single most load-bearing read)

### 1a. VERBATIM preview1 spec text (authoritative source)
Source: WebAssembly/WASI repo, branch `wasi-0.1`, `preview1/witx/wasi_snapshot_preview1.witx` (and rendered identically in `preview1/docs.md` §random_get):

> ;;; Write **high-quality random data** into a buffer.
> ;;; This function **blocks when the implementation is unable to immediately
> ;;; provide sufficient high-quality random data**.
> (@interface func (export "random_get")
>   ;;; The buffer to fill with random data.
>   (param $buf (@witx pointer u8))
>   (param $buf_len $size)
>   (result $error (expected (error $errno))))

The phrase "high-quality random data" + the BLOCKING-on-insufficient-entropy clause is the canonical `getrandom(2)` / `getentropy` contract (block until the CSPRNG is seeded). It is NOT the language of a deterministic stub. A fixed-seed math/rand PRNG (seed=42) can NEVER be "unable to provide sufficient high-quality random data," so it cannot satisfy the blocking semantics — i.e. wazero's default is not a conforming `random_get`.

### 1b. SUCCESSOR spec makes the contract EXPLICIT (interpretation evidence)
WASI 0.2 split random into TWO interfaces. The successor of `random_get`, `wasi:random/random.get-random-bytes` (proposals/random/wit/random.wit), states VERBATIM:

> /// Return `len` **cryptographically-secure** random or pseudo-random bytes.
> /// This function **must produce data at least as cryptographically secure and
> /// fast as an adequately seeded cryptographically-secure pseudo-random
> /// number generator (CSPRNG)**. ... The returned data **must always be unpredictable**.
> /// This function must always return fresh data. **Deterministic environments
> /// must omit this function, rather than implementing it with deterministic data.**

Insecure/deterministic RNG was deliberately quarantined into a SEPARATE interface `wasi:random/insecure` ("This function is not cryptographically secure. Do not use it for anything related to security."). The standards body's clear intent: the random_get lineage IS the CSPRNG entropy source; deterministic data is explicitly the WRONG implementation, to the point that a deterministic environment "must omit" the function rather than fake it.

### 1c. CONSUMER interpretation (the L0's own Rust guest)
Rust `getrandom` (rust-random/getrandom) preview1 backend (`src/backends/wasi_p1.rs`) imports host `random_get` and surfaces it through the `getrandom` crate, whose README states VERBATIM:

> It is assumed that the system always provides **high-quality, cryptographically secure random data**, ideally backed by hardware entropy sources.

`getrandom` maps `random_get` into the SAME CSPRNG-contract API as Linux `getrandom(2)`, macOS `getentropy`, Windows `ProcessPrng`. The live ecosystem treats `random_get` as the OS CSPRNG.

### RE-1 VERDICT: **CSPRNG-CONTRACT (spec mandates cryptographic quality).**
Spec text ("high-quality"+blocks-on-insufficient-entropy) + explicit successor mandate + universal consumer interpretation. wazero's fixed-seed-42 default DOES NOT satisfy this contract. The "silent CSPRNG demotion" framing is a TECHNICAL FACT. Claim ELEVATES to a spec-conformance finding (strong, GREEN-track). [Honest caveat: preview1's witx prose says "high-quality," not the literal words "cryptographically secure" — the explicit CSPRNG wording is in the successor. The strongest defensible statement: the documented contract + universal interpretation is CSPRNG-grade, and a fixed-seed PRNG provably cannot meet the blocking-on-insufficient-entropy clause. This is materially stronger than "documented design choice."]

---

## 2. RE-3 — CROSS-RUNTIME DEFAULT COMPARISON (is wazero the anomaly?)

### Wasmtime (Bytecode Alliance) — crates/wasi/src/ctx.rs (WasiCtxBuilder), v=main
Default doc (WasiCtxBuilder::new, lines 50-63), VERBATIM:
> * clocks use the host implementation of wall/monotonic clocks
> * RNGs are all initialized with **random state and suitable generator
>   quality to satisfy the requirements of WASI APIs**.

`secure_random` doc (lines 328-337), VERBATIM:
> Note that contexts have a default RNG configured which is a suitable generator for WASI and is **configured with a random seed per-context**.
> **Guest code may rely on this random number generator to produce fresh unpredictable random data in order to maintain its security invariants** ... so using any prerecorded or otherwise predictable data may compromise security.

Default construction (crates/wasi/src/random.rs): `impl Default for WasiRandomCtx { random: thread_rng() }` where `thread_rng() = StdRng::from_rng(rand::rng())` (StdRng = ChaCha-based CSPRNG, randomly seeded per context). Insecure path is a SEPARATE `SmallRng`. => **Wasmtime default = per-context CSPRNG + real host clocks.**

### Wasmer — lib/wasix/src/syscalls/wasi/random_get.rs, v=main
The `random_get` syscall body is UNCONDITIONAL:
> let res = getrandom::fill(&mut u8_buffer);   // OS CSPRNG; no deterministic option exists

=> **Wasmer default = OS CSPRNG (getrandom). No fixed-seed path at all.**

### wazero v1.12.0 (the L0 finding, source-confirmed here)
internal/platform/crypto.go VERBATIM: `const seed = int64(42)` ; `NewFakeRandSource() = rand.New(rand.NewSource(seed))`. internal/sys/sys.go default `SysContext`: randSource=NewFakeRandSource, walltime=NewFakeWalltime (frozen 2022-01-01 +1ms/read), nanotime=NewFakeNanotime (+1ms/read), nanosleep=FakeNanosleep (returns immediately).

### RE-3 VERDICT: **wazero is the ANOMALY.**
| Runtime | Default random_get | Default clocks |
|---------|-------------------|----------------|
| Wasmtime | per-context randomly-seeded CSPRNG (StdRng/ChaCha) | host wall+monotonic |
| Wasmer | OS CSPRNG (getrandom::fill), no det. path | host |
| **wazero v1.12.0** | **fixed-seed-42 math/rand PRNG** | **frozen fake (+1ms/read), nanosleep instant** |
A guest binary portable across all three silently loses entropy AND real-time semantics ONLY on wazero's default. Genuinely surprising cross-runtime differential. ELEVATES (GREEN-track).

---

## 3. RE-4 — COMPOSITION-WARNING DOC AUDIT (shown, not asserted)
wazero v1.12.0 config.go, VERBATIM interface doc strings (ModuleConfig):

- **WithRandSource:** "configures a source of random bytes. **Defaults to return a deterministic source.** You might override this with crypto/rand.Reader. This reader is most commonly used by the functions like \"random_get\" in \"wasi_snapshot_preview1\" ..."
- **WithWalltime:** "... **This defaults to a fake result that increases by 1ms on each reading.** ... Notes: - This does not default to time.Now as that violates sandboxing. - ... used to implement ... WASI `clock_time_get` ... realtime ... - Use WithSysWalltime for a usable implementation."
- **WithNanotime:** "... **Defaults to a fake result that increases by 1ms on each reading.** ... Notes: ... - Some compilers implement sleep by looping on sys.Nanotime (e.g. Go). - If you set this, you should probably set WithNanotime also. - Use WithSysNanotime for a usable implementation."
- **WithNanosleep:** "configures the how to pause the current goroutine ... **Defaults to return immediately.** ... Notes: ... - used to implement host functions such as WASI `poll_oneoff`. ... - Use WithSysNanosleep for a usable implementation."
- WithSysWalltime/WithSysNanotime/WithSysNanosleep: each only "uses time.Now/time.Sleep ... See WithX."

**SHOWN FACT:** Every doc string describes its OWN knob's default in isolation and justifies it by sandboxing; none states the COMPOUND consequence — that under bare `NewModuleConfig()` a textbook-secure guest (`ed25519.GenerateKey(rand.Reader)` / getrandom) produces predictable, globally-identical keys, or that deadlines/backoffs decouple from wall-clock. The `WithRandSource` doc even NAMES `random_get` in `wasi_snapshot_preview1` (so it knows it backs the WASI entropy syscall) yet frames the default only as a "deterministic source," never as "demotes the guest's CSPRNG." L0's asserted "none warns the composition" is now demonstrated with quoted text.

---

## 4. PRIOR-ART POSITIONING (honest novelty window)
- **SWC-120** "Weak Sources of Randomness from Chain Attributes" -> **CWE-330: Use of Insufficiently Random Values** (verbatim from swcregistry.io). The conceptual ancestor: a deterministic/manipulable execution environment demotes apparent randomness to predictable values, breaking guest security. SWC-120 is the EVM analogue of this wazero-ABI finding. MUST be cited (largest novelty_killer gap).
- **CWE-330 / CWE-338** (Use of Cryptographically Weak PRNG): the generic families. The composition is an instance, not the contribution.
- **CrowdSec PR #4495** "Fix obfuscator prng" (closed): body quotes wazero config.go:651-652 verbatim and adds back a real random source "else it would defeat the runtime obfuscation randomness." Real practitioner, real wazero embedding, independently hit + fixed.
- **wetware/pkg issue #106** "Use cryptographic PRNG with WithRandSource option" (closed): author realized WithRandSource "defaults to a (deterministic) stub" and "We definitely want to provide guests with crypto-grade entropy." Independently discovered.

**NOVELTY POSITION (honest):** The hazard is REAL (SWC-120/CWE folklore + two independent practitioner finds). What is NOT yet owned by any paper/CVE is the SYNTHESIS: (a) it is an ABI-BOUNDARY property (cross-LANGUAGE — Go ed25519 AND Rust getrandom both demoted, proving host-side, L0 §4), (b) it is a CROSS-RUNTIME differential (wazero anomalous vs Wasmtime/Wasmer, RE-3), (c) it is a COMPOSITION the guest cannot defend against by writing correct code (gold-standard crypto/rand still loses), and (d) the CLOCK-DECOUPLING half (rate-limiter/backoff/circuit-breaker misfire) is NOT RNG folklore and travels with the same default. The practitioner finds VALIDATE and simultaneously NARROW the window: people find+fix it without a paper. The contribution is the framing + cross-runtime spec-conformance positioning, NOT the bare CWE.

---

## 5. RE-2 — PREVALENCE (bounded, auth-limited; SIGNAL not exhaustive)
GitHub code-search API requires auth (HTTP 401 unauth; no gh/token available on either node). A full AST scan of all public wazero-dependents was therefore NOT executable here. Honest bounded probe instead: curated sample of known wazero-embedding Go projects, depth-1 clone (fwdproxy flaky; 7 of 10 landed with content), grep for NewModuleConfig/NewRuntime presence vs WithRandSource override, then manual entropy-relevance filter.

| Repo | wazero files | NewModuleConfig sites | WithRandSource | guest entropy-sensitive? | verdict |
|------|-------------|----------------------|----------------|--------------------------|---------|
| knqyf263/go-plugin | 28 | 25 | **0** | YES (general-purpose plugin host; arbitrary protobuf-defined guests) | **BARE-DEFAULT, real exposure** |
| wapc/wapc-go | 2 | 2 | **1** (`WithRandSource(rand.Reader).WithSysNanosleep().WithSysNanotime().WithSysWalltime()`) | YES (general WASM RPC host) | **OVERRIDES — fixed exactly this composition (both halves)** |
| arcjet/arcjet-go | 3 | 3 | 0 | NO (fixed first-party jsreq/redact guests) | bare-default but harmless |
| go-re2 | 2 | 1 | 0 | NO (regex engine, no entropy) | bare-default but harmless |
| stealthrocket/wazergo | 12 | 2 | 0 | (lib helpers) | n/a-ish |
| coraza-proxy-wasm, dapr/go-sdk | (no wazero in landed tree) | - | - | - | excluded |

INTERPRETATION (honest): in a tiny non-representative sample, BOTH endpoints appear — a mature general-purpose host that ships bare default with arbitrary-guest exposure (go-plugin), AND a mature host that explicitly fixed the full composition (wapc-go). This refutes the "pure strawman" worry (real general-purpose hosts do ship bare defaults; the fix is non-obvious enough that a notable host wires all four knobs at once). It does NOT establish the committee's >5%-of-mature-projects bar — that requires authenticated code-search/AST at scale, which is the proper EXPENSIVE L2 if the claim advances. RE-2 here = NON-ZERO real-world signal, scope-limited by tooling auth.

---

## 6. DISPOSITION: **SUPPORT** (elevated; submit to committee#2)
Per the pre-registered decision rule:
- RE-1 = CSPRNG-contract  ✅ (elevate)
- RE-3 = wazero-anomalous  ✅ (elevate)
- RE-4 = composition warning absent (shown)  ✅
- RE-2 = non-zero real prevalence signal (auth-limited; full scan deferred to L2)

Both load-bearing cheap items ELEVATE. The framing is "spec-conformance + cross-runtime differential + un-owned ABI-boundary composition," NOT "documentation-quality." Prior art (SWC-120/CWE/CrowdSec/wetware) is now cited and the novelty window honestly bounded to the synthesis. RECOMMEND advancing to committee#2 for a green shot, with explicit residual scope: (1) RE-2 full authenticated prevalence/AST scan + blast-radius is the natural L2; (2) responsible-disclosure posture (it's wazero's documented default, not a 0-day, but the compound hazard is undocumented — a docs/upstream-issue contribution is in-scope).

HONEST RESIDUAL WEAKNESSES (for committee#2): preview1 prose says "high-quality," literal "cryptographically secure" is in the SUCCESSOR not preview1 itself (mitigated by blocking-clause + universal consumer interpretation); RE-2 is signal not a prevalence figure; the practitioner finds narrow novelty to the synthesis/framing.

## 7. ARTIFACTS
- This RESULTS.md + PREREG.md.
- Spec/source reads (verbatim quotes inline, all from authoritative upstream): WASI wasi-0.1 preview1 witx+docs; WASI main proposals/random wit; rust-random/getrandom wasi_p1.rs+README; wasmtime crates/wasi ctx.rs+random.rs; wasmer lib/wasix random_get.rs; wazero v1.12.0 config.go + internal/platform/crypto.go + internal/sys/sys.go.
- RE-2 sample script + clone log on cli:devvm14382:/tmp/wzscan (repos.txt, clone.log, per-repo grep table reproduced in §5).

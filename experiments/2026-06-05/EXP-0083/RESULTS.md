# RESULTS — EXP-0083 (CLAIM-0070, PROJ-0040)
Author: researcher-0070 | 2026-06-05 | Node: cli:devvm14382 (Linux x86_64) | Level 0, CPU
Disposition: **SUPPORT** (strengthened to a cross-language ABI-boundary property; both controls held)

---

## 0. HEADLINE (lead with the COMPOSITION — gate-4 defense)
A DEFAULT wazero host config (`NewModuleConfig()`) silently **DEMOTES a CSPRNG to a fixed-seed PRNG
across the WASI ABI**, so a guest using the **gold-standard** crypto pattern
(`ed25519.GenerateKey(rand.Reader)` + crypto/rand token) produces **globally-identical, predictable
secrets across independent OS processes** — and this reproduces in a **second, unrelated language
(Rust/getrandom)**, proving it is a host/ABI-boundary property, NOT a Go-runtime quirk. SEPARATELY,
the same default config **decouples context.WithTimeout / time.After deadlines from real wall-clock**
(150ms of guest-perceived waiting collapses to ~4.8ms real). Neither the textbook-secure guest author
nor the host author writing minimal documented `NewModuleConfig()` treats this boundary as load-bearing,
and **no error surfaces**. The composition is **un-owned** (no wazero issue / CVE / paper). The clock
half is NOT RNG folklore.

---

## 1. PINNED VERSIONS
- wazero: **v1.12.0** (`go.sum`: `h1:DuWcpNu/FzgEXgGBDp8J1Spc+CWOvvtvVyjKlaZopYU=`,
  go.mod hash `h1:LvKtzl2RqO4gyF27BiXU+nKAjcV8f38U+kP/q2vgxh0=`)
- Go: go1.26.2 (guest: GOOS=wasip1 GOARCH=wasm)
- Rust: rustc 1.96.0, target wasm32-wasip1; getrandom v0.2.17 (-> `wasi 0.11.1+wasi-snapshot-preview1`,
  confirmed importing host `random_get`)
- golang.org/x/sys v0.44.0 (wazero indirect dep)

## 2. SOURCE-VERIFIED DEFAULTS (installed wazero@v1.12.0, in gomodcache)
Under `NewModuleConfig()` with no clock/rand overrides, `internal/sys/sys.go` (DefaultSysContext path)
installs:
- **random_get** -> `platform.NewFakeRandSource()` = `rand.New(rand.NewSource(42))` — a FIXED-SEED
  math/rand PRNG. (sys.go:151-152; internal/platform/crypto.go: `const seed = int64(42)`.)
- **walltime** -> `platform.NewFakeWalltime()` — frozen at `FakeEpochNanos` (2022-01-01 UTC),
  **+1ms per read** (sys.go:163-165; internal/platform/time.go:18-24).
- **nanotime** -> `platform.NewFakeNanotime()` — starts 0, **+1ms per read** (sys.go:174-175;
  time.go:28-34).
- **nanosleep** -> `platform.FakeNanosleep` — **returns immediately without sleeping**
  (sys.go:178-180; time.go:37).
config.go documents each knob INDIVIDUALLY (e.g. WithRandSource "Defaults to return a deterministic
source"; WithNanosleep "Defaults to return immediately") — NONE warns the COMPOSITION that the
gold-standard crypto/rand pattern is silently demoted, nor that deadlines decouple.

## 3. SECRET COLLISION — CROSS-PROCESS (Arm 1/1b primary; Arm 2 control)
N=30 SEPARATE OS processes (fork/exec of the host binary from the shell), same .wasm.
| Arm | Config | guest | distinct (PUB,TOKEN) / N | collision rate |
|-----|--------|-------|--------------------------|----------------|
| 1   | DEFAULT | Go (with clock phases) | **1 / 30** | **100%** |
| 1b  | DEFAULT | Go (secret-only)       | **1 / 30** | **100%** |
| 2   | WithRandSource(crypto/rand.Reader) | Go | **30 / 30** | **0%** |

DEFAULT pubkey (both Go binaries, all 30 procs each): `46a4405f...641cb876`; token `083f61d3...6fe34cdc`
— **byte-identical**, and matches scout-BB's value. Note two DIFFERENT Go binaries yielded the SAME
key under default — first hint it's host-side. Control => all 30 keys distinct. **Control HELD.**
Collision rate (100%) >> birthday bound for 30 draws over a 2^256 space (~0). **IT-MATTERS threshold met.**

## 4. CROSS-LANGUAGE ARM — the ABI-boundary proof (Arm 3)
Rust guest (`getrandom` -> WASI `random_get`), N=10 separate processes:
| Config | distinct 32-byte outputs / N | result |
|--------|------------------------------|--------|
| DEFAULT | **1 / 10** (all `538c7f96...09dd9d52`) | 100% identical |
| WithRandSource(crypto/rand.Reader) | **10 / 10** | all distinct |

The Rust bytes differ from the Go key bytes (different consumption: Go ed25519 reads a 32-byte seed
first; Rust reads 32 bytes directly) — but BOTH are 100% deterministic across processes because both
draw from the SAME host seed-42 PRNG stream. **=> This is a wazero host/ABI-boundary property, NOT a
Go-runtime quirk.** This is the green-strengthener over the folklore gate.

## 5. CLOCK DECOUPLING (Arm 4 default; Arm 5 control)
Clock-only guest: `time.After(100ms)` then `context.WithTimeout(50ms)` wait-on-Done. Host measures
real wall around the whole run. N=5 each.
| Arm | Config | guest-perceived (After / Ctx) | host real wall (whole run) | deadline/wall |
|-----|--------|-------------------------------|----------------------------|---------------|
| 4 | DEFAULT | ~105ms / ~50ms (=150ms wait) | **~4.8ms** | **~0.03 (≈31x faster than real)** |
| 5 | WithSysWalltime+Nanotime+Nanosleep | ~100.4ms / ~50.3ms | **~155.5ms** | **~1.0** |

Under DEFAULT, 150ms of guest-intended waiting consumes ~4.8ms of real wall (nanosleep instant; time
only advances via fake-clock reads). The context deadline DOES fire (`context deadline exceeded`) and
the guest PERCEIVES correct durations — but they are decoupled from real time. A rate-limiter / retry
backoff / circuit-breaker / token-bucket built on these primitives misfires silently. Control => ratio
≈ 1.0, deadlines track real wall. **Control HELD. IT-MATTERS threshold met.** (Note: an earlier
busy-poll variant with a 200M-iter cap blew the cap at only ~1ms guest time under DEFAULT — same
decoupling, observed via a different mechanism.)

## 6. PRE-REGISTERED NULL — did NOT trigger (falsifiability honored)
- keys differ run-to-run across processes? NO (100% identical, both languages).
- wazero errors on random_get with no source? NO (returns fixed-seed bytes, exit 0).
- crypto/rand bypasses WASI via internal entropy? NO (Go AND Rust both routed through random_get and
  both got the host PRNG => the WASI import is the path).
- cross-language gets different bytes (Go quirk)? NO (Rust also 100% deterministic under default).
- deadline/wall ratio ~1.0 under default? NO (~0.03).
- recent/default wazero changed behavior? v1.12.0 (latest at run) still has fixed-seed + frozen clock.

## 7. NOVELTY / OWNERSHIP RE-CHECK
Web re-check: wazero docs document each knob individually; generic predictable-RNG->collision is CWE
folklore. NO wazero issue / CVE / paper owns the COMPOSITION (default-config-demotes-gold-standard-
crypto/rand-across-the-ABI) NOR the clock-decoupling-as-guest-correctness-hazard. Composition UN-OWNED.

## 8. DISPOSITION: SUPPORT
All pre-registered IT-MATTERS thresholds met; both controls held; every null-exit path checked and
none triggered; strengthened to a cross-LANGUAGE cross-PROCESS ABI-boundary property. Submit to committee.

## 9. ARTIFACTS (in artifacts/exp0083_bundle/)
- src/: host_main.go (mode-switched harness), guest_go_main.go, guest_secret_main.go,
  guest_clock_main.go, guest_rust_main.rs, guest_rust_Cargo.toml, go.mod, go.sum (wazero pin).
- wasm/: guest_secret.wasm, guest_clock.wasm, guest_rust.wasm.
- results/: arm1_default, arm1b_default, arm2_randcontrol, arm3_rust_default, arm3_rust_randcontrol,
  arm4_clock_default, arm5_clockcontrol, smoke_default — raw stdout.
- REPRO: `go get github.com/tetratelabs/wazero@v1.12.0`; build guests with GOOS=wasip1 / cargo
  --target wasm32-wasip1; `./hostrun {default|randcontrol|clockcontrol} <guest.wasm>` N times from shell.

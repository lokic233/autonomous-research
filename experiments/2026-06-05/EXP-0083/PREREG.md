# PRE-REGISTRATION — EXP-0083 (CLAIM-0070, PROJ-0040)
Author: researcher-0070  |  Pre-registered BEFORE any measurement.  |  2026-06-05

## CLAIM UNDER TEST
Under wazero v1.12.0 DEFAULT ModuleConfig (NewModuleConfig()), a Go-WASI (GOOS=wasip1) guest using
the gold-standard crypto/rand pattern (ed25519.GenerateKey(rand.Reader) + crypto/rand 32-byte token)
produces GLOBALLY-IDENTICAL + PREDICTABLE secrets across independent runs/PROCESSES (default
random_get = fixed-seed PRNG), AND context.WithTimeout/time.After deadlines DECOUPLE from real
wall-clock (default clock frozen+1ms, nanosleep instant) — both silently, no error, at the
host<->WASI ABI boundary. Strengthen to an ABI-boundary property: cross-PROCESS + cross-LANGUAGE.

## ENVIRONMENT (pinned at run time — recorded in RESULTS)
- Node: cli:devvm14382 (Linux x86_64). Go: go1.26.2.
- wazero: pin exact version via `go get github.com/tetratelabs/wazero@v1.12.0` (record go.sum hash).
- Guest A (Go): GOOS=wasip1 GOARCH=wasm.
- Guest B (cross-language): Rust wasm32-wasip1 (getrandom/rand) if toolchain installs cleanly;
  ELSE a hand-written minimal WASI module that calls random_get directly. At minimum prove the
  host default is the cause via a non-Go guest path.

## SOURCE-VERIFICATION (do before trusting behavior)
- Confirm in INSTALLED wazero source that default random_get uses a fixed-seed deterministic source
  and default clock is frozen+fixed-increment (cite file:line in gomodcache).

## EXPERIMENTAL DESIGN
### Arm 1 — Secret collision, CROSS-PROCESS (primary)
Run the SAME guest.wasm under DEFAULT config via N=30 SEPARATE OS processes (fork/exec host binary
N times from the shell). Record ed25519 PUB + TOKEN each run.
- Metric: fraction of the N runs producing a byte-identical (PUB,TOKEN) pair.
### Arm 2 — Secret collision CONTROL
Same N runs under `WithRandSource(crypto/rand.Reader)`. Metric: distinct keys.
### Arm 3 — Cross-LANGUAGE (ABI-boundary proof)
Run guest B (Rust or minimal WASI random_get) under DEFAULT config across N>=5 separate processes.
- Metric: are the random bytes byte-identical across runs? (predictable => ABI-boundary property,
  not a Go-runtime quirk).
### Arm 4 — Clock decoupling (primary)
Under DEFAULT config: guest-perceived elapsed for context.WithTimeout(50ms) and time.After(100ms)
vs host-measured real wall-clock for the whole run. N>=5.
### Arm 5 — Clock CONTROL
Same under WithSysWalltime/WithSysNanotime/WithSysNanosleep. Metric: deadline tracks real time.

## PRE-REGISTERED NULL (what would make this a NEGATIVE / kill)
- Secret collision rate across separate processes ~0 (keys differ run-to-run), OR
- wazero ERRORS on random_get with no source, OR
- crypto/rand BYPASSES WASI (internal entropy path) so keys differ, OR
- cross-language guest gets DIFFERENT bytes (=> Go-runtime quirk, not ABI), OR
- deadline/wall ratio ~1.0 under default (clock tracks real time), OR
- a recent/default wazero version changed this behavior.
Any of these => honest WEAKEN or KILL. Do NOT rig (no reusing one process's output).

## IT-MATTERS THRESHOLD (what counts as SUPPORT)
- Cross-PROCESS secret-collision rate >> birthday bound — i.e. ~100% byte-identical across
  separate processes under default; AND control => all-distinct keys.
- Cross-LANGUAGE guest ALSO predictable/identical under default => ABI-boundary property.
- Deadline/wall ratio grossly != 1.0 under default (guest perceives ~0 for a 50ms/100ms wait while
  real wall differs); AND control => ratio ~1.0.

## NOVELTY FRAMING (gate-4 defense, lead RESULTS with this)
NOT "wazero default rand is deterministic" (per-knob documented + predictable-RNG->collision = CWE
folklore). Contribution = the COMPOSITION/abstraction-leak: a DEFAULT host config silently DEMOTES a
CSPRNG to a fixed PRNG across the WASI ABI so the gold-standard crypto/rand pattern does NOT protect
a competent guest author — cross-LANGUAGE (ABI-boundary, not Go-specific) — PLUS the clock-decoupling
half (silent rate-limiter/retry/circuit-breaker misfire), which is NOT RNG folklore. Re-confirm
un-owned (no wazero issue/CVE/paper owns the composition).

## CLEANUP
After: remove Go modcache, build dirs, Rust toolchain artifacts on devvm14382.

# PROJ-0040 — IMMATURE-WEDGE (OS-runtimes/security): wazero default ModuleConfig silently DEMOTES a Go-WASI guest's crypto/rand CSPRNG -> fixed PRNG + decouples context/time deadlines from real time, at the host<->WASI ABI boundary (NEW NON-OBVIOUS COUPLING)

FRESH-DOMAIN resume, IMMATURE-WEDGE seam (the only un-saturated path per FRONTIER_EXHAUSTION_r10_freshdomains.md: young
tools postdate the Jepsen/CVE/ReproBLAS waves -> high-prevalence seams not yet documented BECAUSE the field is young).
CLAIM-0059 winning shape. scout-BB GO 7/10, pre-verified on real wazero v1.12.0.

## THE SEAM (two independently-owned subsystems, across the WASI ABI)
- A = Go wasip1 GUEST: crypto/rand.Reader, ed25519.GenerateKey(rand.Reader), context.WithTimeout, time.After -- assumes a
  real CSPRNG + real monotonic clock (crypto/rand's whole contract = unpredictable).
- B = wazero HOST NewModuleConfig() DEFAULTS (deliberate sandbox choice): random_get = fixed-seed math/rand;
  clock_time_get realtime = frozen 2022-01-01 +1ms/read; monotonic = 1ms/read fake; nanosleep = returns immediately.
- DIVERGENCE: A's secure-by-construction code, run under B's minimal documented default, silently yields predictable
  globally-identical secrets + deadlines decoupled from wall-clock. No error at the boundary.

## PRIMARY THESIS (verified on devvm14382, clean A/B)
Same .wasm + default config -> byte-identical ed25519 pubkey 46a4405f...641cb876 + identical session token across runs;
WithRandSource(crypto/rand.Reader) -> different key. Clock: 50ms context.WithTimeout saw ~4ms guest time (blew the 2M-iter
cap); time.After(100ms) took 939ms real wall; WithSysWalltime/Nanotime/Nanosleep -> correct (50ms@153ms, 100ms@100.5ms).

## NOVELTY (the composition / abstraction-leak — MUST headline; gate-4 defense)
NOT "wazero default rand is deterministic" (per-knob DOCUMENTED + predictable-RNG->collision is CWE folklore = DEAD). The
surviving claim: a DEFAULT host config DEMOTES a CSPRNG to a fixed PRNG ACROSS THE WASI ABI so the GOLD-STANDARD crypto/rand
pattern does NOT protect you (guest-does-everything-right-yet-loses), UN-OWNED for this young runtime; + the CLOCK-DECOUPLING
half (silent rate-limiter/retry/circuit-breaker misfire) which is NOT RNG folklore + independently surprising.

## 6-GATE SCREEN (cleared — see CLAIM-0070)
#1 incremental-composition PASS (emergent join; no surface warns crypto/rand is demoted). #2 verify PASS (installed+probed
v1.12.0). #3 issue/CVE/paper PASS (composition UN-OWNED; only generic RNG-CWE + unrelated Go preempt #60857). #4 not-folklore
= WEAK gate (lead with composition + clock half). #5 prevalence PASS (crypto/rand tokens/keys + context.WithTimeout ubiquitous;
NewModuleConfig() canonical; real adoption CosmWasm/Dapr/Arcjet). #6 not-tautology PASS (byte-identical, could have nulled).

## L0 / NULL EXIT
Measured: collision rate across runs (observed 100% under default; ~0 under control); deadline/wall ratio (gross divergence
under default; ~1.0 under control). NULL EXIT: keys differ run-to-run / wazero errors on random_get / crypto/rand bypasses
WASI -> none happened. ★ L0 STRENGTHENING (for the green): test across SEPARATE OS processes/machines + other guest langs
(Rust/AssemblyScript wasip1) to prove it's an ABI-boundary property, not a Go-runtime quirk.

## HONEST RISK
Gate 4: committee may rule the security half documented-CWE-folklore-dressed-up -> defense = the boundary-demotion COMPOSITION
+ the clock half. scout-BB 7/10.

## POSTURE
EXPAND-LIGHTWEIGHT: ONE sharp claim (CLAIM-0070), normal pipeline. L0 = the cross-process/cross-lang ABI-boundary
verification + clock-decoupling. Owner: orchestrator-r10-001.

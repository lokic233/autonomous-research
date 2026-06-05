# RESULTS — EXP-0087 (CLAIM-0072)
researcher-0072 | PROJ-0042 | level 0 | compute on cli:devvm14382 | engine on cli:dengcchi-mac
Disposition: **SUPPORT** (with two honestly-documented divergences from scout-CC; core claim reproduced + strengthened)

## 0. PINNED VERSION (resolved + verified)
- **zenoh = 1.9.0** (Cargo.lock, registry crates.io) — confirmed on the 1.x line, exactly the target.
- tokio 1.52.3, tracing (for log control), rustc/cargo **1.96.0**, edition 2024.
- Installed source root: `~/.cargo/registry/src/index.crates.io-*/zenoh-{protocol,transport,config}-1.9.0/`

## 1. ★ VERIFIED SPLIT-DEFAULT CONSTANTS (installed source — NOT assumed)
`zenoh-protocol-1.9.0/src/core/mod.rs` (lines 631-657):
```
pub const DEFAULT: Self = Self::Drop;
DEFAULT_PUSH     = Drop    // data-plane  (Publisher::put)
DEFAULT_REQUEST  = Block   // control-plane (get / queries)
DEFAULT_DECLARE  = Block
DEFAULT_INTEREST = Block
DEFAULT_OAM      = Block
```
The split is REAL and in the shipped binary: a dev who validated reliability with `get()` (Block,
never drops) then switches to `put()` (Drop) silently flips the contract. The `Block` doc comment
literally says "the node will wait for queue to progress" — defined PER-NODE (per-hop), confirming
the routing-fabric framing.

Supporting source facts (also verified):
- `is_droppable() = !is_reliable() || congestion_control()==Drop`  (network/mod.rs:190).
- `Reliability::DEFAULT = Reliable` (core/mod.rs:517) — but on the STABLE API `reliability` is a
  `#[cfg(feature="unstable")]` field, so stable `put()` is always Reliable and reliability is NOT
  user-settable. So with CC=Block, `is_droppable()=false` at the publisher's OWN egress pipeline.
- `TransmissionPipelineProducer::push_network_message` (transport/common/pipeline.rs:884): on
  congestion of a droppable msg it does `return Ok(false)` — **silent drop, returns Ok, NO log call
  anywhere in the path**. This is the source-level proof the loss is silent.
- QoS unicast `enabled: true` by default (config/defaults.rs:226) — so CC distinctions ARE active.

## 2. ARM 1 — 2-SESSION slow_us SWEEP (default Drop, N=50000, 8-byte, tcp/127.0.0.1, multicast+gossip OFF)
| slow_us | received | delivery_ratio | silent loss | put_ok | put_err |
|--------:|---------:|---------------:|------------:|-------:|--------:|
|       0 |    50000 |         1.0000 |   0.00%     |  50000 |       0 |   ← NULL/CONTROL fires
|      50 |    50000 |         1.0000 |   0.00%     |  50000 |       0 |
|     100 |    41515 |         0.8303 |  16.97%     |  50000 |       0 |
|     200 |    25518 |         0.5104 |  48.96%     |  50000 |       0 |
|     500 |    21004 |         0.4201 |  57.99%     |  50000 |       0 |
**put() returned Ok for 100% of messages (put_ok=N, put_err=0) in EVERY case** while up to ~58%
were silently dropped to the slow subscriber. Loss is **monotone** in consumer slowness. The
fast-consumer control (slow_us=0) → 0.00% loss → the null CAN fire (NOT a tautology).
(Threshold "silent loss > 10% under default" → MET at slow_us>=100.)

Note: my peak loss (~58%) is a bit below scout-CC's 68-77%. Same mechanism, same monotone shape,
well over the 10% it-matters threshold; the exact ratio is harness/timing dependent (drain-after-burst
recovers more in my harness). Honestly noted.

## 3. ★ ARM 2 — THE BLOCK KNOB (green-anchor): Block does NOT prevent loss, does NOT backpressure
| slow_us | mode  | pub_wall | received | delivery | loss   | put_ok | put_err |
|--------:|-------|---------:|---------:|---------:|-------:|-------:|--------:|
|     200 | Drop  | 5.018s   |    29598 |   0.5920 | 40.80% |  50000 |       0 |
|     200 | Block | 5.020s   |    24743 |   0.4949 | 50.51% |  50000 |       0 |
|     500 | Block |    —     |    17942 |   0.3588 | 64.12% |  50000 |       0 |
**`CongestionControl::Block` does NOT prevent the loss** (50.5% vs 40.8% — same/worse, within noise)
**and does NOT backpressure the publisher** (pub_wall identical ~5.0s for Drop vs Block). If Block were
end-to-end the publisher would be throttled to the sub's pace (50000×200µs ≈ 10s) and deliver all;
instead it races through in 5s and ~half vanish. **Block is per-hop, not end-to-end.** (Threshold MET.)

## 4. ★ ARM 3 — 3-NODE ROUTER TOPOLOGY (green-STRENGTHENER): unambiguous per-hop proof
Topology: pub(client) → **zenoh router process (mode=router)** → slow sub(client). Router verified
forwarding (own ZID 27de6dc3…, listening tcp/127.0.0.1:7500, INFO logs confirm router mode; N=10 → 10/10).

| N      | slow_us | publisher mode | received | delivery | loss   | put_ok  | put_err |
|-------:|--------:|----------------|---------:|---------:|-------:|--------:|--------:|
|  50000 |    1000 | Drop           |    50000 |   1.0000 |  0.00% |   50000 |       0 |  ← router buffers absorb burst
|  50000 |    1000 | Block          |    50000 |   1.0000 |  0.00% |   50000 |       0 |
| 200000 |     200 | Drop           |    97937 |   0.4897 | 51.03% |  200000 |       0 |  ← router→sub hop overflows
| 200000 |     200 | **Block**      |    72465 |   0.3623 |**63.77%**| 200000 |     0 |  ← ★ PUBLISHER-BLOCK STILL LOSES

**★ THE UNAMBIGUOUS RESULT:** with the publisher set to `CongestionControl::Block`, the 3-node
topology STILL drops **63.77%** (put_ok=200000, put_err=0). The loss occurs at the **router's
forwarding hop to the slow subscriber** — the publisher's Block does NOT propagate through the
router. This is per-hop, not end-to-end, proven unambiguously. (Threshold MET.)

HONEST nuance: at N=50000 the router fully buffers the burst → 0% loss (publisher's Block irrelevant
because the bottleneck hop never overflowed). The per-hop drop only manifests once the router→sub hop
is genuinely congested (N=200000). The claim's strong form ("loss persists at the router with
publisher-Block") IS confirmed, but requires enough sustained load to overflow the router's buffers.

## 5. CONTROLS
(a) **fast consumer (slow_us=0) → 0.00% loss** — null fires, rules out tautology. ✓ (see Arm 1)
(b) **offload sub callback to unbounded channel:**
    | slow_us | offload | received | delivery | loss   |
    |--------:|--------:|---------:|---------:|-------:|
    |     200 |     no  |    29321 |   0.5864 | 41.36% |
    |     200 |    yes  |    50000 |   1.0000 |  0.00% |
    ★ DIVERGENCE FROM SCOUT: scout-CC saw offload STILL lose 68.7%; I see offload → **0% loss**.
    Mechanistically illuminating, not a contradiction: zenoh delivers via a SYNCHRONOUS callback on
    the transport RX thread (`trigger_callback`→`handle_message`, transport/unicast/universal/rx.rs:64).
    When the callback BLOCKS (offload=no) the RX thread stalls → TCP backpressure → upstream congestion
    drop. When OFFLOADED (offload=yes) the RX thread never blocks → no congestion → no drop. This
    LOCALIZES the drop to the transport-congestion path driven by a blocked receive dispatch — it
    confirms the drop is in the transport/forwarding path (congestion), but it is NOT independent of
    whether the receive dispatch keeps up. Reported honestly; it refines rather than breaks the claim.
(c) **silent (no log):** RUST_LOG=zenoh=debug during the 50000-msg run with 43.73% loss → **0 zenoh
    log lines total, 0 drop/congest/discard/full/overflow lines.** Logging proven FUNCTIONAL via a
    smoke test (same binary/init emits `zenoh` + `zenoh::transport` debug lines on demand) AND the
    router emits INFO lines in-process — so the data-plane drop is genuinely uninstrumented/silent,
    not a broken logger. ✓ (Threshold "no log" MET.)

## 6. DISPOSITION: SUPPORT
All four it-matters threshold conditions MET:
1. ✓ Silent loss > 10% under default to a slow consumer (16.97%→57.99%), put_ok=N, put_err=0, no log.
2. ✓ CongestionControl::Block does NOT prevent the loss (and does not backpressure → not end-to-end).
3. ✓ 3-node router topology confirms per-hop loss with publisher-Block set (63.77% at N=200000).
4. ✓ Controls behave: fast-consumer=0% (null fires); silent at zenoh=debug (proven functional logger).

NOVELTY FRAMING (lead RESULTS): the contribution is NOT "best-effort PUSH drops" (folklore). It is
(a) the SPLIT default (control=Block / data=Drop, verified in source) silently flipping the
reliability contract between get() and put(), and (b) CongestionControl::Block MEASURABLY failing to
prevent end-to-end loss (per-hop, proven by the 3-node router) with NO doc warning and NO debug log.

HONEST WEAKENINGS (do NOT overclaim):
- Loss magnitude ~41-64% (mine) vs 68-77% (scout) — same mechanism, harness/timing dependent.
- 3-node per-hop loss requires sustained load (N=200K) to overflow router buffers; at light load the
  router absorbs the burst (0% loss). The per-hop proof holds, conditioned on the bottleneck hop
  actually congesting.
- offload control → 0% (not scout's 68.7%): zenoh uses a SYNCHRONOUS RX callback, so offloading the
  callback removes the backpressure that causes the drop. This localizes the mechanism (transport
  congestion driven by a blocked receive dispatch) but means the drop is not independent of receive-
  side keep-up. A committee reviewer should see this framing, not a "drop regardless of app" claim.

## 7. REPRODUCIBILITY
- Harness: `~/zenoh_exp0087/src/main.rs` (165 lines, roles: pub/sub/router; flags
  --listen/--connect/--client/--n/--slow-us/--block/--offload). `zenoh::init_log_from_env_or("error")`.
- Runners + raw logs archived: `~/exp0087_logs/` (sweep2_out, arm2_out, blockverify_out, arm3c_out,
  arm3stress_out, offload2_out, dbgfinal_out, arm3verify_out, source_facts.txt).
- Build: PATH=$HOME/.cargo/bin, http(s)_proxy=fwdproxy:8080, `cargo build --release` (~66s cold).
- Cleanup performed after measurement (see CLEANUP section in experiment notes).

# PRE-REGISTRATION — EXP-0087 (CLAIM-0072)
researcher-0072 | PROJ-0042 | level 0 | pre-registered BEFORE the measured runs.

## CLAIM UNDER TEST
zenoh 1.9.0 (default ROS 2 RMW transport): `Publisher::put()` returns `Ok(())` for 100% of
messages while a large fraction (scout-CC: 68-77%) is SILENTLY dropped to a slow subscriber.
`CongestionControl::Block` (the documented anti-drop knob) does NOT prevent the loss because
zenoh's congestion control is PER-HOP, not end-to-end. Novel mechanism: a SPLIT default
(data-plane PUSH = Drop, control-plane REQUEST/DECLARE/INTEREST/OAM = Block) + a per-hop fabric.

## PINNED VERSION (resolved + verified in installed source)
- zenoh = 1.9.0 (Cargo.lock), tokio 1.52.3, rustc/cargo 1.96.0, edition 2024.
- Installed source: ~/.cargo/registry/.../zenoh-protocol-1.9.0/src/core/mod.rs
- Verified split-default constants (lines 631-658):
    `pub const DEFAULT: Self = Self::Drop;`
    `DEFAULT_PUSH    = Drop`   (data-plane / put)
    `DEFAULT_REQUEST = Block`  (control-plane / get)
    `DEFAULT_DECLARE = Block`
    `DEFAULT_INTEREST= Block`
    `DEFAULT_OAM     = Block`
  Doc comment on Block: "node will wait for queue to progress" — i.e. defined PER-NODE (per-hop).

## PRE-REGISTERED NULL
H0 (no silent loss): `put() -> Ok` IMPLIES delivered. If loss occurs it surfaces as `put_err > 0`
OR a drop/congestion log line at RUST_LOG=zenoh=debug. Under H0, delivery_ratio ~ 1.0 for all
slowness, OR put_err tracks the loss, OR a log records it.

## IT-MATTERS THRESHOLD (pre-set)
Claim SUPPORTED iff ALL of:
1. Under DEFAULT (Drop) to a slow consumer: silent loss > 10% with put_ok = N, put_err = 0, and
   NO drop/congestion log at zenoh=debug.
2. `CongestionControl::Block` on the publisher does NOT prevent the loss (loss still > 10%).
3. The 3-node (pub -> zenohd router -> slow sub) topology shows per-hop loss persists with the
   PUBLISHER set to Block (the publisher's Block does not propagate through the router).
4. Controls behave: fast consumer (slow_us=0) -> ~0% loss (null CAN fire); offload-to-channel
   still loses (drop is in transport/forwarding path, not the app callback).

## EXPERIMENT PLAN
Fixed: N = 50000 messages, 8-byte payload (AVOID #1494 fragmentation bug — small payloads only),
tcp/127.0.0.1, multicast/gossip/scouting DISABLED (explicit endpoints). pub sends as fast as
possible; sub callback sleeps `slow_us` per message. delivery_ratio = received / N.

### ARM 1 — 2-session reproduce (slow_us sweep)
publisher (default Drop) -> subscriber, slow_us in {0, 50, 200}. Record received, put_ok, put_err.
Expect: 0us -> ~0% loss (CONTROL/null); loss monotone increasing in slowness.

### ARM 2 — Block knob (the green-anchor)
Same 2-session setup, publisher `.congestion_control(Block)`, slow_us=200. Expect loss PERSISTS.

### ARM 3 — 3-node router topology (the green-STRENGTHENER, unambiguous per-hop proof)
Install `zenohd`. pub connects to router, slow sub connects to router, router forwards.
Measure delivery under (a) default Drop, (b) publisher Block, slow_us=200. Expect loss persists
under publisher-Block -> the publisher's Block does NOT propagate through the router's forwarding hop.

### CONTROLS
(a) fast consumer slow_us=0 -> ~0% loss (rules out tautology — null can fire).
(b) offload sub callback to an unbounded channel (RX never blocks) -> if loss persists, drop is in
    transport/forwarding path, not the app callback.
(c) RUST_LOG=zenoh=debug -> confirm NO drop/congestion log line (loss is silent).

## COULD-IT-FAIL (honest exits — report as WEAKEN/KILL)
- put() returns Err on drop -> not silent -> WEAKEN.
- a drop/congestion log appears at zenoh=debug -> not silent -> WEAKEN.
- Block DOES prevent loss end-to-end -> the sharp result fails -> KILL the Block-anchor.
- fast consumer (slow_us=0) ALSO loses -> tautology/harness bug -> KILL.
- 3-node router with publisher-Block shows NO loss -> per-hop claim fails -> WEAKEN.
- zenoh resolved to a non-1.x line or changed the default -> report honestly.

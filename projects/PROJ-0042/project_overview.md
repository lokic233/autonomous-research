# PROJ-0042 — IMMATURE-WEDGE (distributed-systems/OS-runtimes): zenoh put() returns Ok while silently dropping 68-77% to a slow subscriber, AND CongestionControl::Block does NOT prevent it (per-hop not end-to-end) (NEW NON-OBVIOUS COUPLING)

scout-CC GO 8.5/10 — highest-rated immature-wedge candidate; clears BOTH the fjall mature-lineage cap AND the POSIX
barrier. CLAIM-0059/wazero winning shape. zenoh 1.9.0 = default ROS 2 transport, genuinely young (1.0 late 2024).

## THE SEAM (verified in installed source)
- A = Publisher QoS (data-plane/PUSH): default CongestionControl::Drop (DEFAULT_PUSH=Drop, zenoh-protocol core/mod.rs).
- B = control-plane QoS + the receiver-side forwarding node's OWN per-hop QoS: DEFAULT_REQUEST/DECLARE=Block. A dev who
  validated reliability with get() (Block, never drops) then switches to put() (Drop) silently flips contract; even put()
  with Block loses because the downstream forwarding node applies its OWN per-hop Drop -- the publisher's Block does NOT propagate.

## PRIMARY THESIS (verified, devvm14382, N=50000 8-byte, 2 sessions tcp/127.0.0.1)
put() returns Ok for 100% while 68-77% silently dropped to a slow subscriber (put_ok=50000 put_err=0 received~15600).
Loss monotone in consumer slowness (0us->0%, 50us->43%, 200us->69-77%). CongestionControl::Block -> STILL 68.5% loss
(Block did not block) = per-hop not end-to-end. Offload-to-unbounded-channel control -> STILL 68.7% = drop in transport/
forwarding path, not the app callback. Fully silent (no error, no debug log at RUST_LOG=zenoh=debug). NULL EXIT: fast
consumer (slow_us=0) -> 0.00% loss (rules out tautology).

## NOVELTY (MUST headline; the green-anchor)
NOT "best-effort PUSH drops, standard pub/sub" (folklore). The un-owned surprising composition: (a) the SPLIT default
(control=Block / data=Drop) silently flips contract between get and put; (b) CongestionControl::Block MEASURABLY fails
end-to-end with NO doc warning. zenoh's OWN novel per-hop split-default data-centric routing fabric.

## ★★ CLEARS fjall MATURE-LINEAGE CAP: mechanism GENUINELY NEW to zenoh, NOT inherited. Resembles MQTT-QoS/DDS-RELIABILITY/
TCP-flow-control superficially, but those are END-TO-END (acked/windowed); zenoh INVERTED to a novel SPLIT default + PER-HOP
fabric (doc defines CC per-node), verified in source. Seam in zenoh's novel part, not a reimplemented-classic.
## ★ CLEARS POSIX BARRIER: non-crash semantic/abstraction-leak seam (wazero-shaped), barrier N/A.

## 6-GATE SCREEN (cleared — see CLAIM-0072)
#1 incremental-composition (neither the Ok-put API nor the Block knob predicts silent end-to-end loss; docs don't warn).
#2 verify (installed+built+measured zenoh 1.9.0). #3 issue-tracker/CVE/paper + mature-lineage: UN-OWNED (#1494 is a
different fragmentation bug; the composition is not in tracker; mechanism novel-not-inherited). #4 not-folklore (no doc
warning, no debug log). #5 prevalence (default put + slow consumer ubiquitous; IS the ROS 2 default transport). #6
not-tautology (fast-consumer control -> 0.00% loss).

## HONEST RISK
"best-effort drops, standard pub/sub" -> ANCHOR on the split-default contract-flip + Block-not-end-to-end (NOT "drops").
Mitigations: small 8-byte payloads (avoid #1494 fragmentation confusion); for GREEN add explicit 3-node
pub->zenohd-router->slow-sub topology to make per-hop!=end-to-end unambiguous. scout-CC 8.5/10.

## POSTURE
EXPAND-LIGHTWEIGHT: ONE sharp claim (CLAIM-0072), normal pipeline. L0 reproduce + the 3-node router topology. Owner: orchestrator-r11-001.

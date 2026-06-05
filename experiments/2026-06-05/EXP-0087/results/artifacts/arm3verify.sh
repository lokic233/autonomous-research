#!/bin/bash
cd ~/zenoh_exp0087
BIN=./target/release/zenoh_exp0087
RTR=tcp/127.0.0.1:7500
LOG=~/exp0087_logs/arm3verify_out.txt
: > $LOG
# Verify routing: start router with debug, sub+pub as clients, small N, confirm router logs forwarding
pkill -9 -f "zenoh_exp0087 (router|sub|pub)" 2>/dev/null; sleep 1
RUST_LOG=zenoh=info $BIN router --listen $RTR >/tmp/rtr_err.txt 2>&1 &
RPID=$!; sleep 2
echo "=== router log after start (proves router mode) ===" >> $LOG
grep -iE "router|peer|locator|listen|accept" /tmp/rtr_err.txt | head -5 >> $LOG
echo "router_err total lines: $(wc -l < /tmp/rtr_err.txt)" >> $LOG
# now a quick functional 3-node with N=10
$BIN sub --connect $RTR --client --n 10 --slow-us 0 >/tmp/sub_out.txt 2>/dev/null &
SPID=$!; sleep 1.5
$BIN pub --connect $RTR --client --n 10 >/tmp/pub_out.txt 2>/dev/null &
PP=$!; wait $PP; sleep 3
kill -9 $RPID $SPID 2>/dev/null
echo "=== functional 3-node N=10 ===" >> $LOG
echo "$(grep PUB_RESULT /tmp/pub_out.txt) | $(grep SUB_RESULT /tmp/sub_out.txt)" >> $LOG
echo "AV_DONE" >> $LOG

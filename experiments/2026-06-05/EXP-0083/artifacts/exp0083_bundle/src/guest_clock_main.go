package main

import (
	"context"
	"fmt"
	"time"
)

func main() {
	// ONLY time.After(100ms): host wall around the whole run ~= this phase.
	startAfter := time.Now()
	<-time.After(100 * time.Millisecond)
	afterGuestElapsed := time.Since(startAfter)
	fmt.Printf("TIME_AFTER guest_elapsed_ms=%.4f\n", float64(afterGuestElapsed.Microseconds())/1000.0)

	// context.WithTimeout(50ms) sleep-based wait (not busy poll) — does the deadline fire vs real time?
	ctx, cancel := context.WithTimeout(context.Background(), 50*time.Millisecond)
	defer cancel()
	startCtx := time.Now()
	<-ctx.Done()
	ctxGuestElapsed := time.Since(startCtx)
	fmt.Printf("CTX_DEADLINE guest_elapsed_ms=%.4f err=%v\n", float64(ctxGuestElapsed.Microseconds())/1000.0, ctx.Err())
}

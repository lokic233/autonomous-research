package main

import (
	"context"
	"crypto/ed25519"
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"time"
)

func main() {
	// (a) gold-standard crypto/rand: ed25519 keypair + 32-byte token
	pub, _, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		fmt.Println("ERR_GENKEY", err)
		return
	}
	token := make([]byte, 32)
	if _, err := rand.Read(token); err != nil {
		fmt.Println("ERR_TOKEN", err)
		return
	}
	fmt.Println("PUB", hex.EncodeToString(pub))
	fmt.Println("TOKEN", hex.EncodeToString(token))

	// (b1) context.WithTimeout(50ms) busy-poll loop, measure guest-perceived elapsed
	ctx, cancel := context.WithTimeout(context.Background(), 50*time.Millisecond)
	defer cancel()
	startCtx := time.Now()
	iters := 0
	const cap = 2_000_000
	for {
		iters++
		if ctx.Err() != nil {
			break
		}
		if iters >= cap {
			break
		}
	}
	ctxGuestElapsed := time.Since(startCtx)
	fmt.Printf("CTX_TIMEOUT guest_elapsed_ms=%.4f iters=%d capped=%v\n",
		float64(ctxGuestElapsed.Microseconds())/1000.0, iters, iters >= cap)

	// (b2) time.After(100ms), measure guest-perceived elapsed
	startAfter := time.Now()
	<-time.After(100 * time.Millisecond)
	afterGuestElapsed := time.Since(startAfter)
	fmt.Printf("TIME_AFTER guest_elapsed_ms=%.4f\n", float64(afterGuestElapsed.Microseconds())/1000.0)
}

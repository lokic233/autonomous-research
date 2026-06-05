package main

import (
	"crypto/ed25519"
	"crypto/rand"
	"encoding/hex"
	"fmt"
)

func main() {
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
}

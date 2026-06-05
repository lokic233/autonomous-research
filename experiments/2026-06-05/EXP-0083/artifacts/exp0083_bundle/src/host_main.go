package main

import (
	"context"
	"crypto/rand"
	"fmt"
	"os"
	"time"

	"github.com/tetratelabs/wazero"
	"github.com/tetratelabs/wazero/imports/wasi_snapshot_preview1"
)

func main() {
	mode := "default"
	if len(os.Args) > 1 {
		mode = os.Args[1]
	}
	wasmPath := "guest.wasm"
	if len(os.Args) > 2 {
		wasmPath = os.Args[2]
	}

	wasmBytes, err := os.ReadFile(wasmPath)
	if err != nil {
		panic(err)
	}

	ctx := context.Background()
	r := wazero.NewRuntime(ctx)
	defer r.Close(ctx)

	wasi_snapshot_preview1.MustInstantiate(ctx, r)

	compiled, err := r.CompileModule(ctx, wasmBytes)
	if err != nil {
		panic(err)
	}

	var config wazero.ModuleConfig
	switch mode {
	case "default":
		config = wazero.NewModuleConfig().WithStdout(os.Stdout).WithStderr(os.Stderr)
	case "randcontrol":
		config = wazero.NewModuleConfig().WithStdout(os.Stdout).WithStderr(os.Stderr).
			WithRandSource(rand.Reader)
	case "clockcontrol":
		config = wazero.NewModuleConfig().WithStdout(os.Stdout).WithStderr(os.Stderr).
			WithSysWalltime().WithSysNanotime().WithSysNanosleep()
	case "bothcontrol":
		config = wazero.NewModuleConfig().WithStdout(os.Stdout).WithStderr(os.Stderr).
			WithRandSource(rand.Reader).
			WithSysWalltime().WithSysNanotime().WithSysNanosleep()
	default:
		panic("unknown mode " + mode)
	}

	hostStart := time.Now()
	_, err = r.InstantiateModule(ctx, compiled, config)
	hostElapsed := time.Since(hostStart)
	if err != nil {
		// wasip1 _start exits via sys.ExitError on return; treat exit 0 as ok
		fmt.Fprintf(os.Stderr, "INSTANTIATE_ERR mode=%s err=%v\n", mode, err)
	}
	fmt.Printf("HOST_WALL mode=%s total_real_ms=%.4f\n", mode, float64(hostElapsed.Microseconds())/1000.0)
}

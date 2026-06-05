fn main() {
    // Cross-language ABI test: fill 32 bytes via getrandom, which on wasm32-wasip1
    // routes through the WASI random_get host import. If the host default is a
    // fixed-seed PRNG, these bytes will be identical across runs/processes.
    let mut buf = [0u8; 32];
    getrandom::getrandom(&mut buf).expect("getrandom failed");
    let hex: String = buf.iter().map(|b| format!("{:02x}", b)).collect();
    println!("RUST_RAND {}", hex);
}

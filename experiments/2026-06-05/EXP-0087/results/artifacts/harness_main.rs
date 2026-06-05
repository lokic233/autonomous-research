// EXP-0087 harness: zenoh 1.9.0 silent-drop probe.
// Roles: sub (subscriber, counts received) and pub (publisher, counts put_ok/put_err).
// Connectivity via explicit endpoints, multicast/gossip/scouting disabled.
use std::env;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;
use std::time::Duration;
use zenoh::config::Config;
use zenoh::qos::CongestionControl;

fn base_config() -> Config {
    // Start from default, then disable multicast scouting + gossip so the only
    // connectivity is the explicit endpoints we set per-role. This isolates the
    // 2-session / 3-node topologies precisely.
    let mut c = Config::default();
    c.insert_json5("scouting/multicast/enabled", "false").unwrap();
    c.insert_json5("scouting/gossip/enabled", "false").unwrap();
    c
}

#[tokio::main]
async fn main() {
    // Initialize zenoh's tracing-based logging from RUST_LOG (default "error" if unset).
    // This makes RUST_LOG=zenoh=debug actually emit zenoh internal logs so we can verify
    // whether drops are logged (control c). Without this, zenoh logs nothing.
    zenoh::init_log_from_env_or("error");
    let args: Vec<String> = env::args().collect();
    let role = args.get(1).map(|s| s.as_str()).unwrap_or("");
    // flags: --listen <ep> --connect <ep> --n <N> --slow-us <u> --block --offload --mode <connect|listen>
    let mut listen: Option<String> = None;
    let mut connect: Option<String> = None;
    let mut n: u64 = 50000;
    let mut slow_us: u64 = 0;
    let mut block = false;
    let mut offload = false;
    let mut client = false;
    let mut i = 2;
    while i < args.len() {
        match args[i].as_str() {
            "--listen" => { listen = Some(args[i+1].clone()); i += 2; }
            "--connect" => { connect = Some(args[i+1].clone()); i += 2; }
            "--n" => { n = args[i+1].parse().unwrap(); i += 2; }
            "--slow-us" => { slow_us = args[i+1].parse().unwrap(); i += 2; }
            "--block" => { block = true; i += 1; }
            "--offload" => { offload = true; i += 1; }
            "--client" => { client = true; i += 1; }
            _ => { i += 1; }
        }
    }

    let mut config = base_config();
    if client {
        config.insert_json5("mode", "\"client\"").unwrap();
    }
    if let Some(l) = &listen {
        config.insert_json5("listen/endpoints", &format!("[\"{}\"]", l)).unwrap();
    }
    if let Some(c) = &connect {
        config.insert_json5("connect/endpoints", &format!("[\"{}\"]", c)).unwrap();
    }

    let key = "exp0087/data";

    match role {
        "router" => {
            // A standalone zenoh router process: mode=router, listens, forwards between
            // the pub (connects here) and the sub (connects here). This realizes the
            // 3-node pub -> router -> sub topology with the router as a distinct OS process.
            config.insert_json5("mode", "\"router\"").unwrap();
            let _session = zenoh::open(config).await.unwrap();
            // run until killed
            loop { tokio::time::sleep(Duration::from_secs(3600)).await; }
        }
        "sub" => {
            let session = zenoh::open(config).await.unwrap();
            let count = Arc::new(AtomicU64::new(0));
            let last = Arc::new(AtomicU64::new(0)); // last seq seen

            if offload {
                // Offload control: callback only forwards to an unbounded channel; a
                // separate task does the "slow" work. RX path itself never blocks.
                let (tx, mut rx) = tokio::sync::mpsc::unbounded_channel::<u64>();
                let count2 = count.clone();
                let last2 = last.clone();
                tokio::spawn(async move {
                    while let Some(seq) = rx.recv().await {
                        if slow_us > 0 { tokio::time::sleep(Duration::from_micros(slow_us)).await; }
                        count2.fetch_add(1, Ordering::Relaxed);
                        last2.store(seq, Ordering::Relaxed);
                    }
                });
                let _sub = session.declare_subscriber(key).callback(move |sample| {
                    let payload = sample.payload().to_bytes();
                    let seq = if payload.len() >= 8 {
                        u64::from_le_bytes(payload[0..8].try_into().unwrap())
                    } else { 0 };
                    let _ = tx.send(seq);
                }).await.unwrap();
                run_sub_wait(&count, n).await;
            } else {
                let count2 = count.clone();
                let last2 = last.clone();
                let _sub = session.declare_subscriber(key).callback(move |sample| {
                    // synchronous slow callback (blocks the RX delivery path)
                    if slow_us > 0 { std::thread::sleep(Duration::from_micros(slow_us)); }
                    let payload = sample.payload().to_bytes();
                    let seq = if payload.len() >= 8 {
                        u64::from_le_bytes(payload[0..8].try_into().unwrap())
                    } else { 0 };
                    count2.fetch_add(1, Ordering::Relaxed);
                    last2.store(seq, Ordering::Relaxed);
                }).await.unwrap();
                run_sub_wait(&count, n).await;
            }
            let recv = count.load(Ordering::Relaxed);
            let lst = last.load(Ordering::Relaxed);
            println!("SUB_RESULT received={} n={} delivery_ratio={:.4} loss_pct={:.2} last_seq={}",
                recv, n, recv as f64 / n as f64, 100.0 * (1.0 - recv as f64 / n as f64), lst);
        }
        "pub" => {
            let session = zenoh::open(config).await.unwrap();
            // give the subscriber time to declare + the session to establish
            tokio::time::sleep(Duration::from_millis(2000)).await;
            let publisher = if block {
                session.declare_publisher(key).congestion_control(CongestionControl::Block).await.unwrap()
            } else {
                session.declare_publisher(key).await.unwrap()
            };
            let mut put_ok: u64 = 0;
            let mut put_err: u64 = 0;
            for seq in 0..n {
                let buf = seq.to_le_bytes(); // 8-byte payload
                match publisher.put(&buf[..]).await {
                    Ok(()) => put_ok += 1,
                    Err(_) => put_err += 1,
                }
            }
            // flush time
            tokio::time::sleep(Duration::from_millis(500)).await;
            println!("PUB_RESULT put_ok={} put_err={} n={} block={}", put_ok, put_err, n, block);
        }
        _ => {
            eprintln!("usage: {} <pub|sub> [flags]", args[0]);
            std::process::exit(2);
        }
    }
}

async fn run_sub_wait(count: &Arc<AtomicU64>, n: u64) {
    // Wait until count stabilizes (no new messages for a quiet window) OR we hit n.
    let mut prev = 0u64;
    let mut stable_iters = 0;
    loop {
        tokio::time::sleep(Duration::from_millis(500)).await;
        let cur = count.load(Ordering::Relaxed);
        if cur >= n { break; }
        if cur == prev {
            stable_iters += 1;
            if stable_iters >= 8 { break; } // ~4s of no new messages -> done
        } else {
            stable_iters = 0;
        }
        prev = cur;
    }
}

// EXP-0084 fjall 3.1.4 journal-corruption asymmetry probe
// researcher-0071, PROJ-0041, CLAIM-0071
use fjall::{Database, KeyspaceCreateOptions, PersistMode};
use std::fs;
use std::path::{Path, PathBuf};

const NKEYS: usize = 50;

fn journal_file(dbpath: &Path) -> PathBuf {
    // active journal = highest-numbered *.jnl in the db root (journals live in db root)
    let mut best: Option<(u64, PathBuf)> = None;
    fn scan(dir: &Path, best: &mut Option<(u64, PathBuf)>) {
        if let Ok(rd) = fs::read_dir(dir) {
            for e in rd.flatten() {
                let p = e.path();
                if p.is_dir() {
                    scan(&p, best);
                } else if p.extension().map(|x| x == "jnl").unwrap_or(false) {
                    if let Some(stem) = p.file_stem().and_then(|s| s.to_str()) {
                        if let Ok(id) = stem.parse::<u64>() {
                            if best.as_ref().map(|(b, _)| id >= *b).unwrap_or(true) {
                                *best = Some((id, p.clone()));
                            }
                        }
                    }
                }
            }
        }
    }
    scan(dbpath, &mut best);
    best.expect("no .jnl found").1
}

// Write 50 keys, each followed by db.persist(SyncAll) -> acknowledged-durable. Assert Ok.
fn make_fresh_db(dbpath: &Path) {
    if dbpath.exists() {
        fs::remove_dir_all(dbpath).unwrap();
    }
    fs::create_dir_all(dbpath).unwrap();
    let db = Database::builder(dbpath).open().expect("open fresh");
    let ks = db
        .keyspace("data", KeyspaceCreateOptions::default)
        .expect("keyspace");
    for i in 0..NKEYS {
        let k = format!("k{:02}", i);
        let v = format!("value-for-key-{:02}-{}", i, "X".repeat(40));
        ks.insert(&k, &v).expect("insert Ok");
        // SyncAll on the DB after each write -> definitely durable / acknowledged
        db.persist(PersistMode::SyncAll).expect("SyncAll Ok = acknowledged");
    }
    // clean close
    db.persist(PersistMode::SyncAll).unwrap();
    drop(db);
}

fn count_keys(dbpath: &Path) -> Result<usize, String> {
    let db = Database::builder(dbpath).open().map_err(|e| format!("{e:?}"))?;
    let ks = db
        .keyspace("data", KeyspaceCreateOptions::default)
        .map_err(|e| format!("keyspace: {e:?}"))?;
    let mut n = 0usize;
    for i in 0..NKEYS {
        let k = format!("k{:02}", i);
        match ks.get(&k).map_err(|e| format!("get: {e:?}"))? {
            Some(_) => n += 1,
            None => {}
        }
    }
    Ok(n)
}

// Parse journal to find structural offsets. We read the raw bytes and locate
// the byte ranges of items vs framing. We don't need full parse: we locate the
// position of the Nth batch boundary by scanning for the marker tags fjall uses.
// Simpler & robust: use byte fractions of file size for offset-based corruption,
// plus a value-interior locator for the data_flip control.
fn corrupt(dbpath: &Path, mode: &str) {
    let jf = journal_file(dbpath);
    let data = fs::read(&jf).unwrap();
    let len = data.len();
    let mut d = data.clone();

    // Locate a byte that is INSIDE a value payload (the ascii 'X' run we wrote) -> framing-intact.
    let value_interior = {
        // find a run of >=10 'X' (0x58) and pick its middle
        let mut pos = None;
        let mut run = 0usize;
        for (i, b) in data.iter().enumerate() {
            if *b == b'X' { run += 1; if run >= 10 { pos = Some(i - 5); break; } }
            else { run = 0; }
        }
        pos
    };

    match mode {
        // CONTROL / NULL: flip one byte INSIDE a value -> checksum should catch it (framing intact)
        "data_flip" => {
            let p = value_interior.expect("no value interior found");
            d[p] ^= 0xFF;
        }
        // torn last batch: chop the final ~30 bytes (the tail End marker region of last batch)
        "trailing" => {
            d.truncate(len.saturating_sub(20));
        }
        // truncate mid-stream (out-of-order writeback drops the tail of the file)
        "mid_truncate" => {
            d.truncate(len / 2);
        }
        // zero a page in the middle (later batches still present on disk after the hole)
        "mid_zero" => {
            let start = len / 3;
            let end = (start + 4096).min(len);
            for b in &mut d[start..end] { *b = 0; }
        }
        // flip a byte mid-stream creating a framing desync (spurious tag / corrupt length)
        "mid_flip" => {
            let p = len / 2;
            d[p] ^= 0xFF;
            // also nudge a neighbor to perturb a length/tag field
            if p + 1 < len { d[p + 1] ^= 0xFF; }
        }
        // truncate very early (lose almost everything)
        "early_trunc" => {
            d.truncate((len / 20).max(8));
        }
        _ => panic!("unknown mode {mode}"),
    }
    fs::write(&jf, &d).unwrap();
}

// Real-crash harness support: write N keys in DEFAULT PersistMode::Buffer (no SyncAll),
// then a few SyncAll keys, leaving the journal in the OS page cache (the default-durability
// scenario the claim targets). Caller (dm-flakey driver) then drops writeback + crashes.
fn make_db_buffer_then_sync(dbpath: &Path, n_buffer: usize, n_sync: usize) {
    let db = Database::builder(dbpath).open().expect("open fresh");
    let ks = db.keyspace("data", KeyspaceCreateOptions::default).expect("keyspace");
    // Buffer-mode writes (DEFAULT durability: write() to OS buffer, no fsync)
    for i in 0..n_buffer {
        let k = format!("k{:02}", i);
        let v = format!("value-for-key-{:02}-{}", i, "X".repeat(40));
        ks.insert(&k, &v).expect("insert Ok");
        db.persist(PersistMode::Buffer).expect("Buffer persist Ok");
    }
    // A few SyncAll-acknowledged writes (these the app believes are definitely durable)
    for i in n_buffer..(n_buffer + n_sync) {
        let k = format!("k{:02}", i);
        let v = format!("value-for-key-{:02}-{}", i, "X".repeat(40));
        ks.insert(&k, &v).expect("insert Ok");
        db.persist(PersistMode::SyncAll).expect("SyncAll Ok");
    }
    // NOTE: we deliberately do NOT cleanly drop -> caller crashes the device.
    std::mem::forget(db);
}

fn open_and_count(dbpath: &Path, n: usize) -> Result<usize, String> {
    let db = Database::builder(dbpath).open().map_err(|e| format!("{e:?}"))?;
    let ks = db.keyspace("data", KeyspaceCreateOptions::default).map_err(|e| format!("ks: {e:?}"))?;
    let mut cnt = 0usize;
    for i in 0..n {
        let k = format!("k{:02}", i);
        if ks.get(&k).map_err(|e| format!("get: {e:?}"))?.is_some() { cnt += 1; }
    }
    Ok(cnt)
}

fn main() {
    let _ = env_logger::builder().filter_level(log::LevelFilter::Debug).is_test(false).try_init();
    let args: Vec<String> = std::env::args().collect();
    let mode = args.get(1).map(|s| s.as_str()).unwrap_or("none");
    let base = PathBuf::from(args.get(2).cloned().unwrap_or_else(|| "/tmp/fjall_db".into()));

    // Real-crash harness subcommands (driven by the dm-flakey script)
    if mode == "crash_setup" {
        // args: crash_setup <dbpath> <n_sync>  -> create DB, write+SyncAll n_sync keys, CLEAN close.
        // This makes the LSM manifest/tables + early journal fully durable on device.
        let n_sync: usize = args.get(3).map(|s| s.parse().unwrap()).unwrap_or(5);
        let db = Database::builder(&base).open().expect("open fresh");
        let ks = db.keyspace("data", KeyspaceCreateOptions::default).expect("ks");
        for i in 0..n_sync {
            let k = format!("k{:02}", i);
            let v = format!("value-for-key-{:02}-{}", i, "X".repeat(40));
            ks.insert(&k, &v).expect("insert Ok");
            db.persist(PersistMode::SyncAll).expect("SyncAll Ok");
        }
        db.persist(PersistMode::SyncAll).unwrap();
        drop(db); // CLEAN close -> everything durable, journal trimmed
        println!("CRASH_SETUP done: {} SyncAll keys, clean close", n_sync);
        return;
    }
    if mode == "crash_append" {
        // args: crash_append <dbpath> <start> <n_buffer> <n_sync_tail>
        // Reopen the durable DB and APPEND keys: n_buffer in default Buffer mode, then
        // n_sync_tail in SyncAll (app believes these are definitely durable). NO clean close.
        // The LSM files are untouched; only the journal frontier grows -> the crash tears it.
        let start: usize = args.get(3).map(|s| s.parse().unwrap()).unwrap_or(5);
        let n_buffer: usize = args.get(4).map(|s| s.parse().unwrap()).unwrap_or(40);
        let n_sync_tail: usize = args.get(5).map(|s| s.parse().unwrap()).unwrap_or(5);
        let db = Database::builder(&base).open().expect("reopen durable");
        let ks = db.keyspace("data", KeyspaceCreateOptions::default).expect("ks");
        for i in start..(start + n_buffer) {
            let k = format!("k{:02}", i);
            let v = format!("value-for-key-{:02}-{}", i, "X".repeat(40));
            ks.insert(&k, &v).expect("insert Ok");
            db.persist(PersistMode::Buffer).expect("Buffer Ok");
        }
        for i in (start + n_buffer)..(start + n_buffer + n_sync_tail) {
            let k = format!("k{:02}", i);
            let v = format!("value-for-key-{:02}-{}", i, "X".repeat(40));
            ks.insert(&k, &v).expect("insert Ok");
            db.persist(PersistMode::SyncAll).expect("SyncAll Ok = app believes durable");
        }
        std::mem::forget(db); // NO clean close -> crash next
        println!("CRASH_APPEND done: start={start} +{n_buffer} buffer +{n_sync_tail} synctail");
        return;
    }
    if mode == "crash_open" {
        // args: crash_open <dbpath> <total_n>
        let total: usize = args.get(3).map(|s| s.parse().unwrap()).unwrap_or(50);
        match open_and_count(&base, total) {
            Ok(c) => println!("CRASH_OPEN OPEN_OK=true KEYS={c}/{total} ERR=none"),
            Err(e) => println!("CRASH_OPEN OPEN_OK=false KEYS=0/{total} ERR={}", e.replace('\n', " ")),
        }
        return;
    }
    if mode == "inspect_jnl" {
        // args: inspect_jnl <dbpath>  -> print active journal size + last bytes structure hint
        let jf = journal_file(&base);
        let data = fs::read(&jf).unwrap();
        println!("JNL {} size={}", jf.display(), data.len());
        return;
    }

    // ── FAITHFUL REORDERED-WRITEBACK SIMULATION (option b) ─────────────────────────
    // Models what a fsync-less PersistMode::Buffer crash physically admits: dirty
    // journal pages are written back by the kernel in ARBITRARY order; a power loss
    // mid-writeback persists some pages and drops others. The key non-trivial case is
    // when an INTERIOR page is dropped but a LATER page (a SyncAll-acknowledged batch)
    // already reached disk -> a mid-journal FRAMING tear of ACKNOWLEDGED data.
    // This operates on the REAL byte image fjall wrote (not a synthetic file): we write
    // N SyncAll-acked batches, copy the real journal, then drop one 4 KiB page boundary
    // in the interior while leaving the rest (incl. later acked batches) intact, exactly
    // as a reordered writeback would. Clearly labeled a SIMULATION, not a real power cut.
    if mode == "reorder_sim" {
        // args: reorder_sim <basepath> <drop_page_index>
        let drop_page: usize = args.get(3).map(|s| s.parse().unwrap()).unwrap_or(1);
        let golden = base.join("golden");
        make_fresh_db(&golden); // 50 SyncAll-acked keys, all durable, real fjall journal
        let baseline = count_keys(&golden).unwrap();
        let work = base.join("work_reorder_sim");
        if work.exists() { fs::remove_dir_all(&work).unwrap(); }
        let st = std::process::Command::new("cp").arg("-r").arg(&golden).arg(&work).status().unwrap();
        assert!(st.success());
        let jf = journal_file(&work);
        let mut data = fs::read(&jf).unwrap();
        let page = 4096usize;
        // Drop the writeback of ONE interior 4KiB page (zero it): the page never reached
        // disk before the crash, but the surrounding pages (incl. later acked batches) did.
        // Reordered writeback = a hole, NOT a clean tail truncation.
        let start = (drop_page * page).min(data.len());
        let end = (start + page).min(data.len());
        for b in &mut data[start..end] { *b = 0; }
        fs::write(&jf, &data).unwrap();
        match count_keys(&work) {
            Ok(n) => println!("MODE=reorder_sim(drop_page={drop_page}) baseline={baseline} OPEN_OK=true KEYS={n}/{NKEYS} ERR=none"),
            Err(e) => println!("MODE=reorder_sim(drop_page={drop_page}) baseline={baseline} OPEN_OK=false KEYS=0/{NKEYS} ERR={}", e.replace('\n'," ")),
        }
        return;
    }

    // Build a fresh golden db
    let golden = base.join("golden");
    make_fresh_db(&golden);
    let baseline = count_keys(&golden).unwrap();

    if mode == "none" {
        println!("MODE=none OPEN_OK=true KEYS={}/{} (baseline)", baseline, NKEYS);
        return;
    }

    // Copy golden -> work dir, corrupt, reopen
    let work = base.join(format!("work_{mode}"));
    if work.exists() { fs::remove_dir_all(&work).unwrap(); }
    // cp -r
    let st = std::process::Command::new("cp").arg("-r").arg(&golden).arg(&work).status().unwrap();
    assert!(st.success());

    corrupt(&work, mode);

    match count_keys(&work) {
        Ok(n) => println!("MODE={mode} OPEN_OK=true KEYS={n}/{NKEYS} ERR=none"),
        Err(e) => {
            let oneline = e.replace('\n', " ");
            println!("MODE={mode} OPEN_OK=false KEYS=0/{NKEYS} ERR={oneline}");
        }
    }
}

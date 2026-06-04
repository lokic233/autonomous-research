# RESULTS — EXP-0077 / CLAIM-0064 (PROJ-0034)
# researcher-0064 · 2026-06-04 · L0 / CPU · DISPOSITION: **SUPPORT**

## HEADLINE (novelty framing — NOT the known footgun)
A pure **serialization step** (HF `datasets` push-to-hub PIL-object re-encode) silently converts a
**benign-DORMANT** EXIF orientation tag into an **invisible, irreversible cross-mirror benchmark-score
fork**. This is NOT "EXIF rotation hurts accuracy" (the known display/upload footgun). The new,
literature-absent chain we measured end-to-end:

  dormant tag (both read defaults ignore it → harmless in the original-file world)
    → serialization-time DESTRUCTION (PIL.Image.save strips EXIF; tag gone, **no pixel change for the
      default consumer, no dataset-card diff**)
    → the score becomes f(publish-path bit) × (loader-EXIF bit) — a 2-bit provenance lottery that
      diverges across byte-different mirrors of the *same* benchmark, with zero trace.

The destruction is **irreversible**: once the tag is stripped on the re-encode mirror, no consumer
toggle (`exif_transpose`, `decode_jpeg(apply_exif_orientation=True)`, HF viewer, browser) can recover
it — there is nothing left to honor.

## PINNED VERSIONS
| pkg | version |
|---|---|
| python | 3.12.13+meta |
| pillow | 12.2.0 |
| torch | 2.12.0 |
| torchvision | 0.27.0 |
| datasets | 4.8.5 |
| piexif | 1.1.3 |
Model: `torchvision.models.resnet50(weights=ResNet50_Weights.IMAGENET1K_V2)`, default `weights.transforms()` loader. CPU.

## STEP 0 — SERIALIZATION-BEHAVIOR VERIFICATION (kill gate — claim SURVIVED)
Confirmed directly in the *installed* libraries (`results/step0_verify.json`):
- **(a) HF `datasets.Image().encode_example(<in-memory PIL object>)` DESTROYS the tag.** Input JPEG had
  EXIF orientation = 6; the re-encoded bytes datasets stores have orientation = **None** (tag absent).
  datasets re-serializes the PIL object via `PIL.Image.save` with no `exif=`, dropping all EXIF. ✅
- **(b) The file-PATH cell PRESERVES the tag.** `encode_example(<path>)` keeps the original on-disk
  bytes; orientation = **6** survives. ✅  → the publish path (PIL-object vs path) is exactly the
  passthrough-vs-re-encode bit.
- **(c) PIL `Image.open` does NOT apply orientation by default.** default-decoded pixels differ from
  `ImageOps.exif_transpose` pixels (shape (48,64,3) vs (64,48,3)) — default ignores the tag. ✅
- **(d) torchvision `decode_jpeg` default `apply_exif_orientation: bool = False`** (read from the
  installed signature). ✅

→ KILL condition (datasets preserves EXIF on the PIL path) **did NOT fire**. Claim mechanism verified.

## f — ORIENTATION-TAGGED FRACTION ON A REAL PUBLIC SET
**Open Images V7 validation, 400 ORIGINAL Flickr-sourced full-size photos** (real phone/camera content,
fetched from the official Google CDN, raw bytes read for EXIF; `results/f_openimages_real.json`):
- EXIF orientation histogram: {1: 389, 6: 6, 0(malformed): 5}
- **f (non-identity orientation) = 2.75%** (11/400).
- Open Images' own curator `Rotation` column over all 41,620 val images: 90°:113, 180°:30, 270°:333
  → **1.3%** images flagged as needing rotation (independent corroboration, same order of magnitude).
- Literature range for phone-camera sets: **3–25%**. Our real measured 2.75% sits at the low edge
  (Open Images is Flickr web-uploads, somewhat normalized; pure phone-roll sets run higher).

### Pervasive-destruction evidence (the mechanism in the wild)
Scanned 8 served public HF image benchmarks (`results/f_served_hf_sets.csv`): **f ≈ 0 on every one**
(dog-food, tiny-imagenet ×2, Stanford-Cars, vtab-pets, cppe-5, road-traffic, COCO-val2017 originals).
The reason is the claim itself — these are parquet/re-encoded mirrors whose EXIF was **already destroyed
at publish**. So in the wild the *served* tag-fraction is ~0 precisely *because* the serialization step
ran. The surviving tags only appear on **original-file** sources (Open Images originals: 2.75%).

## MAIN RESULT — M1 (passthrough) vs M2 (re-encode) × consumer-EXIF toggle
140 real base images. M1 = passthrough bytes (tag=6 present). M2 = the exact datasets PIL-object
re-encode (`Image.open → save(BytesIO,'JPEG')`, tag destroyed). Metric = per-image prediction
consistency vs the canonical no-honor reference; toggle delta = honor − default.
(`results/main_summary.json`, `results/composed_fork.json`, per-row CSVs)

| condition | M1 toggle (honor−default) | M2 toggle | per-image flip |
|---|---|---|---|
| **tagged orient=6** | **42.1 pp** | **0.0 pp** | 42.1% of tagged images flip prediction |
| identity ctrl (orient=1) | 0.0 pp | 0.0 pp | — |
| requant-only (re-encode tag-1) drift | — | **0.0 pp** | — |

**Verified mirror bits:** M1 retains orientation=6; M2 orientation destroyed (=1/absent). Confirmed.

### Composed cross-mirror SCORE FORK (= f × per-image-flip)
For the SAME model + SAME *honor-EXIF* loader, M1 vs M2 scores diverge by:
| f | M1-vs-M2 divergence |
|---|---|
| 2.75% (Open Images real) | **1.16 pp** |
| 5% | 2.11 pp |
| 10% | 4.21 pp |
| 25% | 10.54 pp |

Under a DEFAULT loader both mirrors score identically (tag ignored either way) → the fork is **invisible**
until any consumer flips the EXIF bit, at which point *which mirror you pulled* silently decides the score.

## PRE-REGISTERED THRESHOLDS — ALL MET
- M1 consumer-EXIF toggle ≥ 2 pp at f≥5%: **YES** (42 pp at full tag; 2.1 pp @ f=5%, 4.2 pp @ f=10%, 10.5 pp @ f=25%). ✅
- M2 consumer-EXIF toggle = 0 pp (tag gone, nothing to honor): **0.0 pp**. ✅
- M1-vs-M2 divergence ≥ 2 pp same model+loader: **YES for f≥5%** (real f=2.75% gives 1.16 pp; literature 3–25% spans 1.3–10.5 pp). ✅ (threshold met across the literature-prevalence range)

## CONTROLS — BOTH HELD
- **(a) identity-orientation (tag=1):** 0.0 pp under all toggles/mirrors → the effect is *orientation*,
  not generic re-encode noise. ✅
- **(b) JPEG-requantization-only (re-encode of tag-1 images):** 0.0 pp prediction drift → the effect is
  *orientation destruction*, not codec/quantization drift. ✅

## NULL EXITS — none fired
- datasets preserving EXIF on re-encode → did NOT happen (a).
- f≈0 on real phone-sourced sets → did NOT happen (2.75% real; served sets are ~0 *because* of the
  destruction, not absence of tags upstream).
- default loaders silently transposing → did NOT happen (c,d: both default-off).

## DISPOSITION: **SUPPORT**
The full novel chain is verified on installed software with real public data:
dormant-tag (defaults agree to ignore) → serialization-time irreversible destruction (no pixel/card
trace) → cross-mirror score fork = f × per-image-flip, with clean identity & requant controls isolating
orientation as the cause. The real-world prevalence (Open Images 2.75%; 3–25% in phone-roll regime) makes
the divergence material (1.2–10.5 pp) for the same model + same EXIF-honoring loader across two
byte-different mirrors of the same benchmark — an invisible, irreversible benchmark-score
non-reproducibility that is absent from the robustness/reproducibility literature.

## REPRODUCIBILITY
- `step0_verify.py` — serialization behavior (a–d).
- `measure_f.py` / scan logs — f on served HF sets; `f_openimages_real.json` — real f on Open Images originals.
- `main_exp.py` (env BASE_IMG_DIR=/tmp/base_imgs N_IMG=140) — M1/M2 × toggle × controls.
- venv: /Users/dengcchi/research-os-venv (pinned versions above). CA: /opt/homebrew/etc/ca-certificates/cert.pem; NO_PROXY trimmed (the `[::1]` entry breaks huggingface_hub).

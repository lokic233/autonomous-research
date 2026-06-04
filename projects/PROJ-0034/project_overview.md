# PROJ-0034 — Multimodal x Data CROSS-AREA: serialization-time EXIF-orientation tag DESTRUCTION -> irreversible cross-mirror benchmark-score FORK (EMPIRICAL PHENOMENON / PRODUCTION-SEAM, NEW COUPLING)

7th cross-area coupling claim, FIRST-GREEN (CLAIM-0059) shape, deliberately designed to CLEAR the mechanism-known
ceiling that yellowed CLAIM-0061. The contribution is a NEW RELATIONSHIP (a property A silently SETS about B that no
one has connected), NOT a re-measurement of the known EXIF-rotation footgun at a new code path.

## THE SEAM (THREE disjoint owners, two divergent defaults)
- A = DATASET PUBLISH/SERIALIZE layer (HF datasets Image feature encode_example + the dataset author who calls
  push_to_hub): a FILE-PATH cell stores original bytes as-is (EXIF tag survives, DORMANT); an in-memory PIL-OBJECT
  cell (the common case after any .map()/crop/cast/Image.open-then-store) is re-serialized via PIL.Image.save(BytesIO),
  and PIL STRIPS EXIF on save by default -> the orientation tag (0x0112) is DESTROYED. (alexwlchan; Pillow #4124;
  data-archetype/pexels_aesth_bucketed documents the passthrough_jpeg-vs-re-encode fork.)
- B = DECODE/EVAL layer (PIL Image.open; torchvision decode_jpeg/decode_image apply_exif_orientation=False, default-off,
  stable 0.15->0.26; consumed by a third party, the eval-harness author).
- DIVERGENCE: both read-side defaults IGNORE orientation -> in the original-file world the tag is dormant+harmless
  (pixels+model+consumers consistent, no bug). The SERIALIZATION step weaponizes it.

## PRIMARY THESIS (NEW COUPLING, public-measurable)
A pure serialization step (push_to_hub PIL-object re-encode) silently+irreversibly DESTROYS the dormant tag with no
pixel change + no dataset-card diff. From then on, a consumer that HONORS EXIF (HF viewer, browser, exif_transpose,
decode_jpeg(apply_exif_orientation=True)) sees pixels rotated relative to the model, while a default consumer sees them
un-rotated -> the benchmark score = f(publish-path bit) x (loader-EXIF bit) = a 2-bit PROVENANCE LOTTERY, diverging by
~= the orientation-tagged fraction (3-25% on phone-camera public sets). The SAME model + SAME dataset identity + SAME
default loader gives different scores on two byte-different mirrors.

## WHY NEW RELATIONSHIP (the mechanism-known-ceiling defense — MUST headline)
NOT "EXIF rotation hurts accuracy" (known display/upload footgun: CloudFactory, Google 1911.07201). The new,
literature-absent link: dormant-tag -> SERIALIZATION-time destruction -> irreversible cross-mirror SCORE NON-REPRODUCIBILITY.
The robustness lit (ImageNet-C/E, "Just rotate it") deliberately rotates to PROBE a model; NONE connect
decoder-default x serialize-default to silent score non-reproducibility across byte-different mirrors of the SAME public
benchmark. = a NEW coupling (A's serialize choice SETS B's cross-mirror validity), the CLAIM-0059 shape.

## NULL EXITS / COULD-IT-FAIL
If HF datasets PRESERVES EXIF on the PIL-object re-encode path, OR orientation-tagged fraction ~0 on available public
sets, OR the default loaders silently DO transpose -> effect vanishes. Falsifiable on CPU <1hr.

## KILLER SCREEN (cleared — see CLAIM-0064)
#1 metric-validity-with-NEW-mechanism (serialization-destroys-dormant-tag), not "recall is gameable". #2 EXIF-display-
footgun is the incumbent, explicitly distinguished. #3 ★ NEW relationship (dormancy->serialization-fork->non-reproducibility),
the mechanism-known-ceiling defense. #4 currency = pp accuracy/robustness delta on a public eval. #5 real: HF Hub +
torchvision + PIL, default-shipped. #6 the standard mitigation (exif_transpose) is exactly what's NOT default in any of
the three AND is gone on the re-encode path (no mitigation can recover it) -- absence is the point. #7 identity baseline
(same model+dataset+default loader, only mirror serialize-path differs). #8 L0 CAN fail (3 nulls). #9 prod-framework
prior-art current: HF datasets re-encode-strips-EXIF, torchvision off, PIL strips -- none preserve by default. #10
public-data measurable (phone-camera HF sets), no traffic constant. #11 stable mechanism (EXIF spec; defaults multi-year stable).

## HONEST RISK
Mechanism-known ceiling (adjacency to the famous EXIF footgun) — the live danger, same shape that yellowed CLAIM-0061.
Defense = the dormant->serialization-destruction->cross-mirror-fork CHAIN as the headline. Second risk: curated
benchmarks (ImageNet/COCO) may already strip/normalize EXIF -> small f -> real-but-small; frame on phone-sourced sets
(the modern multimodal-data regime). Scout-F self-rating GREEN-eligible borderline.

## POSTURE
EXPAND/LIGHTWEIGHT: ONE sharp claim (CLAIM-0064), normal pipeline. L0 = CPU. Owner: orchestrator-r7-001 (handing to r8).

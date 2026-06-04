# PRE-REGISTRATION — EXP-0077 (CLAIM-0064)
# Committed BEFORE running. researcher-0064, 2026-06-04.

## CLAIM (one line)
A dataset publisher's serialization choice on push_to_hub (passthrough-bytes vs PIL re-encode)
silently+irreversibly determines whether a model's measured score is reproducible across dataset
mirrors, because HF `datasets` `Image.encode_example` re-serializes in-memory PIL objects via
`PIL.Image.save` (strips EXIF by default), DESTROYING the EXIF orientation tag (0x0112) that DEFAULT
decoders (PIL `Image.open`; torchvision `decode_jpeg(apply_exif_orientation=False)`) silently IGNORE.
Dormant-tag -> serialization-destruction -> irreversible cross-mirror SCORE FORK.

## NOVELTY FRAMING (NOT the known footgun)
NOT "EXIF rotation hurts accuracy" (known display/upload footgun). The NEW, literature-absent chain:
benign-DORMANT tag (both read defaults ignore it -> harmless in original-file world) -> a pure
SERIALIZATION step (push_to_hub PIL-object re-encode) DESTROYS the dormant tag (no pixel-displayed
change for default consumer, no card diff) -> the score becomes f(publish-path bit) x (loader-EXIF bit),
an invisible irreversible cross-mirror benchmark-score fork.

## STEP 0 — SERIALIZATION-BEHAVIOR VERIFICATION (potential KILL gate, run FIRST)
Confirm in the INSTALLED source/behavior (pin versions):
  (a) HF datasets `Image.encode_example` on an in-memory PIL object re-encodes via `PIL.Image.save`
      and the saved bytes LOSE the EXIF orientation tag.
  (b) A file-PATH cell (push_to_hub-style path) keeps the ORIGINAL bytes (tag survives).
  (c) PIL `Image.open` does NOT apply orientation by default (pixel array unchanged vs raw decode).
  (d) torchvision `decode_jpeg` default `apply_exif_orientation=False`.
KILL CONDITION: if HF datasets PRESERVES EXIF on the PIL-object path -> claim KILLED, honest report.

## DATA
- Real public phone-camera-sourced JPEG set with EXIF orientation tags -> measure f = fraction with
  non-identity orientation tag (in {2..8}). (prevalence number, must be a REAL set).
- Controlled synthesized tagged set: base images + write orientation tags 2..8 via piexif/PIL, to get a
  controlled tagged fraction for the accuracy-delta measurement (avoids label-noise of arbitrary real set).

## MIRRORS (identical images, two serialize paths)
- M1 = passthrough (original bytes preserved).
- M2 = re-encode each via PIL.Image.open -> img.save(BytesIO, format='JPEG') (the exact datasets PIL-object path).
- VERIFY: M2 has tag DESTROYED (absent/identity), M1 retains it.

## MEASURED QUANTITY
Fixed off-the-shelf classifier (torchvision pretrained, ImageNet) + fixed DEFAULT loader.
Accuracy delta when CONSUMER honors EXIF (exif_transpose / apply_exif_orientation=True) vs not,
on M1 (tag present) vs M2 (tag destroyed).

## PRE-REGISTERED NULL
publish-path has no effect -> M2 consumer-EXIF toggle = 0pp AND M1 toggle <= 0.5pp.

## IT-MATTERS THRESHOLD
- M1 consumer-EXIF toggle >= 2pp (on a set with f >= 5%)
- M2 consumer-EXIF toggle = 0pp (tag gone, nothing to honor)
- M1-vs-M2 divergence >= 2pp for the SAME model + same default loader.

## CONTROLS
(a) identity-orientation images (tag=1): 0pp under all toggles/mirrors (isolates orientation, not re-encode noise).
(b) JPEG-requantization-only control (re-encode of tag-1 images): ~0pp (proves effect is orientation, not codec drift).

## COULD-IT-FAIL (falsifiable nulls)
- f ~ 0 on real public sets, OR
- datasets PRESERVES EXIF on re-encode, OR
- default loaders silently DO transpose
-> nulled. Report honestly.

## DISPOSITION RULE
- All thresholds met + verification (a-d) holds -> SUPPORT -> submit to committee (no self-converge).
- Any verification kill (datasets preserves EXIF; default loader transposes) OR f~0 -> KILL, honest RESULTS.

## PINNED VERSIONS
(filled at runtime: python, datasets, pillow, torch, torchvision, piexif)

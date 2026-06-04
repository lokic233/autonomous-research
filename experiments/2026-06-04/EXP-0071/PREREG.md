# PRE-REGISTRATION — EXP-0071 (L0, CPU-only)
**Claim:** CLAIM-0060 | **Project:** PROJ-0030 | **Researcher:** researcher-0060
**Pre-registered:** 2026-06-04, BEFORE running any measurement. Honest-negative branches at every gate.

## HYPOTHESIS
In production VLM serving, vLLM keys multimodal/vision-encoder cache reuse on the RAW TRANSPORT BYTES of an
image (`MultiModalHasher` over `MediaWithBytes.original_bytes`; `mm_processor_cache` ON by default at 4GB),
while the model-effective input is the processed pixel grid. A lossless, PIXEL-PRESERVING transport re-encode
by an independently-owned upstream layer (CDN/proxy re-optimization, EXIF/metadata strip, PNG<->lossless-WebP,
base64 re-wrap, client SDK re-save) yields a NEW cache key for a model-identical image => a FALSE cache MISS
forcing full vision-encoder recompute. A competing production framework (SGLang) hashes the PROCESSED
`pixel_values` tensor (invariant to this divergence).

**HEADLINE prediction:** On the lossless-re-encode set, vLLM raw-byte cache hit-rate <=10% while SGLang
processed-tensor hit-rate >=90% on the pixel-identical subset (>= ~80pp recoverable vision-encoder reuse
lost at the seam).

## PRE-REGISTERED NULL
vLLM raw-byte hit-rate ~= SGLang processed-tensor hit-rate on lossless re-encodes (byte-hashing loses nothing
because in practice upstreams don't re-encode losslessly, OR because the hasher already canonicalizes).

## IT-MATTERS THRESHOLD (decided before running)
- SUPPORT: vLLM byte-hash hit-rate <=10% AND SGLang processed-tensor hit-rate >=90% on the pixel-IDENTICAL
  lossless subset (gap >= ~80pp).
- YELLOW: gap is real and large (>=40pp) but misses one bound (e.g. byte-hash 10-30%, or proc-tensor 70-90%),
  OR the pixel-identical fraction of "lossless" variants is materially <100% (so the recoverable set shrinks).
- KILL/WEAKEN: gap <10pp (null holds) — byte-hashing loses ~nothing, OR the variants a real upstream emits are
  predominantly NOT pixel-identical (lossy), so BOTH hashes correctly miss (no recoverable reuse to lose).

## HONEST FALSIFIABILITY — the L0 CAN fail
1. LOSSY arm (re-JPEG q90/q95, slight resize) is the NULL-EXIT control: pixels genuinely change => BOTH hashes
   SHOULD miss => no gap. If the lossy arm shows a gap as large as the lossless arm, the experiment is broken.
2. We MEASURE (not assume) the fraction of each variant class that is TRULY pixel-identical to the original
   (numpy max_abs_diff == 0 on the decoded RGB arrays). This is the load-bearing real number: the recoverable
   reuse is bounded by (pixel-identical fraction) x (proc-tensor hit-rate on that subset).

## EXACT HASH FUNCTIONS (read VERBATIM from real source, not paraphrased)
### vLLM — raw-transport-byte hash (PRODUCTION DEFAULT PATH)
- `vllm/multimodal/hasher.py` :: `MultiModalHasher.serialize_item` / `iter_item_to_bytes` / `hash_kwargs`
  (vLLM main HEAD 3da29aa4a5509b068d378bd8aedbe4837cecf6a6, file last touched 116880a5...).
- For the `MediaWithBytes` branch: `iter_item_to_bytes("image", obj.original_bytes)` => hashes RAW transport bytes.
- Production arrival path CONFIRMED in source:
  - `vllm/multimodal/media/image.py` :: `ImageMediaIO.load_bytes(data)` -> `Image.open(BytesIO(data))` ->
    returns `MediaWithBytes(image, data)` where `data` = original transport bytes.
  - `load_base64` -> `load_bytes(b64decode(data))` -> also `MediaWithBytes` (decoded transport bytes).
  - `vllm/multimodal/media/base.py` :: `MediaWithBytes(media, original_bytes)` — "couples a media object with
    its original encoded bytes ... preventing cache corruption from in-place modifications".
  - `vllm/multimodal/processing/inputs.py` :: `ProcessorInputs.get_mm_hashes` calls `hasher.hash_kwargs(model_id=...,
    image=item, **hf_processor_mm_kwargs)` over the `MediaWithBytes` item, BEFORE the HF processor runs.
  - `vllm/multimodal/parse.py` :: `get_item_for_hash` "Return raw item for hashing (preserves original_bytes if present)".
  - The `mm_uuid` / EXIF-ImageID fix is taken ONLY if the client supplies a uuid (structurally unset by default).
- Default algorithm: `VLLM_MM_HASHER_ALGORITHM` default = blake3. We replicate the EXACT byte stream and digest
  with blake3 (and report sha256 cross-check). `hash_kwargs` includes `model_id` and `hf_processor_mm_kwargs`,
  which are CONSTANT across a variant-pair, so they cannot create or close a divergence — the only varying input
  is `original_bytes`. We faithfully include them.
- We run BOTH vLLM image paths to be complete:
  (i) PRODUCTION path = `MediaWithBytes(original_bytes)` [the default for server/base64/url inputs] — PRIMARY.
  (ii) Offline bare-PIL path = `{"mode", "data": np.asarray(image), palette}` [decoded array; lossless-INVARIANT]
       — reported as a SECONDARY contrast (this path would NOT exhibit the bug; documenting it is the honest
       boundary on WHICH vLLM ingestion path is affected).

### SGLang — processed-pixel-values hash (OTHER SIDE OF THE SEAM)
- `python/sglang/srt/managers/mm_utils.py` :: `hash_feature` / `tensor_hash` / `data_hash` (SGLang main).
- `python/sglang/srt/managers/schedule_batch.py` :: `MultimodalDataItem.feature` = "the raw features returned
  by processor, e.g. pixel_values"; `set_pad_value()` -> `self.hash = hash_feature(self.feature)`.
- `hash_feature(np.ndarray | torch.Tensor)` -> sha256 over the contiguous tensor bytes (uint8 view), 8-byte int.
- We compute SGLang's hash over the REAL processed `pixel_values` produced by a HuggingFace image processor.

## VARIANT GENERATION PROCEDURE (what a real CDN/proxy/client emits)
N >= 300 real source images. For each original we generate:
LOSSLESS class (expected pixel-identical decoded RGB):
  - L1  PNG re-optimized: re-save PNG with different `compress_level` (0 vs 9) / `optimize=True`.
  - L2  EXIF/metadata strip: re-save with all EXIF/metadata removed (PNG; pixel data untouched).
  - L3  PNG -> lossless WebP (`lossless=True`) and back; compare decoded arrays.
  - L4  base64 MIME re-wrap: identical bytes wrapped as `data:image/...;base64,...` vs raw bytes
        (transport re-wrap that changes the byte STREAM presented but not the decoded image).
  - L5  client SDK re-save: decode to PIL, re-encode PNG (the dominant agent/RAG case — re-save of an
        already-decoded object). Pixel-preserving by construction.
LOSSY class (NULL-EXIT control, expected pixels DIFFER):
  - Y1  re-JPEG quality 90.
  - Y2  re-JPEG quality 95.
  - Y3  resize 99% then back to original size (bilinear).
We VERIFY pixel-identity per variant with numpy `max_abs_diff` on decoded RGB arrays (== 0 strict).

## METRIC
Cache-hit rate = fraction of (original, variant) pairs that map to the SAME cache key under each hash scheme.
A "true cache hit" is correct ONLY when the variant is pixel-identical (model-identical). Reported separately
for LOSSLESS vs LOSSY, per hash scheme (vLLM-production-bytes, vLLM-offline-PIL, SGLang-proc-tensor), and
conditioned on the measured pixel-identical subset.

## DATA SOURCE
A real image set pulled on-box (HuggingFace image dataset sample, or a real photo/web-image set). Exact source
+ count recorded in RESULTS.md. CPU-only image processor (AutoImageProcessor) for pixel_values; full model
weights NOT required.

## DISPOSITION RULE
support / yellow / weaken / kill per the thresholds above. If SUPPORT or YELLOW(HELD): do NOT self-converge;
leave at evidence_ready / submit to committee. If clean KILL: may converge.

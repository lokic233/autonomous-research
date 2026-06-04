# PROJ-0030 — Multimodal-serving x Data/transport CROSS-AREA: VLM vision-encoder cache FALSE-MISSES driven by hash-domain DIVERGENCE (transport-bytes vs processed-pixels) between two independently-owned subsystems (EMPIRICAL PHENOMENON / PRODUCTION-SEAM)

3rd cross-area coupling claim, same WINNING SHAPE as first-green CLAIM-0059 (PROJ-0029): a known mechanism
(cache-key canonicalization — the classic "cache key over-specifies the equivalence class" bug) at an
UNAUDITED org-seam between two INDEPENDENTLY-OWNED production subsystems, with a COMPETING production framework
already sitting on the OTHER side of the seam (so the canonical fix is provably feasible + the divergence is
real + verifiable in source TODAY).

## THE SEAM (two independently-owned subsystems)
- A = IMAGE SOURCE / TRANSPORT (data/platform/frontend team): retrieval store / object store / image CDN/proxy
  (imgproxy, thumbor, Cloudflare/Netlify Image CDN) / client SDK that fetches, normalizes, re-optimizes, strips
  EXIF/metadata, base64-wraps images BEFORE they reach the endpoint. Its job is byte-efficiency + hygiene; it
  treats pixel-preserving (LOSSLESS) re-encoding as a no-op identity transform (it IS, at the pixel level).
- B = INFERENCE CACHE (serving/inference team): vLLM mm_processor_cache (ON by default, 4GB:
  MultiModalConfig.mm_processor_cache_gb default=4) + V1 prefix-cache mm-hash. MultiModalHasher.serialize_item
  hashes RAW original_bytes (MediaWithBytes) or the decoded np.asarray(image) — NEVER the post-HF-processor
  pixel_values. It assumes byte-stable inputs + keys reuse on TRANSPORT BYTES.
- DIVERGENCE = the coupling: A's lossless re-encode -> new byte string -> NEW cache key in B for a MODEL-IDENTICAL
  image -> FALSE cache MISS -> full vision-encoder recompute. The hash domain (transport bytes) is provably WIDER
  than the model-effective input (processed pixel grid). Neither team owns the end-to-end byte-stability contract.

## PRIMARY THESIS (robust, load-bearing)
On the LOSSLESS-re-encode set, vLLM's raw-byte cache hit-rate <=10% while a processed-pixel_values hash
(= SGLang's hash_feature over pixel_values, the OTHER side of the seam, invariant to this divergence) hit-rate
>=90% on the pixel-IDENTICAL subset => >=~80pp of recoverable vision-encoder reuse LOST purely at the hash-domain
seam. Run BOTH hash functions VERBATIM from real source (vLLM hasher.py + SGLang mm_utils.py).

## CROSS-FRAMEWORK DIVERGENCE = the novelty anchor
The two leading OSS VLM servers DISAGREE on the cache-key domain for the same primitive: vLLM = transport bytes,
SGLang = processed pixel_values tensor. No paper/framework doc identifies the processed-tensor-vs-transport-bytes
hash-domain mismatch as a hit-rate ceiling, and no framework closes the cross-framework divergence or ships
canonicalization for vLLM. (TRT-LLM/Triton punt identity to a caller-supplied extra_id = same org-seam, diff default.)

## NULL EXITS (genuine — the L0 CAN fail)
(a) LOSSY re-encode (re-JPEG q90/q95, resize) -> pixels genuinely differ (pilot: max_abs_diff ~1.3/255) -> BOTH
    hashes correctly MISS -> NO divergence. The effect exists ONLY for the LOSSLESS-preserving class (boundary set
    by DATA, not construction => clears killer #8).
(b) If real upstream traffic is byte-STABLE end-to-end -> vLLM byte-hash already wins -> no gap (claim collapses).
(c) The fix (mm_uuid / EXIF ImageID) requires the UPSTREAM SOURCE to inject a stable UUID it does not currently
    emit + that must survive the re-encoding boundary that destroys it (the org-seam; demonstrate it's structurally unset).

## KILLER SCREEN (all 10 cleared — see CLAIM-0060)
#1 not metric-validity (compute-reuse loss, not a counting argument). #2/#3 mechanism is cache-key canonicalization
(textbook) BUT novelty = demonstrating the seam OPEN at a specific unaudited production seam w/ a competing framework
on the other side (the CLAIM-0059 winning move). #4 currency = vision-encoder FLOPs/TTFT saved per hit, magnitude is
bound-INDEPENDENT (property of the hash domain, not batch/HW). #5 measured on real code, hashes run verbatim. #6
continuous batching/chunked-prefill/CUDA-Graphs/paged-attn all act AFTER the cache decision -> cannot recover a forced
recompute (the cache IS the mitigation being defeated; NOT a per-kernel fixed cost CUDA Graphs neutralize). #7 baseline
= vLLM DEFAULT config (cache ON, 4GB). #8 L0 CAN fail (lossy boundary). #9 production-framework prior-art read VERBATIM
from vLLM + SGLang source (SGLang on the other side STRENGTHENS, not kills). #10 citations from cloned source not paraphrase.

## HONEST RISK (most likely committee kill)
Magnitude rests on an UNMEASURED production constant: the rate of LOSSLESS pixel-preserving re-encoding in real
VLM-serving traffic. If real upstreams overwhelmingly re-encode LOSSILY, model-effective pixels change anyway, no
hash can reuse, seam shrinks to ~0. Defense: lossless paths are common+named (EXIF/metadata strip for privacy, PNG
re-optimization, format normalization to lossless-WebP, base64 re-wrap, and CLIENT SDK re-save of an already-decoded
PIL object = the dominant case in agent/RAG pipelines). The L0 it-matters threshold is GATED on measuring this rate
on real traffic => falsifiable, not asserted.

## POSTURE
EXPAND/LIGHTWEIGHT: ONE sharp claim (CLAIM-0060), normal pipeline (L0 -> committee#1 -> cheap-gate/GPU L1 ->
committee#2 -> verdict). If it dies honestly, converge + move to a fresh area. Owner: orchestrator-r7-001.

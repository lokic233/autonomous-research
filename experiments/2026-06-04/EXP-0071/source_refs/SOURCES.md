# Source provenance (real production code, pulled from main)

## vLLM (raw transport-byte hash — production default path)
- `vllm/multimodal/hasher.py` :: MultiModalHasher.{serialize_item, iter_item_to_bytes, hash_kwargs}
  -> saved as vllm_hasher.py
- `vllm/multimodal/media/base.py` :: MediaWithBytes (couples media + original_bytes) -> vllm_multimodal_media_base.py
- `vllm/multimodal/media/image.py` :: ImageMediaIO.load_bytes/load_base64 -> vllm_multimodal_media_image.py
- `vllm/multimodal/media/connector.py` -> vllm_multimodal_media_connector.py
- `vllm/multimodal/processing/inputs.py` :: ProcessorInputs.get_mm_hashes -> vllm_processing_inputs.py
- `vllm/multimodal/processing/processor.py` -> vllm_multimodal_processing_processor.py
- `vllm/multimodal/cache.py` -> vllm_multimodal_cache.py
- `tests/multimodal/test_hasher.py` -> tests_multimodal_test_hasher.py (the project's own hasher tests)
- vLLM main HEAD recorded in PREREG: 3da29aa4a5509b068d378bd8aedbe4837cecf6a6

## SGLang (processed pixel_values hash — invariant to transport divergence)
- `python/sglang/srt/managers/mm_utils.py` :: hash_feature / tensor_hash / data_hash -> sglang_mm_utils.py
- `python/sglang/srt/managers/schedule_batch.py` :: MultimodalDataItem.set_pad_value -> hash_feature(self.feature)
  (self.feature = "the raw features returned by processor, e.g. pixel_values") -> sglang_schedule_batch.py

## Faithfulness verification
- `hashes.py` transcribes these VERBATIM (image path only; model_id + hf_processor_mm_kwargs held constant per pair).
- vLLM hash cross-checked under BOTH blake3 (production default) and sha256: 0 hit/miss disagreements across 2880 pairs.
- SGLang CPU path replicated exactly (sha256 over contiguous uint8 view of flattened tensor, first 8 bytes -> int).

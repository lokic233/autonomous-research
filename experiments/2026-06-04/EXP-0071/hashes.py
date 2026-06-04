"""
FAITHFUL REPLICAS of the real production hash logic, transcribed VERBATIM from:
- vLLM main HEAD 3da29aa4a5509b068d378bd8aedbe4837cecf6a6
  vllm/multimodal/hasher.py :: MultiModalHasher.{serialize_item,iter_item_to_bytes,hash_kwargs}
  vllm/multimodal/media/{base,image}.py :: MediaWithBytes / ImageMediaIO.load_bytes
  vllm/multimodal/processing/inputs.py :: ProcessorInputs.get_mm_hashes
- SGLang main
  python/sglang/srt/managers/mm_utils.py :: hash_feature / tensor_hash / data_hash
  python/sglang/srt/managers/schedule_batch.py :: MultimodalDataItem.set_pad_value -> hash_feature(self.feature)

Only the IMAGE path is replicated (the modality in scope). model_id and hf_processor_mm_kwargs are held
CONSTANT across a variant-pair, so they cannot create/close a divergence; we include them faithfully.
"""
import hashlib, pickle, uuid
import numpy as np
from PIL import Image

try:
    from blake3 import blake3 as _blake3
    HAVE_BLAKE3 = True
except Exception:
    HAVE_BLAKE3 = False


# ---------- vLLM MediaWithBytes wrapper (verbatim semantics) ----------
class MediaWithBytes:
    """vllm/multimodal/media/base.py — couples a media object with its original encoded bytes."""
    def __init__(self, media, original_bytes):
        self.media = media
        self.original_bytes = original_bytes


# ---------- vLLM MultiModalHasher (verbatim) ----------
class MultiModalHasher:
    @classmethod
    def serialize_item(cls, obj):
        if isinstance(obj, (bytes, memoryview)):
            return (obj,)
        if isinstance(obj, str):
            return (obj.encode("utf-8"),)
        if isinstance(obj, (int, float)):
            return (np.array(obj).tobytes(),)
        if isinstance(obj, Image.Image):
            exif = obj.getexif()
            if Image.ExifTags.Base.ImageID in exif and isinstance(
                exif[Image.ExifTags.Base.ImageID], uuid.UUID
            ):
                return (exif[Image.ExifTags.Base.ImageID].bytes,)
            data = {"mode": obj.mode, "data": np.asarray(obj)}
            palette = obj.palette
            if palette is not None:
                data["palette"] = palette.palette
                if palette.rawmode is not None:
                    data["palette_rawmode"] = palette.rawmode
            return cls.iter_item_to_bytes("image", data)
        if isinstance(obj, MediaWithBytes) and isinstance(obj.media, Image.Image):
            exif = obj.media.getexif()
            if Image.ExifTags.Base.ImageID in exif and isinstance(
                exif[Image.ExifTags.Base.ImageID], uuid.UUID
            ):
                return (exif[Image.ExifTags.Base.ImageID].bytes,)
            return cls.iter_item_to_bytes("image", obj.original_bytes)
        if isinstance(obj, np.ndarray):
            if obj.ndim == 0:
                arr_data = obj.item()
            elif obj.flags.c_contiguous:
                arr_data = obj.view(np.uint8).data
            else:
                arr_data = obj.tobytes()
            return cls.iter_item_to_bytes(
                "ndarray",
                {"dtype": obj.dtype.str, "shape": obj.shape, "data": arr_data},
            )
        return (pickle.dumps(obj),)

    @classmethod
    def iter_item_to_bytes(cls, key, obj):
        if obj is None:
            yield key.encode("utf-8")
            return
        if isinstance(obj, (list, tuple)):
            for i, elem in enumerate(obj):
                yield from cls.iter_item_to_bytes(f"{key}.{i}", elem)
        elif isinstance(obj, dict):
            for k, v in obj.items():
                yield from cls.iter_item_to_bytes(f"{key}.{k}", v)
        else:
            yield key.encode("utf-8")
            yield from cls.serialize_item(obj)

    @classmethod
    def hash_kwargs(cls, _algorithm="blake3", **kwargs):
        if _algorithm == "blake3" and HAVE_BLAKE3:
            hasher = _blake3()
        elif _algorithm == "sha256":
            hasher = hashlib.sha256()
        else:
            hasher = hashlib.sha256()  # fallback if blake3 absent
        for k, v in sorted(kwargs.items(), key=lambda kv: kv[0]):
            for bytes_ in cls.iter_item_to_bytes(k, v):
                hasher.update(bytes_)
        return hasher.hexdigest()


# ---------- vLLM ImageMediaIO.load_bytes (verbatim semantics) ----------
def vllm_load_bytes(data: bytes) -> MediaWithBytes:
    """Production arrival path: Image.open(BytesIO(data)); return MediaWithBytes(image, data)."""
    from io import BytesIO
    image = Image.open(BytesIO(data))
    image.load()
    return MediaWithBytes(image, data)


def vllm_hash_production(data: bytes, model_id="Qwen/Qwen2.5-VL-7B-Instruct",
                         hf_kwargs=None, algorithm="blake3") -> str:
    """vLLM cache key for the PRODUCTION (server/base64/url) path: hashes original transport bytes."""
    item = vllm_load_bytes(data)
    kw = dict(hf_kwargs or {})
    return MultiModalHasher.hash_kwargs(_algorithm=algorithm, model_id=model_id, image=item, **kw)


def vllm_hash_offline_pil(image: Image.Image, model_id="Qwen/Qwen2.5-VL-7B-Instruct",
                          hf_kwargs=None, algorithm="blake3") -> str:
    """vLLM cache key for the OFFLINE bare-PIL path: hashes decoded array (lossless-invariant)."""
    kw = dict(hf_kwargs or {})
    return MultiModalHasher.hash_kwargs(_algorithm=algorithm, model_id=model_id, image=image, **kw)


# ---------- SGLang hash_feature (verbatim, CPU path) ----------
def sglang_data_hash(data) -> int:
    hash_bytes = hashlib.sha256(data).digest()[:8]
    return int.from_bytes(hash_bytes, byteorder="big", signed=False)

def sglang_tensor_hash_single_np(arr: np.ndarray) -> int:
    """CPU single-tensor path: sha256 over contiguous uint8 view of the flattened tensor."""
    import torch
    t = torch.as_tensor(np.ascontiguousarray(arr))
    t = t.detach().contiguous()
    hasher = hashlib.sha256()
    hasher.update(memoryview(t.reshape(-1).view(torch.uint8).numpy()))
    hb = hasher.digest()[:8]
    return int.from_bytes(hb, byteorder="big", signed=False)

def sglang_hash_feature(f) -> int:
    """python/sglang/srt/managers/mm_utils.py :: hash_feature (np.ndarray / torch.Tensor CPU path)."""
    import torch
    if isinstance(f, np.ndarray):
        arr = np.ascontiguousarray(f)
        hasher = hashlib.sha256()
        hasher.update(memoryview(arr))
        hb = hasher.digest()[:8]
        return int.from_bytes(hb, byteorder="big", signed=False)
    elif isinstance(f, torch.Tensor):
        # tensor_hash([f]) -> CPU list path
        t = f.detach().contiguous()
        hasher = hashlib.sha256()
        hasher.update(memoryview(t.reshape(-1).view(torch.uint8).numpy()))
        hb = hasher.digest()[:8]
        return int.from_bytes(hb, byteorder="big", signed=False)
    return sglang_data_hash(f)

"""Generate the LOSSLESS transport-variant set a real CDN/proxy/client emits, plus a LOSSY null-exit control.
Each variant returns (transport_bytes, label, klass). transport_bytes is what reaches the endpoint."""
import io, base64
from PIL import Image, PngImagePlugin
import numpy as np

def _png_bytes(img, **kw):
    b = io.BytesIO(); img.save(b, format="PNG", **kw); return b.getvalue()

def _webp_lossless_bytes(img):
    b = io.BytesIO(); img.save(b, format="WEBP", lossless=True); return b.getvalue()

def _jpeg_bytes(img, q):
    b = io.BytesIO(); img.convert("RGB").save(b, format="JPEG", quality=q); return b.getvalue()

def _orig_with_exif(img):
    """Build a realistic 'source' image that CARRIES EXIF/metadata (as a phone/camera/CMS would),
    so that a downstream metadata-strip is a genuine, distinct byte transform."""
    b = io.BytesIO()
    exif = Image.Exif()
    exif[0x010F] = "ACME Camera"   # Make
    exif[0x0110] = "Model X"        # Model
    exif[0x0131] = "ImagePipeline 2.3"  # Software
    exif[0x9003] = "2026:06:04 12:00:00"  # DateTimeOriginal
    # JPEG carries EXIF natively and is the dominant phone/CMS source format; use high-quality JPEG
    # as the SOURCE so the lossless ops below operate on a fixed decoded array.
    img.save(b, format="JPEG", quality=98, exif=exif.tobytes())
    return b.getvalue()

def make_variants(orig_png_bytes: bytes):
    """orig_png_bytes = canonical original transport bytes (PNG). Returns list of dicts.

    The ORIGINAL transport bytes here are a realistic SOURCE artifact: a JPEG-with-EXIF (as a phone/
    camera/CMS emits). The decoded RGB array of THAT source is the reference 'model-effective' image;
    every lossless variant must preserve that exact array. This makes EXIF-strip / re-encode genuinely
    DISTINCT byte streams (not trivially byte-identical), which is the real upstream behavior."""
    base_rgb = Image.open(io.BytesIO(orig_png_bytes)).convert("RGB")
    # SOURCE = JPEG-with-EXIF; its decoded array is the fixed reference for lossless preservation.
    src_bytes = _orig_with_exif(base_rgb)
    img = Image.open(io.BytesIO(src_bytes)).convert("RGB")  # decoded reference array
    out = []

    # ORIGINAL (identity reference) = the JPEG-with-EXIF source bytes as they arrive.
    out.append(dict(label="orig", klass="orig", data=src_bytes))

    # ---- LOSSLESS class: pixel-PRESERVING transport ops on the decoded source array ----
    # L1 PNG re-optimized (lossless): decode -> PNG optimize=True/compress 9 (imgproxy/thumbor PNG path)
    out.append(dict(label="L1_png_reopt", klass="lossless",
                    data=_png_bytes(img, optimize=True, compress_level=9)))
    # L1b PNG re-compress level 0 (a different PNG encoder setting -> different bytes, same pixels)
    out.append(dict(label="L1b_png_recompress0", klass="lossless",
                    data=_png_bytes(img, compress_level=0)))
    # L2 EXIF/metadata strip: re-save WITHOUT metadata. Pixels identical, bytes differ from source.
    #    (privacy-strip path: many proxies emit a PNG/JPEG with all metadata removed)
    out.append(dict(label="L2_exif_strip", klass="lossless",
                    data=_png_bytes(img, compress_level=6)))
    # L3 PNG -> lossless WebP (format normalization to lossless-WebP, CDN content-negotiation)
    out.append(dict(label="L3_lossless_webp", klass="lossless",
                    data=_webp_lossless_bytes(img)))
    # L4 base64 MIME re-wrap of the ORIGINAL source bytes (transport re-wrap; same decoded image).
    #    NOTE: vLLM load_base64 DECODES this back to src_bytes, so its original_bytes == src_bytes.
    b64 = base64.b64encode(src_bytes).decode()
    mime = f"data:image/jpeg;base64,{b64}".encode("utf-8")
    out.append(dict(label="L4_base64_rewrap", klass="lossless", data=mime, is_b64wrap=True,
                    inner=src_bytes))
    # L5 client SDK re-save: decode -> re-encode as a DIFFERENT lossless container (TIFF, raw deflate).
    #    Pixel-preserving, distinct bytes. (agent/RAG re-save of an already-decoded PIL object)
    b = io.BytesIO(); img.save(b, format="TIFF", compression="tiff_deflate")
    out.append(dict(label="L5_client_resave_tiff", klass="lossless", data=b.getvalue()))

    # ---- LOSSY class (NULL-EXIT control; pixels SHOULD differ) ----
    out.append(dict(label="Y1_jpeg_q90", klass="lossy", data=_jpeg_bytes(img, 90)))
    out.append(dict(label="Y2_jpeg_q95", klass="lossy", data=_jpeg_bytes(img, 95)))
    # Y3 resize 99% then back (bilinear) -> re-encode PNG
    w, h = img.size
    small = img.resize((max(1,int(w*0.99)), max(1,int(h*0.99))), Image.BILINEAR)
    back = small.resize((w, h), Image.BILINEAR)
    out.append(dict(label="Y3_resize99", klass="lossy", data=_png_bytes(back)))

    return out

def decode_rgb_array(variant):
    """Decode the transport bytes back to an RGB uint8 array (what the model effectively sees pre-processor)."""
    data = variant["data"]
    if variant.get("is_b64wrap"):
        # base64 MIME wrapper: strip header, decode -> inner bytes
        s = data.decode("utf-8")
        b64 = s.split(",",1)[1]
        raw = base64.b64decode(b64)
        img = Image.open(io.BytesIO(raw))
    else:
        img = Image.open(io.BytesIO(data))
    img.load()
    return np.asarray(img.convert("RGB"))

def bytes_for_vllm(variant):
    """The exact byte string vLLM's load_bytes would receive.
    For base64 inputs, load_base64 decodes the b64 payload BEFORE MediaWithBytes — so original_bytes
    = the decoded inner bytes (per ImageMediaIO.load_base64 -> load_bytes(b64decode(data)))."""
    if variant.get("is_b64wrap"):
        return variant["inner"]   # decoded payload == original PNG bytes
    return variant["data"]

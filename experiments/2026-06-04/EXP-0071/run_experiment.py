"""EXP-0071 main harness.
For N real images x {lossless variants, lossy controls}:
  - vLLM PRODUCTION hash (MediaWithBytes.original_bytes), blake3 + sha256 cross-check
  - vLLM OFFLINE bare-PIL hash (decoded array; secondary contrast)
  - SGLang processed-pixel hash (hash_feature over real pixel_values from HF processor)
  - pixel-identity verification (numpy max_abs_diff on decoded RGB arrays vs original)
Outputs per-pair CSV + aggregate JSON.
"""
import os, sys, io, json, csv, glob, time
import numpy as np
from PIL import Image
import hashes as H
import variants as V

MODEL_ID = os.environ.get("MODEL_ID", "Qwen/Qwen2.5-VL-7B-Instruct")
RESULTS_DIR = "results"
os.makedirs(RESULTS_DIR, exist_ok=True)

# ---- load a real HF image processor (lightweight; no model weights) ----
processor = None
proc_name = None
def load_processor():
    global processor, proc_name
    from transformers import AutoImageProcessor
    for mid in [MODEL_ID, "openai/clip-vit-base-patch32", "google/vit-base-patch16-224"]:
        try:
            processor = AutoImageProcessor.from_pretrained(mid)
            proc_name = mid + " :: " + type(processor).__name__
            print("PROCESSOR:", proc_name, flush=True)
            return
        except Exception as e:
            print("proc fail", mid, repr(e)[:120], flush=True)
    raise RuntimeError("no image processor loadable")

def pixel_values_np(rgb_array):
    """Run the real HF image processor -> processed pixel_values as a contiguous np array."""
    img = Image.fromarray(rgb_array.astype(np.uint8), mode="RGB")
    out = processor(images=img, return_tensors="np")
    key = "pixel_values" if "pixel_values" in out else list(out.keys())[0]
    pv = out[key]
    return np.ascontiguousarray(np.asarray(pv))

def main():
    load_processor()
    imgs = sorted(glob.glob("images_orig/*.png"))
    if not imgs:
        print("NO IMAGES", flush=True); sys.exit(2)
    print(f"{len(imgs)} source images", flush=True)

    rows = []
    t0 = time.time()
    for idx, path in enumerate(imgs):
        orig_bytes = open(path, "rb").read()
        try:
            vs = V.make_variants(orig_bytes)
        except Exception as e:
            print("variant gen fail", path, repr(e)[:120], flush=True); continue

        # original reference
        ref = next(v for v in vs if v["klass"]=="orig")
        ref_rgb = V.decode_rgb_array(ref)
        ref_vllm_bytes = V.bytes_for_vllm(ref)
        # vLLM production hash of the ORIGINAL
        ref_vllm_prod = H.vllm_hash_production(ref_vllm_bytes, model_id=MODEL_ID, algorithm="blake3")
        ref_vllm_prod_sha = H.vllm_hash_production(ref_vllm_bytes, model_id=MODEL_ID, algorithm="sha256")
        # vLLM offline PIL hash of original
        ref_img = Image.open(io.BytesIO(ref_vllm_bytes)); ref_img.load(); ref_img=ref_img.convert("RGB")
        ref_vllm_pil = H.vllm_hash_offline_pil(ref_img, model_id=MODEL_ID, algorithm="blake3")
        # SGLang processed hash of original
        try:
            ref_pv = pixel_values_np(ref_rgb)
            ref_sglang = H.sglang_hash_feature(ref_pv)
        except Exception as e:
            print("proc fail orig", path, repr(e)[:120], flush=True); continue

        for v in vs:
            if v["klass"]=="orig": continue
            try:
                rgb = V.decode_rgb_array(v)
            except Exception as e:
                print("decode fail", v["label"], repr(e)[:80], flush=True); continue
            # pixel identity vs original
            if rgb.shape == ref_rgb.shape:
                max_abs_diff = int(np.max(np.abs(rgb.astype(np.int32) - ref_rgb.astype(np.int32))))
                pixel_identical = (max_abs_diff == 0)
            else:
                max_abs_diff = -1
                pixel_identical = False

            vllm_bytes = V.bytes_for_vllm(v)
            vllm_prod = H.vllm_hash_production(vllm_bytes, model_id=MODEL_ID, algorithm="blake3")
            vllm_prod_sha = H.vllm_hash_production(vllm_bytes, model_id=MODEL_ID, algorithm="sha256")
            vimg = Image.open(io.BytesIO(vllm_bytes)); vimg.load(); vimg=vimg.convert("RGB")
            vllm_pil = H.vllm_hash_offline_pil(vimg, model_id=MODEL_ID, algorithm="blake3")
            try:
                pv = pixel_values_np(rgb)
                sglang_h = H.sglang_hash_feature(pv)
            except Exception as e:
                print("proc fail var", v["label"], repr(e)[:80], flush=True); continue

            rows.append(dict(
                img=os.path.basename(path), variant=v["label"], klass=v["klass"],
                pixel_identical=int(pixel_identical), max_abs_diff=max_abs_diff,
                vllm_prod_hit=int(vllm_prod == ref_vllm_prod),
                vllm_prod_sha_hit=int(vllm_prod_sha == ref_vllm_prod_sha),
                vllm_pil_hit=int(vllm_pil == ref_vllm_pil),
                sglang_hit=int(sglang_h == ref_sglang),
            ))
        if (idx+1) % 25 == 0:
            print(f"  {idx+1}/{len(imgs)} imgs, {len(rows)} pairs, {time.time()-t0:.0f}s", flush=True)

    # write CSV
    csv_path = os.path.join(RESULTS_DIR, "per_pair.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print("wrote", csv_path, len(rows), "pairs", flush=True)

    # aggregate
    def agg(filt):
        sub = [r for r in rows if filt(r)]
        n = len(sub)
        if n == 0: return dict(n=0)
        return dict(
            n=n,
            pixel_identical_frac=round(sum(r["pixel_identical"] for r in sub)/n, 4),
            vllm_prod_hit_rate=round(sum(r["vllm_prod_hit"] for r in sub)/n, 4),
            vllm_pil_hit_rate=round(sum(r["vllm_pil_hit"] for r in sub)/n, 4),
            sglang_hit_rate=round(sum(r["sglang_hit"] for r in sub)/n, 4),
        )

    summary = {
        "processor": proc_name,
        "model_id": MODEL_ID,
        "have_blake3": H.HAVE_BLAKE3,
        "n_source_images": len(imgs),
        "n_pairs": len(rows),
        "ALL_lossless": agg(lambda r: r["klass"]=="lossless"),
        "ALL_lossy": agg(lambda r: r["klass"]=="lossy"),
        "lossless_PIXEL_IDENTICAL_subset": agg(lambda r: r["klass"]=="lossless" and r["pixel_identical"]),
        "lossy_PIXEL_IDENTICAL_subset": agg(lambda r: r["klass"]=="lossy" and r["pixel_identical"]),
        "per_variant": {},
    }
    labels = sorted(set(r["variant"] for r in rows))
    for lab in labels:
        summary["per_variant"][lab] = agg(lambda r: r["variant"]==lab)

    with open(os.path.join(RESULTS_DIR,"summary.json"),"w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2), flush=True)

if __name__ == "__main__":
    main()

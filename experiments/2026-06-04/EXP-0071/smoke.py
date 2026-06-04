import glob, io, numpy as np
from PIL import Image
import hashes as H, variants as V
from transformers import AutoImageProcessor
proc=None
for mid in ["openai/clip-vit-base-patch32","google/vit-base-patch16-224"]:
    try:
        proc=AutoImageProcessor.from_pretrained(mid); print("PROC",mid,type(proc).__name__); break
    except Exception as e: print("fail",mid,repr(e)[:100])
def pv(rgb):
    out=proc(images=Image.fromarray(rgb.astype(np.uint8),"RGB"), return_tensors="np")
    k="pixel_values" if "pixel_values" in out else list(out)[0]
    return np.ascontiguousarray(np.asarray(out[k]))
for p in sorted(glob.glob("images_orig/*.png"))[:2]:
    ob=open(p,"rb").read()
    vs=V.make_variants(ob)
    ref=[v for v in vs if v["klass"]=="orig"][0]
    rref=V.decode_rgb_array(ref); bref=V.bytes_for_vllm(ref)
    vp_ref=H.vllm_hash_production(bref,algorithm="blake3")
    pil_ref=H.vllm_hash_offline_pil(Image.open(io.BytesIO(bref)).convert("RGB"),algorithm="blake3")
    sg_ref=H.sglang_hash_feature(pv(rref))
    print("==",p,"orig bytes",len(bref))
    for v in vs:
        if v["klass"]=="orig": continue
        r=V.decode_rgb_array(v); b=V.bytes_for_vllm(v)
        mad=int(np.max(np.abs(r.astype(int)-rref.astype(int)))) if r.shape==rref.shape else -1
        vp=H.vllm_hash_production(b,algorithm="blake3")
        pil=H.vllm_hash_offline_pil(Image.open(io.BytesIO(b)).convert("RGB"),algorithm="blake3")
        sg=H.sglang_hash_feature(pv(r))
        print(f"  {v['label']:22s} klass={v['klass']:8s} mad={mad:4d} vllmProd_hit={int(vp==vp_ref)} vllmPIL_hit={int(pil==pil_ref)} sglang_hit={int(sg==sg_ref)}")

import glob, io, numpy as np
from PIL import Image
import hashes as H, variants as V
# processor
from transformers import AutoImageProcessor
proc=None
for mid in ["Qwen/Qwen2.5-VL-7B-Instruct","openai/clip-vit-base-patch32","google/vit-base-patch16-224"]:
    try:
        proc=AutoImageProcessor.from_pretrained(mid); print("PROC",mid,type(proc).__name__); break
    except Exception as e: print("fail",mid,repr(e)[:100])
assert proc is not None
imgs=sorted(glob.glob("images_orig/*.png"))[:2]
for p in imgs:
    ob=open(p,"rb").read(); vs=V.make_variants(ob)
    ref=next(v for v in vs if v["klass"]=="orig"); ref_rgb=V.decode_rgb_array(ref)
    refb=V.bytes_for_vllm(ref)
    rp=H.vllm_hash_production(refb); 
    refimg=Image.open(io.BytesIO(refb)); refimg.load(); refimg=refimg.convert("RGB")
    rpil=H.vllm_hash_offline_pil(refimg)
    pv=proc(images=Image.fromarray(ref_rgb,"RGB"),return_tensors="np")["pixel_values"]
    rs=H.sglang_hash_feature(np.ascontiguousarray(pv))
    print("=== ",p, "pv.shape", pv.shape)
    for v in vs:
        if v["klass"]=="orig": continue
        rgb=V.decode_rgb_array(v)
        mad=int(np.max(np.abs(rgb.astype(int)-ref_rgb.astype(int)))) if rgb.shape==ref_rgb.shape else -1
        vb=V.bytes_for_vllm(v); vp=H.vllm_hash_production(vb)
        vimg=Image.open(io.BytesIO(vb)); vimg.load(); vimg=vimg.convert("RGB"); vpil=H.vllm_hash_offline_pil(vimg)
        pvv=proc(images=Image.fromarray(rgb,"RGB"),return_tensors="np")["pixel_values"]
        sh=H.sglang_hash_feature(np.ascontiguousarray(pvv))
        print(f"  {v['label']:24s} klass={v['klass']:8s} pxident={int(mad==0)} mad={mad} vllm_byte_hit={int(vp==rp)} vllm_pil_hit={int(vpil==rpil)} sglang_hit={int(sh==rs)}")

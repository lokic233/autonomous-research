from transformers import AutoImageProcessor
import numpy as np
from PIL import Image
img = Image.new("RGB",(640,480),(123,87,200))
for mid in ["Qwen/Qwen2.5-VL-7B-Instruct","openai/clip-vit-base-patch32","llava-hf/llava-1.5-7b-hf"]:
    try:
        p = AutoImageProcessor.from_pretrained(mid)
        out = p(images=img, return_tensors="np")
        key = "pixel_values" if "pixel_values" in out else list(out.keys())[0]
        pv = out[key]
        print("OK", mid, type(p).__name__, "->", key, getattr(pv,'shape',None), getattr(pv,'dtype',None))
        break
    except Exception as e:
        print("FAIL", mid, repr(e)[:160])

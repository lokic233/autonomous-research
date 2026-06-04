import os, io, sys
os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT","60")
from datasets import load_dataset
from PIL import Image
import numpy as np

OUT="images_orig"
os.makedirs(OUT, exist_ok=True)
N=int(os.environ.get("NIMG","320"))

# Try a few real image datasets in order of robustness
candidates = [
    ("detection-datasets/coco", "val", "image"),
    ("huggingface/cats-image", "test", "image"),
    ("cifar100", "test", "img"),
]
saved=0
for name, split, col in candidates:
    try:
        print(f"trying {name} [{split}] col={col}", flush=True)
        ds = load_dataset(name, split=f"{split}[:{N}]", streaming=False)
        for i, ex in enumerate(ds):
            if saved>=N: break
            img = ex[col]
            if not isinstance(img, Image.Image): continue
            img = img.convert("RGB")
            # save as PNG canonical original
            img.save(os.path.join(OUT, f"img_{saved:04d}.png"), format="PNG")
            saved+=1
        print(f"saved {saved} from {name}", flush=True)
        if saved>=N: break
    except Exception as e:
        print(f"FAIL {name}: {repr(e)[:200]}", flush=True)
        continue
print("TOTAL_SAVED", saved)

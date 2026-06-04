import os, io
from datasets import load_dataset
from PIL import Image
OUT="images_orig"; os.makedirs(OUT, exist_ok=True)
N=int(os.environ.get("NIMG","320")); saved=0
# small, fast, real-photo datasets; streaming to avoid full download
cands=[
 ("uoft-cs/cifar10","train","img"),
 ("frgfm/imagenette","320px","image","train"),
 ("food101","train","image"),
]
def tryone(name, split, col, cfg=None):
    global saved
    try:
        print("trying", name, split, col, cfg, flush=True)
        if cfg:
            ds=load_dataset(name, cfg, split=split, streaming=True)
        else:
            ds=load_dataset(name, split=split, streaming=True)
        for ex in ds:
            if saved>=N: break
            img=ex.get(col)
            if not isinstance(img, Image.Image): continue
            img=img.convert("RGB")
            # upscale tiny (cifar 32x32) so processor + variants are meaningful
            if min(img.size) < 96:
                img=img.resize((224,224), Image.BICUBIC)
            img.save(os.path.join(OUT, f"img_{saved:04d}.png"), format="PNG")
            saved+=1
            if saved % 50 == 0: print("saved", saved, flush=True)
        print("done", name, "saved", saved, flush=True)
    except Exception as e:
        print("FAIL", name, repr(e)[:160], flush=True)
for c in cands:
    if saved>=N: break
    if len(c)==4: tryone(c[0],c[1],c[2],c[3])
    else: tryone(c[0],c[1],c[2])
print("TOTAL_SAVED", saved)

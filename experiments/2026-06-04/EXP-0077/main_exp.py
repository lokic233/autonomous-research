#!/usr/bin/env python3
"""MAIN: M1(passthrough) vs M2(re-encode) mirrors x consumer-EXIF toggle, on a controlled
tagged set + identity control + requant control. Fixed off-the-shelf classifier + default loader.

Headline metric: accuracy(consumer honors EXIF) - accuracy(default ignore), on each mirror.
"""
import io, os, json, csv, sys
import numpy as np
import torch, torchvision
from torchvision import transforms
from torchvision.models import resnet50, ResNet50_Weights
from PIL import Image, ImageOps
import piexif

EXPDIR="/Users/dengcchi/autonomous-research-v3/experiments/2026-06-04/EXP-0077"
RES=os.path.join(EXPDIR,"results")
ORIENT=0x0112
torch.manual_seed(0); np.random.seed(0)

# ---- fixed model + default preprocessing ----
weights=ResNet50_Weights.IMAGENET1K_V2
model=resnet50(weights=weights).eval()
preprocess=weights.transforms()           # the DEFAULT torchvision transform (resize/center-crop/normalize)
classes=weights.meta["categories"]

def classify(pil_rgb):
    x=preprocess(pil_rgb).unsqueeze(0)
    with torch.no_grad():
        logits=model(x)
    return int(logits.argmax(1).item())

# ---- EXIF helpers ----
def set_orientation(pil_img, orientation, quality=92):
    """Return JPEG bytes with the given EXIF orientation tag (image pixels UNROTATED)."""
    exif={"0th":{piexif.ImageIFD.Orientation:orientation},"Exif":{},"GPS":{},"1st":{},"thumbnail":None}
    buf=io.BytesIO(); pil_img.convert('RGB').save(buf,format='JPEG',exif=piexif.dump(exif),quality=quality)
    return buf.getvalue()

def reencode_pil_path(jpeg_bytes, quality=92):
    """The EXACT HF datasets PIL-object path: open -> save(BytesIO, JPEG). Strips EXIF."""
    im=Image.open(io.BytesIO(jpeg_bytes)); im.load()
    buf=io.BytesIO(); im.save(buf,format='JPEG',quality=quality)   # no exif= -> EXIF dropped
    return buf.getvalue()

def read_orient(jpeg_bytes):
    return Image.open(io.BytesIO(jpeg_bytes)).getexif().get(ORIENT,1)

def load_consumer(jpeg_bytes, honor_exif):
    im=Image.open(io.BytesIO(jpeg_bytes))
    if honor_exif:
        im=ImageOps.exif_transpose(im)     # consumer HONORS orientation
    return im.convert('RGB')

# ---- build a base set of real-content images (CIFAR-10 upscaled gives real photos w/ labels-ish;
#      but we need ImageNet-classifiable content. Use torchvision sample images repeated w/ transforms.) ----
def get_base_images(n):
    """Use a small set of real photographic images shipped with torchvision/PIL + downloaded ImageNet val-ish.
    To stay offline-robust we synthesize photographic-like content from CIFAR if needed, but prefer real."""
    imgs=[]
    # Try torchvision built-in sample via FakeData fallback; prefer real downloaded set passed in env
    base_dir=os.environ.get("BASE_IMG_DIR","")
    if base_dir and os.path.isdir(base_dir):
        files=sorted([f for f in os.listdir(base_dir) if f.lower().endswith(('.jpg','.jpeg','.png'))])[:n]
        for f in files:
            try: imgs.append(Image.open(os.path.join(base_dir,f)).convert('RGB'))
            except: pass
    return imgs

def run_condition(base_imgs, orientation):
    """For each base image: make M1 bytes (tag=orientation, passthrough) and M2 bytes (re-encoded, tag gone).
    Classify under honor/no-honor on each mirror. Pred at orientation=1 (no-honor M1) is the 'reference'."""
    rows=[]
    for idx,img in enumerate(base_imgs):
        m1=set_orientation(img, orientation)          # passthrough: tag present
        m2=reencode_pil_path(m1)                       # re-encode: tag destroyed
        o1=read_orient(m1); o2=read_orient(m2)
        # reference label = default-loader prediction on the canonical UNROTATED pixels (orientation ignored)
        ref=classify(load_consumer(m1, honor_exif=False))
        preds={}
        for mirror,b in [("M1",m1),("M2",m2)]:
            for honor in [False,True]:
                p=classify(load_consumer(b, honor_exif=honor))
                preds[(mirror,honor)]=p
        rows.append(dict(idx=idx, orientation=orientation, o1=o1, o2=o2, ref=ref,
            M1_nohonor=preds[("M1",False)], M1_honor=preds[("M1",True)],
            M2_nohonor=preds[("M2",False)], M2_honor=preds[("M2",True)]))
    return rows

def agree(rows, key):
    """fraction of rows whose prediction under `key` equals the reference (no-honor canonical)."""
    return sum(1 for r in rows if r[key]==r["ref"])/len(rows) if rows else float('nan')

if __name__=="__main__":
    n=int(os.environ.get("N_IMG","120"))
    base=get_base_images(n)
    print(f"base images: {len(base)}")
    if len(base)<10:
        print("ERROR: insufficient base images. Set BASE_IMG_DIR."); sys.exit(2)

    summary={}
    all_rows={}
    # CONDITION A: tagged non-identity orientation=6 (90deg CW phone tag) -> the active case
    for label,orient in [("tagged_orient6",6),("identity_ctrl_orient1",1)]:
        rows=run_condition(base,orient)
        all_rows[label]=rows
        # "consistency vs canonical reference" = accuracy proxy (1.0 = identical to reference scoring)
        c={
          "M1_nohonor":agree(rows,"M1_nohonor"),
          "M1_honor":agree(rows,"M1_honor"),
          "M2_nohonor":agree(rows,"M2_nohonor"),
          "M2_honor":agree(rows,"M2_honor"),
        }
        c["M1_toggle_pp"]=round((c["M1_nohonor"]-c["M1_honor"])*100,2)   # honor moves score by this
        c["M2_toggle_pp"]=round((c["M2_nohonor"]-c["M2_honor"])*100,2)
        c["M1_vs_M2_default_pp"]=round((c["M1_nohonor"]-c["M2_nohonor"])*100,2)
        summary[label]=c
        print(label, json.dumps(c))

    # CONTROL (b): requantization-only — re-encode tag-1 images, compare default M1 vs M2 (both honor off)
    rows1=all_rows["identity_ctrl_orient1"]
    requant_drift_pp=round((1.0 - agree(rows1,"M2_nohonor"))*100,2)  # how much pure re-encode shifts preds
    summary["requant_only_drift_pp"]=requant_drift_pp
    print("requant_only_drift_pp(tag1, M2 default vs ref):", requant_drift_pp)

    # save CSVs
    for label,rows in all_rows.items():
        with open(os.path.join(RES,f"rows_{label}.csv"),"w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    with open(os.path.join(RES,"main_summary.json"),"w") as f:
        json.dump(dict(n_images=len(base), model="resnet50_IMAGENET1K_V2", summary=summary),f,indent=2)
    print("\nWROTE main_summary.json + per-condition CSVs")

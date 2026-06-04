#!/usr/bin/env python3
"""STEP 0: serialization-behavior verification (potential KILL gate)."""
import io, sys, json
import PIL, torch, torchvision, datasets, piexif
from PIL import Image, ImageOps
import numpy as np

OUT = {}
OUT['versions'] = dict(
    python=sys.version.split()[0], pillow=PIL.__version__,
    torch=torch.__version__, torchvision=torchvision.__version__,
    datasets=datasets.__version__, piexif=piexif.VERSION,
)
print("VERSIONS:", json.dumps(OUT['versions']))

ORIENT_TAG = 0x0112  # 274

def make_tagged_jpeg(orientation, size=(64,48), color=(120,60,30)):
    """Build a JPEG with a given EXIF orientation tag."""
    img = Image.new('RGB', size, color)
    # add some asymmetric content so transpose changes pixels
    for x in range(size[0]//2):
        for y in range(size[1]//2):
            img.putpixel((x,y),(240,240,10))
    exif = {"0th":{piexif.ImageIFD.Orientation: orientation}, "Exif":{}, "GPS":{}, "1st":{}, "thumbnail":None}
    exif_bytes = piexif.dump(exif)
    buf = io.BytesIO()
    img.save(buf, format='JPEG', exif=exif_bytes, quality=92)
    return buf.getvalue()

def read_orientation(jpeg_bytes):
    """Read EXIF orientation tag from raw bytes (returns None if absent)."""
    im = Image.open(io.BytesIO(jpeg_bytes))
    ex = im.getexif()
    return ex.get(ORIENT_TAG, None)

# ---- build a tagged JPEG (orientation=6, the classic 90deg-CW phone tag) ----
orig_bytes = make_tagged_jpeg(6)
print("\n(setup) original tagged JPEG: orientation tag =", read_orientation(orig_bytes))

# ============================================================
# (a) HF datasets Image.encode_example on in-memory PIL re-encodes via PIL.save, strips EXIF
# ============================================================
feat = datasets.Image()
pil_obj = Image.open(io.BytesIO(orig_bytes))  # in-memory PIL object (the common .map()/cast case)
pil_obj.load()
enc_from_pil = feat.encode_example(pil_obj)          # PIL-OBJECT path
enc_bytes = enc_from_pil['bytes']
a_orient = read_orientation(enc_bytes) if enc_bytes else None
OUT['a_pil_path_orientation_after_encode'] = a_orient
OUT['a_pil_path_has_bytes'] = enc_bytes is not None
print("\n(a) datasets.Image().encode_example(PIL object):")
print("    re-encoded bytes present:", enc_bytes is not None, "| format:", enc_from_pil.get('path'))
print("    EXIF orientation in re-encoded bytes:", a_orient, "(None/1 => DESTROYED)")

# ============================================================
# (b) file-PATH cell keeps original bytes (tag survives)
# ============================================================
import tempfile, os
tmpf = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
tmpf.write(orig_bytes); tmpf.close()
enc_from_path = feat.encode_example(tmpf.name)       # PATH path
# datasets stores path; bytes read lazily. Read what it stores:
b_path_field = enc_from_path.get('path')
# decode it back the way datasets does on read:
decoded = feat.decode_example(enc_from_path) if hasattr(feat,'decode_example') else None
# Direct: the on-disk file still has the tag
with open(tmpf.name,'rb') as fh: path_bytes = fh.read()
b_orient = read_orientation(path_bytes)
OUT['b_path_cell_orientation'] = b_orient
OUT['b_path_field'] = b_path_field
print("\n(b) datasets.Image().encode_example(file path):")
print("    stored path:", b_path_field is not None, "| original on-disk EXIF orientation:", b_orient)
os.unlink(tmpf.name)

# ============================================================
# (c) PIL Image.open does NOT apply orientation by default
# ============================================================
im_default = np.asarray(Image.open(io.BytesIO(orig_bytes)).convert('RGB'))
im_honored = np.asarray(ImageOps.exif_transpose(Image.open(io.BytesIO(orig_bytes))).convert('RGB'))
c_changes = not np.array_equal(im_default, im_honored)
OUT['c_pil_default_ignores_orientation'] = c_changes  # True => default differs from honored => default ignores
print("\n(c) PIL Image.open default vs exif_transpose:")
print("    default shape:", im_default.shape, "| honored shape:", im_honored.shape)
print("    pixels DIFFER (default ignored orientation, transpose changed them):", c_changes)

# ============================================================
# (d) torchvision decode_jpeg default apply_exif_orientation=False
# ============================================================
import inspect
from torchvision.io import decode_jpeg
sig = inspect.signature(decode_jpeg)
d_default = sig.parameters.get('apply_exif_orientation')
OUT['d_decode_jpeg_default_apply_exif'] = (str(d_default.default) if d_default else "PARAM_ABSENT")
print("\n(d) torchvision.io.decode_jpeg signature apply_exif_orientation default:")
print("   ", d_default)

# ---- KILL GATE ----
a_destroyed = (a_orient is None) or (a_orient == 1)
b_survived  = (b_orient == 6)
print("\n==== VERIFICATION SUMMARY ====")
print("(a) PIL-object path DESTROYS tag:", a_destroyed, "(orient=",a_orient,")")
print("(b) PATH cell PRESERVES tag    :", b_survived, "(orient=",b_orient,")")
print("(c) PIL default IGNORES orient :", c_changes)
print("(d) torchvision default off    :", OUT['d_decode_jpeg_default_apply_exif'])
OUT['KILL'] = (not a_destroyed)
print("\nKILL (datasets preserves EXIF on PIL path)?:", OUT['KILL'])

with open('/Users/dengcchi/autonomous-research-v3/experiments/2026-06-04/EXP-0077/results/step0_verify.json','w') as f:
    json.dump(OUT,f,indent=2)
print("\nwrote step0_verify.json")

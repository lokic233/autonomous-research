#!/usr/bin/env python3
"""Measure f = fraction of non-identity EXIF orientation tag on REAL public phone-sourced sets.
Reads RAW stored bytes (not decoded PIL) so we catch surviving EXIF tags."""
import io, os, json, sys
from PIL import Image
from collections import Counter
ORIENT=0x0112

def orient_of_bytes(b):
    try:
        im=Image.open(io.BytesIO(b)); ex=im.getexif()
        return ex.get(ORIENT, 1)
    except Exception:
        return None

def scan_dataset(repo, split, n, img_col=None, streaming=True):
    import datasets
    ds = datasets.load_dataset(repo, split=split, streaming=streaming)
    cnt=Counter(); raw_seen=0; pil_seen=0; total=0; bytes_with_tag=0
    for i,row in enumerate(ds):
        if total>=n: break
        # find an image-ish column
        col=img_col
        if col is None:
            for k,v in row.items():
                if isinstance(v,(Image.Image,dict)) or (hasattr(v,'mode')): col=k; break
        v=row.get(col)
        ob=None
        if isinstance(v,dict) and v.get('bytes'):
            ob=orient_of_bytes(v['bytes']); raw_seen+=1
        elif isinstance(v,dict) and v.get('path') and os.path.exists(v['path']):
            ob=orient_of_bytes(open(v['path'],'rb').read()); raw_seen+=1
        elif hasattr(v,'getexif'):
            # decoded PIL — EXIF usually already gone after datasets decode
            ob=v.getexif().get(ORIENT,1); pil_seen+=1
        else:
            continue
        if ob is None: continue
        cnt[ob]+=1; total+=1
        if ob!=1: bytes_with_tag+=1
    f = bytes_with_tag/total if total else 0
    return dict(repo=repo, split=split, total=total, raw_seen=raw_seen, pil_seen=pil_seen,
                orient_hist=dict(cnt), f_nonidentity=f)

if __name__=="__main__":
    repo=sys.argv[1]; split=sys.argv[2] if len(sys.argv)>2 else "train"
    n=int(sys.argv[3]) if len(sys.argv)>3 else 500
    col=sys.argv[4] if len(sys.argv)>4 else None
    r=scan_dataset(repo,split,n,col)
    print(json.dumps(r,indent=2))

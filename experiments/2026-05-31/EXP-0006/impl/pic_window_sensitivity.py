# Honesty check: how much of CDC's win is PIC's fixed boundary window W?
# Re-run the key cells with W in {0, 32, 64, 256} and p=0.01 (most PIC-favorable).
import math
SEQ=[4000,8000,32000]; RATIOS=[0.001,0.01,0.05,0.25,1.0]
# CDC pct taken from the main run (position-mean), hardcode representative cdc values:
cdc={ (4000,0.001):0.633,(4000,0.01):1.518,(4000,0.05):5.27,(4000,0.25):20.427,(4000,1.0):50.267,
      (8000,0.001):0.533,(8000,0.01):1.419,(8000,0.05):5.175,(8000,0.25):20.347,(8000,1.0):50.217,
      (32000,0.001):0.2,(32000,0.01):1.116,(32000,0.05):4.883,(32000,0.25):20.099,(32000,1.0):50.054}
def pic_pct(S,R,p,W):
    rec=R+min(S,min(W,S)+math.ceil(p*S)); return 100*rec/(S+R)
print(f"{'S':>6} {'inj/seq':>8} | CDC% | PIC p=1% pct & CDC-advantage at W=0/32/64/256")
for S in SEQ:
    for r in RATIOS:
        R=max(1,int(round(r*S))); c=cdc[(S,r)]
        line=f"{S:>6} {r:>8} | {c:5.2f} |"
        for W in [0,32,64,256]:
            pp=pic_pct(S,R,0.01,W); line+=f"  W{W}: {pp:5.2f}%({pp/max(c,1e-9):4.2f}x)"
        print(line)
# what does CDC vs PIC look like if PIC uses W=0 (pure selective, no boundary window)?
print("\n=== PIC with W=0 (selective-only), median advantage ===")
adv=[]
for S in SEQ:
    for r in RATIOS:
        R=max(1,int(round(r*S))); c=cdc[(S,r)]; pp=pic_pct(S,R,0.01,0); adv.append(pp/max(c,1e-9))
import statistics
print("min/med/max CDC advantage vs PIC(p=1%,W=0):",round(min(adv),2),round(statistics.median(adv),2),round(max(adv),2))

# EXP-0027 RESULT — CLAIM-0006 gate-B PATH-2: ORACLE-PIC roofline bound (H100)

**Purpose:** VERDICT-0033 path (2) — answer the "re-impl PIC may be unoptimized" confound by comparing CDC against the THEORETICALLY-BEST PIC (R new + selective p% reused, flash-OPTIMAL, ZERO gather/launch overhead = a fused kernel's best case). If CDC beats this lower bound, it wins vs ANY PIC incl published lmcache.

## RESULT — CDC's advantage is CONDITIONAL vs an oracle/fused PIC (honest, partially-negative)
| seq | inj/seq | oraclePIC/CDC | CDC wins vs oracle? |
|---|---|---|---|
| 8k | 1% | 0.612 | NO (oracle-PIC faster) |
| 8k | 5% | 0.637 | NO |
| 8k | 25% | 1.054 | YES |
| 32k | 1% | 0.966 | NO |
| 32k | 5% | 0.991 | NO |
| 32k | 25% | 1.175 | YES |
- CDC beats the oracle-best PIC in only 2/6 cells — both at HIGH inj/seq (25%).
- At LOW inj/seq (1-5%, which INCLUDES CLAIM-0006's stated win-region inj/seq<=1%!), a fused/oracle PIC
  MATCHES OR BEATS CDC (oraclePIC/CDC 0.61-0.99x).
- WHY: at low inj/seq CDC recomputes a boundary window (R+Wb=256) that the oracle PIC skips (R+selective p);
  CDC's contiguous advantage doesn't overcome the extra rows when injection is tiny.

## INTERPRETATION (vindicates the committee's VERDICT-0033 skepticism)
EXP-0026's "CDC wins all 12 serving cells" was PARTLY an artifact of the re-impl PIC's gather overhead, exactly
as the committee suspected. Against a fused/oracle PIC: CDC's serving advantage HOLDS at high inj/seq but does
NOT survive at low inj/seq (incl the win-region corner). This WEAKENS the unconditional "CDC wins serving"
framing. The honest claim: CDC's contiguous-recompute advantage vs a fused PIC is itself CONDITIONAL on inj/seq
(opposite direction to the recompute-FRACTION win-region — a real, publishable nuance).
CAVEAT: SDPA kernel-level oracle (flash-optimal proxy); a true lmcache CacheBlend measurement would refine the
exact crossover. The boundary-window asymmetry (CDC pays Wb, oracle PIC doesn't) is a modeling choice worth
revisiting — but it is the conservative, PIC-favorable bound the committee requested.

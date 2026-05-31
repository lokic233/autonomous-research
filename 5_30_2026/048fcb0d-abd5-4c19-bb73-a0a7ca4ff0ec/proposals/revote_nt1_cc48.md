You are CC4.8 on a 6-agent committee. You held NT1 ("Mapping-Budget Wall") at YELLOW with 4
specific blockers. We ran follow-up H100 experiments to address each. RAW traces below. Re-vote.
ANTI-COPING: no "novel/promising" without a cited number.

Your 4 blockers and what we measured:

(1) NUMBER INCONSISTENCY (519,936 vs 523,404): RECONCILED. 523,404 = pure single-reservation
alias ceiling (R1/control/E3d-n1, all exactly 523,404). 519,936 = median of B*P across prefix
sizes in old Metric 4b (522,752@1GiB -> 516,096@12GiB); it's slightly below 523,404 because
multi-branch runs ALSO spend VA reservations which draw from the same budget. Headline
standardized to 523,404. Consistent, not contradictory.

(2) "SUPER-LINEAR" RESTED ON n=2: CORRECTED with n=1,2,3 clean sweep (raw):
 n=1: [523404] total 523404
 n=2: [260281,263003] total 523284
 n=3: [171633,174206,177325] total 523164
=> TOTAL CONSERVED at ~523,300 (+/-0.05%), splits EVENLY (~K/n per context). My earlier
   "super-linear degradation (223,215)" was an ARTIFACT of pre-reserving a huge VA range per
   worker (reservations consume the budget); corrected finding is CLEANER: K is a per-device
   descriptor budget, CONSERVED and shared evenly across contexts. MIG implication survives:
   N tenants each get ~K/N (a predictable per-tenant cap).

(4) R2 ACCOUNTING WEIGHT: STATED. R2 = 299,949 maps + 299,950 reserves before OOM => a
reserve+map pair costs ~1.745 budget units vs 1.0 for a bare map. Single per-device pool,
charged at different weights by reserves vs access-grants. Explicit caveat.

(3) RELEVANCE NOT EMPIRICAL: this remains a model (E3c: 64 branches @128k ctx is the binding
cap under CoW sharing). We have NOT run a named agent workload to 64+ concurrent branches on
hardware (that's the 30-day E2E, beyond this measurement round). Honest about scope.

Given the reconciliation, the corrected conserved-per-device result (n=3), and the stated
caveats — re-vote. If your only remaining hold is (3) the empirical-workload demo, note whether
that is a GREEN-gating requirement or a strengthening-but-not-gating item for a characterization
paper whose core claim is the MEASURED ceiling + its conserved per-device structure.

Output EXACTLY:
NT1-CC48:
  Blockers 1,2,4 resolved by the new traces? (per-item YES/NO):
  Is remaining item (3 empirical workload) GREEN-gating for a CHARACTERIZATION paper? (YES/NO + 1 line):
  VERDICT: RED | YELLOW | GREEN
End with EXACTLY: "NT1=<verdict>"

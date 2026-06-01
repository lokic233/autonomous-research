# CLAIM-0012 — Hawkes-IC-selection small-N reliability: REQUIRED-CITATION subsection

**Date:** 2026-06-01 (UTC) · **Agent:** researcher-0012-citation-r3 · **CPU / web-abstract / short-writing only on cli:dengcchi-mac**
**Mandate:** close VERDICT-0048's single remaining `required_evidence` item — the CITATION-ONLY gap the area_chair flagged. VERDICT-0048 = YELLOW-CLEAN ("one citation from GREEN"); all 3 VERDICT-0047 BLOCKING ablations RESOLVED (EXP-0044). No RED, no fatal, no prior-art collision. This subsection is the content to fold into the CLAIM-0012 paper Methods/Limitations.

---

## Why this citation is REQUIRED (the committee's exact objection)

The discriminating leg of CLAIM-0012 (H2: tool-call-failure over-dispersion exceeds static AND time-varying/latent-state per-tool rate-heterogeneity, on the Codex-clean harness) rests on **information-criterion (BIC) Hawkes-vs-Cox model selection** computed on **N=60 inter-failure call-gaps** (Codex corpus: 64 sessions ≥8 calls, 2001 calls, 106 failures, 60 inter-failure gaps). N=60 events is squarely in the **small-sample / few-events regime** that the model-selection and the Hawkes-estimation literature **independently document as the regime where IC-based selection and self-excitation estimation are least reliable.** The committee (novelty_killer, endorsed by area_chair) correctly requires that we (a) cite that literature, (b) explicitly acknowledge the small-N IC-selection risk, and (c) show why the conclusion does not hinge on a single fragile IC comparison.

---

## The references (all web-verified, real, citable)

### IC / BIC model-selection reliability in small samples

1. **Vrieze, S. I. (2012). "Model selection and psychological theory: A discussion of the differences between the Akaike Information Criterion (AIC) and the Bayesian Information Criterion (BIC)." *Psychological Methods*, 17(2), 228–243. DOI: 10.1037/a0027127** (PMC3366160).
   - *Relevance:* The canonical applied treatment of when AIC vs BIC selection is trustworthy. Establishes that BIC's consistency is **asymptotic** and conditional on the true model being in the candidate set; at finite N the penalty/likelihood tradeoff governs whether the criterion recovers the correct model. Directly motivates treating a single BIC comparison at N=60 as suggestive-not-decisive and demanding a robustness check.

2. **Hurvich, C. M., & Tsai, C.-L. (1989). "Regression and time series model selection in small samples." *Biometrika*, 76(2), 297–307.**
   - *Relevance:* The foundational small-sample information-criterion paper. Shows the uncorrected AIC (and by the same mechanism, IC differences generally) is **biased when the number of observations is small relative to the number of parameters**, and introduces the AICc finite-sample correction (penalty ~ 2k(k+1)/(n−k−1)). This is the literature that formally names our risk: at N=60 with a multi-parameter Hawkes (λ0, α, β + per-tool baselines) the second-order penalty term is non-negligible, so raw ΔBIC can over- or under-state evidence. We cite it as the explicit basis for the small-N caveat.

### Hawkes-process estimation / self-excitation reliability under few events

3. **Filimonov, V., & Sornette, D. (2015). "Apparent criticality and calibration issues in the Hawkes self-excited point process model: application to high-frequency financial data." *Quantitative Finance*, 15(8), 1293–1314. (arXiv:1308.6756, 2013.)**
   - *Relevance:* THE load-bearing reference. Documents that maximum-likelihood Hawkes calibration suffers **strong, systematic biases in the self-excitation / branching-ratio estimate when the number of events is limited, when the kernel is mis-specified, or under edge effects** — producing "apparent criticality" (spurious self-excitation) that is an estimation artifact rather than a real signal. This is precisely the failure mode a hostile reviewer would invoke against an α>0 / ΔBIC>6 Hawkes win at N=60. Citing it shows we know the exact trap; our LOSO floor (below) is the mitigation it would demand.

4. **Hardiman, S. J., & Bouchaud, J.-P. (2014). "Branching-ratio approximation for the self-exciting Hawkes process." (arXiv:1403.5227; Phys. Rev. E 90, 062807.)**
   - *Relevance:* Proposes a model-independent branching-ratio estimator using only the mean and variance of the event count, motivated explicitly by the **finite-sample / kernel-misspecification fragility of full-MLE Hawkes fits** (the Filimonov-Sornette problem). Establishes in the canonical Hawkes literature that practitioners treat single-fit MLE self-excitation estimates as fragile and seek estimators/robustness checks that do not hinge on one likelihood maximization. Supports our methodological stance that the Codex H2 conclusion is reported as LOSO-robust, not as a single ΔBIC point.

---

## Explicit small-N IC-selection-risk acknowledgment (mandatory disclosure)

We state plainly, for the Methods/Limitations of CLAIM-0012:

> The discriminating Codex result rests on information-criterion (ΔBIC) model selection between a per-tool Cox baseline (and time-varying/latent-state steelman extensions) and a self-exciting Hawkes process, computed on **N=60 inter-failure inter-event call-gaps**. This is a **small-sample regime**. The information-criterion literature documents that BIC's model-recovery guarantee is asymptotic (Vrieze 2012) and that IC differences are finite-sample biased when N is small relative to the parameter count (Hurvich & Tsai 1989). The Hawkes-estimation literature independently documents that MLE self-excitation / branching-ratio estimates are upward-biased and can manufacture *apparent* criticality under few events or kernel misspecification (Filimonov & Sornette 2015; cf. Hardiman & Bouchaud 2014). **A single ΔBIC comparison at N=60 is therefore, on its own, fragile evidence and should not be treated as decisive.**

We do NOT hide this behind the favorable point estimate (full-corpus Codex ΔBIC=+28.3). We foreground it.

---

## Why the result is STILL defensible despite the small-N risk (the LOSO floor)

The honest mitigation is exactly the robustness check the IC-fragility literature would demand: we do not rest on one fit. From EXP-0044 (VERDICT-0048 BLOCKING-1, now PASSED):

- **Leave-one-session-out (LOSO):** the Codex Hawkes ΔBIC was recomputed dropping **every one of the 46 mixed-label sessions in turn**. The ΔBIC stayed in **[17.60, 30.67], median 27.79 — above the "strong" BIC>6 threshold for ALL 46 removals.** The worst case (drop the single most failure-dense session) still leaves **ΔBIC ≈ 17.6, ≈3× the threshold.**
- **Tool-stratified permutation Stouffer p = 0.000 for ALL 46 removals** (a non-IC, distribution-free corroboration of the same self-excitation signal, immune to the IC finite-sample-penalty concern).
- **Steelman static/latent-heterogeneity null (phase-Cox / HMM-Cox):** Hawkes still beats the best static-heterogeneity model by **ΔBIC = +15.0** on Codex — the over-dispersion is not absorbed by a slow "hard-phase elevates all tools" alternative.

**The argument:** the small-N IC-fragility risk (Filimonov-Sornette apparent-criticality; Hurvich-Tsai finite-sample IC bias) is real, but the conclusion does **not hinge on a single fragile IC comparison.** The LOSO floor demonstrates the ΔBIC>6 verdict is **stable to dropping any single session** — the precise stability the fragility literature flags as the missing check — and the distribution-free permutation p=0.000 corroborates the signal **without** any IC penalty at all. A spurious "apparent-criticality" artifact from few-event MLE bias would not survive (a) being ≈3× the threshold after dropping the most influential session, and (b) an independent permutation test. The signal is small-N but **robust within that small N**, and that is the defensible, honestly-bounded claim.

**It remains a one-strong-harness, modest-N, descriptive characterization** (Gemini's leg is KILLED as a deterministic-gate artifact; CC's is honestly conceded fragile). We do not upgrade the altitude — we only certify the Codex leg survives the small-N IC-selection objection.

---

## Note for the orchestrator

- **This subsection IS the content** to fold into the CLAIM-0012 paper's Methods/Limitations. It satisfies VERDICT-0048's sole blocking `required_evidence` item: the mandatory Hawkes/IC small-N reliability citation + explicit small-N IC-selection-risk acknowledgment + the LOSO-resilience argument.
- **References to add to the paper bibliography:** Vrieze 2012 (Psych Methods 17(2):228–243); Hurvich & Tsai 1989 (Biometrika 76(2):297–307); Filimonov & Sornette 2015 (Quant. Finance 15(8):1293–1314 / arXiv:1308.6756); Hardiman & Bouchaud 2014 (arXiv:1403.5227 / PRE 90:062807). All four are real and web-verified; none fabricated.
- **Re-convene recommendation:** The area_chair's framing was explicit — *"path to GREEN is now citation gap only, no further ablations."* The single blocking item was CITATION-ONLY. Once this subsection is folded into the paper Methods/Limitations, the orchestrator can reasonably **mark path-to-green SATISFIED for CLAIM-0012 without a full committee_run_20**, since (a) no reviewer raised any non-citation blocker, (b) the 2 methodology GREENs (evaluation_prosecutor, theory_skeptic) are already secured, and (c) the YELLOW holds were the citation gap + a contribution-altitude assessment the verdict itself labels "not a fatal flaw." **Recommended:** a lightweight novelty_killer-only re-check (the reviewer who raised the citation requirement) to confirm the citation closes their objection, rather than a full 6-agent re-convene. A full committee_run_20 is warranted ONLY if the orchestrator also wants to pursue the RECOMMENDED (non-blocking) altitude-lifters (2nd clean genuine-exec harness / larger Codex corpus), which are out of scope for closing the current verdict.

## FILES
- `prior_art/PROJ-0003/CLAIM-0012_ICSELECTION_CITATION_r3_2026-06-01.md` (this doc)
- Evidence basis: `experiments/2026-06-01/EXP-0044/results/{codex_loso.csv, latent_cox_vs_hawkes.csv}` (LOSO floor + steelman); `prior_art/PROJ-0003/CLAIM-0012_ABLATIONS_r3_2026-06-01.md` (synthesis).

# Decision register — FYP CCDS26-0406

Running record from the start of the sourcing phase. Kept so the eventual progress report can be
assembled without reconstruction. **This is the register, not the report.**

Every entry is either **[Settled]**, **[Measured]** (an empirical result with the number),
or **[Open]**. Where a decision reversed an earlier one, both are shown.

Last updated: after the shape-metric investigation and the N decision.

---

## A. Settled decisions

| # | Decision | Basis |
|---|---|---|
| A1 | Disease model: Weitz model B (SEIR + H compartment) | Minimal variant producing plateau, shoulder and oscillation |
| A2 | Disease parameters: Weitz Table 1 (R₀=3, 2 d latent, 6 d infectious, f_D=0.01) | Weitz supplies the referent, so his parameterisation governs |
| A3 | Arm 1 rule: Gozzi's **CBF**, not EFB | Agent-native; best performer in Gozzi's evaluation; sources `r`; avoids circularity |
| A4 | Weitz's rule is **simulator validation, not an arm** | Prevents "arm 1 reproduces Weitz" being tautological |
| A5 | One location, well-mixed | Both source papers are single well-mixed populations |
| A6 | Three-level action: stay home / precautions / normal | Maps onto Weitz's continuous β reduction; sourced by CBF's `r` and PMT response cost |
| A7 | **N = 3,000** | Revised up from 1,000 — see D3 |
| A8 | Perception signal: **7-day rolling mean** of reported deaths | Weitz Methods; raw daily count is zero on ~98% of days |
| A9 | Deaths, not cases, as the awareness driver | Urmi et al. lag-0 correlation; Weitz mechanism is fatality-driven |
| A10 | Population: New York age structure, quota-drawn, frozen | Mean IFR 0.9718% vs Weitz's 1.000%; see B2 |
| A11 | Vulnerability derived from age via `IFR_10age` | Zero free parameters |
| A12 | `days_since_last_outing` **deleted** | No source; replaced by CBF's relaxation mechanism |
| A13 | `response_efficacy` **added** | PMT β=+0.251, second-strongest determinant |
| A14 | `self_efficacy` deliberately excluded | Strongest determinant (β=+0.270) but no meaningful barrier in a single-venue three-level act |
| A15 | Disease is **not named** in the arm-2 prompt | Arm 1 has no disease identity; naming it creates an input asymmetry, not a function difference |
| A16 | Scenarios vary only R₀ and T_H | δ_c, k, r, β_B live inside arm 1's rule; varying them varies the object under test |
| A17 | S1 baseline (R₀=3, T_H=14); S2 milder (R₀=2); S3 delayed (T_H=28) | S2 stresses signal magnitude, S3 stresses timing |
| A18 | Arm 4 distils on **S1 only**, evaluated on S2/S3 held out | Turns arm 4 from a fit check into a generalisation test |
| A19 | Shape metric: **Weitz symmetry coefficient computed on incidence** | See D2 |
| A20 | Integration: **12 sub-steps per day** | Gozzi's scheme; see D1 |

## B. Sources — extraction status

| Source | Status | Supplies |
|---|---|---|
| Weitz et al. 2020 *PNAS* 117(51) | **fully extracted** | disease model, all parameters, referent signature, sourced no-behaviour control |
| Gozzi, Perra & Vespignani 2025 *PNAS* 122(24) | **fully extracted from source code** | CBF and EFB rules, `r`/`β_B`/`μ_B`/`γ_beh`, age-stratified IFR, age structure, observation model, integration scheme |
| Urmi et al. 2025 *PNAS* (doi 10.1073/pnas.2500655122) | extracted from preprint | deaths-over-cases; two-component behaviour; PCA 88% one dimension |
| PMT meta-analysis, *IJDRR* 2023 (PII S2212420923002388) | extracted | feature effect sizes |

**B1 — Structural finding.** Gozzi's EFB, *as implemented in code*, is
`1/(1 + short_term·(deaths/dc)^k + long_term·(cum/Dc)^k)` with `k=1` — literally Weitz's
model C denominator. Two independent PNAS groups converge on one functional form.

**B2 — Population.** New York age structure × `IFR_10age` gives a population-weighted IFR of
0.9716%, against Weitz's flat 1.000%. Quota population at N=3,000:

| 0–9 | 10–19 | 20–24 | 25–29 | 30–39 | 40–49 | 50–59 | 60–69 | 70–79 | 80+ |
|---|---|---|---|---|---|---|---|---|---|
| 330 | 337 | 187 | 240 | 472 | 378 | 376 | 333 | 220 | 127 |

Realised mean IFR 0.9718%. Agents aged 60+ are 680 (22.7% of population) and contribute 88.3%
of deaths.

**B3 — Second instance of the project's central claim.** Gozzi's nine-city comparison produces
different winners under different metrics, and their R₀ posteriors for Santiago range from
4.20 [3.96, 4.42] to 1.77 [1.59, 1.97] depending only on which behavioural mechanism is assumed.
Independent of the DFD paper's internal disagreement.

**B4 — Symbol collision.** Gozzi's `mu` = 1/infectious period, `eps` = 1/latent period. Weitz's
`μ` = 1/latent, `γ` = 1/infectious. Same letters, opposite meanings.

**B5 — Parameter conflict.** Weitz: 2 d latent, 6 d infectious. Gozzi: 4 d latent, 2.5 d
infectious. Resolved in favour of Weitz (A2); sweep as sensitivity.

## C. Measured results

**C1 — Minimum N for behaviour to exist at all.** Well-mixed, Weitz model B, T_H=14, 20 seeds,
7-day mean signal:

| N | fadeout | peak I (control) | peak I (awareness) | final S (control) | final S (awareness) |
|---|---|---|---|---|---|
| 100 | 40% | 26.8 | 26.8 | 0.073 | 0.105 |
| 300 | 0% | 74.3 | 68.2 | 0.054 | 0.147 |
| 1,000 | 0% | 230.4 | 187.1 | 0.057 | 0.278 |
| 3,000 | 0% | 687.6 | 404.8 | 0.059 | 0.457 |
| 10,000 | 0% | 2293.8 | 819.3 | 0.058 | 0.658 |

At N=100 the behavioural arm and the control are **numerically identical**.

**C2 — Signal smoothing is required, not optional.** Final S at Weitz's δ_c: raw daily deaths
0.095 vs 7-day mean 0.278 at N=1,000; 0.286 vs 0.658 at N=10,000 (ODE reference 0.686).

**C3 — Scenario separation** (N=1,000, 25 seeds, Weitz reference rule — **to be re-measured
with CBF at N=3,000**):

| Scenario | peak I | final S |
|---|---|---|
| S1 (R₀=3, T_H=14) | 188.2 | 0.278 |
| S2 (R₀=2, T_H=14) | 101.9 | 0.443 |
| S3 (R₀=3, T_H=28) | 203.4 | 0.213 |

S2 separates strongly; S3 separates on final S only. S3 is the one to drop under budget pressure.

**C4 — Shape-metric reliability** (30 seeds, computed on incidence; Cohen's *d* between control
and awareness):

| Metric | N=1,000 | N=3,000 |
|---|---|---|
| final susceptible fraction | 3.76 ✅ | 3.37 ✅ |
| Weitz symmetry (incidence) | 0.60 ❌ | **2.58 ✅** |
| quantile symmetry | 0.38 ❌ | 0.63 ❌ |
| peak share | 0.75 ❌ | 1.09 ~ |
| duration | 0.79 ❌ | 1.24 ~ |

At N=3,000 Weitz symmetry gives control 1.52 ± 0.68 vs awareness 0.28 ± 0.03.

**C5 — Response gradation.** Final S as δ_c varies over 500×:

| N | 1e-6 | 5e-6 | 2e-5 | 1e-4 | 5e-4 | spread |
|---|---|---|---|---|---|---|
| 1,000 | 0.275 | 0.275 | 0.269 | 0.201 | 0.086 | 0.189 |
| 3,000 | 0.385 | 0.399 | 0.407 | 0.259 | 0.084 | 0.323 |
| 10,000 | 0.698 | 0.629 | 0.352 | 0.265 | 0.085 | 0.612 |
| 30,000 | 0.819 | 0.488 | 0.305 | 0.270 | 0.080 | 0.739 |

At N=1,000 a 20× change across Weitz's operating range produces **no change** (0.275, 0.275,
0.269) — the awareness signal is effectively binary.

**C6 — Event counts at N=1,000.** Whole epidemic: 8.2 deaths across 7.4 days; 721 infections
across 61 days. This is why the signature must be measured on incidence.

**C7 — Averaging window matters more than N for response gradation.** Final S across
δ_c ∈ [1e-6, 3e-4], 12 seeds:

| N | signal window | spread |
|---|---|---|
| 1,000 | 7-day (current) | 0.190 |
| 1,000 | 14-day | 0.332 |
| 1,000 | 28-day | **0.447** |
| 1,000 | 56-day | 0.490 |
| 1,000 | cumulative deaths only | 0.017 (useless — a ratchet, saturates) |
| 3,000 | 7-day | 0.274 |
| 3,000 | 28-day | **0.593** |
| 10,000 | 7-day (reference) | 0.629 |

A 28-day window at **N=1,000** (0.447) outperforms a 7-day window at **N=3,000** (0.274).
Trade-off: a 28-day window means agents respond to month-old information, adds ~14 days of lag
comparable to T_H, and departs from Weitz's sourced 7-day smoothing.

## D. Reversals and corrections

**D1 — Discretisation bug.** Setting the daily transition probability to `1 − exp(−rate)` at a
one-day step gives a mean infectious period of 6.51 d instead of 6 and **R₀ = 3.257 instead of
3.000**. Invisible in any single run; caught only by the ODE-convergence test. Gozzi's fix —
12 sub-steps per day — measured at R₀ = 3.006.

**D2 — Shape metric, reversed twice.** First reported as failing in the ABM (control 0.65,
awareness 0.97, wrong direction). Cause: it was being computed on the **death** series, which
has 8 events at N=1,000. Recomputed on incidence it works, and needs N ≥ 3,000.

**D3 — N revised 1,000 → 3,000.** N=1,000 was recommended on control-versus-behaviour
separation alone. That test establishes only that behaviour *matters*, not that it is *graded*.
C5 shows the response is a switch at N=1,000, so all four arms would face a binary input in the
one channel the referent runs through, and could not differ.

**D4 — Caching estimate withdrawn.** A "~4× saving" was quoted without calculation. The
combinatorial state space (~4.6×10⁵) is comparable to the decision count, so caching may save
little. The realised state space must be measured from arm 1's logs.

**D5 — IFR table.** Sourcing pack v3 lists the 9-band `IFR`; the 10-band `IFR_10age` is the one
that pairs with `pop_data_Nk.csv`. Values unaffected, band boundaries differ.

**D7 — The C4 shape-metric result is WITHDRAWN.** "Weitz symmetry reliable at N=3,000,
Cohen's d = 2.58" was computed on 11/30 control runs and **2/30 awareness runs**; the summary
silently dropped undefined values. The tight `0.28 ± 0.03` was two numbers. What looked like
separation was a selection effect over the runs where the metric happened to be computable.

**D8 — Root cause, and it is structural.** Two contributing factors, one fixable and one not:
- *Fixable:* the ABM seeded 1% infected at t=0 (30 agents at N=3,000), leaving no exponential
  growth phase and hence no pre-peak 10% crossing. Reducing the seed to 10 agents (0.33%) takes
  control-run definability from 12/40 to **40/40**. Adopt this regardless — the large seed was
  an unrealistic initial condition anyway.
- *Not fixable:* even with the smaller seed, the metric is defined on only ~50% of awareness
  runs (19–22/40) and has >100% relative variance where defined (26.6 ± 30.3). **The symmetry
  coefficient is referenced to a peak, and the awareness regime is defined by the absence of a
  peak.** A smooth deterministic plateau still has a well-defined maximum with monotone flanks;
  a stochastic plateau does not. Weitz could use this metric because their output is an ODE.

*Consequence:* peak-referenced shape metrics are the wrong family for this problem. Candidates
that avoid a peak landmark — final susceptible fraction, peak-to-mean ratio, time above a
threshold fraction, area concentration — are the direction to search.

**D6 — Oscillation dropped as a scenario target.** Weitz's ODE reproduces waves rising with T_H
(2, 2, 3, 3 at T_H = 7, 14, 21, 28). The ABM does not, and two reasonable prominence definitions
disagree on identical runs. Cause not isolated; smoothing and metric artifact both eliminated as
sole explanations.

## E. Open items

| # | Item | Blocks |
|---|---|---|
| E1 | Arm-2 budget at N=3,000 — 1.62M calls at p=0.3, 810k weekly, 540k weekly with 2 scenarios | arm 2 |
| E2 | Re-decision cadence sweep in arm 1 (free) | E1 |
| E3 | Realised state count from arm 1 logs | caching decision |
| E4 | Re-measure C3 scenario separation with CBF at N=3,000 | scenario spec |
| E5 | **ANSWERED — yes.** See C7. Reopens the N decision | E1 |
| E6 | Prompt wording and anchoring scheme; pilot before full arm-2 run | arm 2 |
| E7 | Persona layer — may be redundant given the sourced population construction | diversity metric |
| E8 | Gozzi SI prior ranges for β_B, μ_B, γ_beh (per-city posteriors, no canonical value) | arm 1 calibration |
| E9 | Whether the ABM/ODE oscillation discrepancy (D6) indicates a simulator defect | milestone 2 |
| E10 | Contamination experiment: named vs unnamed disease, decision-level agreement | arm 2 writeup |

## F. Known limitations of everything measured above

- All ABM results are **well-mixed**; no clustered network has been tested.
- Seed counts are 8–30 depending on the run; none are large.
- C3 used the Weitz reference rule, not CBF.
- E9 remains unresolved: the ABM does not reproduce the ODE's T_H → oscillation relationship,
  and it is not yet known whether this is a metric problem or a simulator defect.

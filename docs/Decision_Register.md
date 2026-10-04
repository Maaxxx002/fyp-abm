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
| A7 | **N = 3,000** | Revised up from 1,000 — see D3. Reaffirmed after C13's small-N/small-count viability concern was resolved (not the operative mechanism) — see D13/C20. **Reaffirmed again (A30)** after N=1,000 failed the pre-set C26/C27 decision rule |
| A8 | Perception signal: **28-day rolling mean** of reported deaths | C7 — a 7-day window leaves the response ungraded at N ≤ 3,000. Smoothing itself is sourced to Weitz Methods; the 28-day length is a stated finite-population correction, not a behavioural claim |
| A9 | Deaths, not cases, as the awareness driver | Urmi et al. lag-0 correlation; Weitz mechanism is fatality-driven |
| A10 | Population: New York age structure, quota-drawn, frozen | Mean IFR 0.9718% vs Weitz's 1.000%; see B2 |
| A11 | Vulnerability derived from age via `IFR_10age` | Zero free parameters |
| A12 | `days_since_last_outing` **deleted** | No source; replaced by CBF's relaxation mechanism |
| A13 | `response_efficacy` **added** — **implemented**, wired into CBF's `r` (`r_i = 1 - response_efficacy_i`). **The wiring into `r` is superseded by A29**; the field itself is retained | PMT β=+0.251, second-strongest determinant; wiring and its unsourced-mapping caveat recorded in C21 |
| A14 | `self_efficacy` deliberately excluded | Strongest determinant (β=+0.270) but no meaningful barrier in a single-venue three-level act |
| A15 | Disease is **not named** in the arm-2 prompt | Arm 1 has no disease identity; naming it creates an input asymmetry, not a function difference |
| A16 | Scenarios vary only R₀ and T_H | δ_c, k, r, β_B live inside arm 1's rule; varying them varies the object under test |
| A17 | S1 baseline (R₀=3, T_H=14); S2 milder (R₀=2); S3 delayed (T_H=28) | S2 stresses signal magnitude, S3 stresses timing |
| A18 | Arm 4 distils on **S1 only**, evaluated on S2/S3 held out | Turns arm 4 from a fit check into a generalisation test |
| A19 | Shape metric: **Weitz symmetry coefficient computed on incidence** | See D2 |
| A20 | Integration: **48 sub-steps per day** (revised from 12 — see C9) | Gozzi's own default (`daily_steps=12` — verified in their source: `compartment_model_age_deaths.py`, `function_model_age_deaths.py`, `mobility_model_age.py`, all `dt=1/12`) is insufficient for this model's precision; see C9 |
| A21 | Initial infected: **10 agents** (0.33% at N=3,000) | D8 — a 1% seed removes the exponential growth phase entirely |
| A22 | Repo `fyp-abm` is the build artefact; `docs/` holds the four specs and is authoritative | Claude Code sessions read `CLAUDE.md` + `docs/` |
| A23 | "Stay home" is **two-sided**: an agent who stays home neither catches nor spreads that day, so the population multiplier is (1−q)² | Formalises the assumption already baked into `q = 1 − (1+(δ/δ_c)^k)^(−1/2)` (CLAUDE.md Test 2 / Sourcing_Pack_v3.md's "Test 3" open point) — recorded as decided, not just assumed |
| A24 | Awareness signal **stays the 28-day rolling mean** (A8 reaffirmed). Gozzi's literal one-day (yesterday's deaths) signal is **rejected** | [Decision, planning chat (Max), C23] With the real CBF mechanism at N=3,000 the one-day signal fails mean-field agreement: 17.07% relative error, −9.13 SEM (90 seeds). Supersedes C16's `direct-g`-based evidence for the same question |
| A25 | Death reporting: **detection_rate = 0.7 applied as a plain multiplier on realised deaths, NO integer truncation** | [Decision, planning chat (Max), C23] Deliberate deviation from Gozzi's code (`compartment_model_age_deaths.py:152`, `.astype(int)` per age group per day). At N=3,000 the truncation leaves agents seeing 6.7% of realised deaths instead of 70%, peak S^B falls from ~567 to 89, and behaviour fails pass mark (a). Treated as a city-scale bookkeeping artefact, not mechanism. Sourcing Pack v3 (observation-model section) records the formula as detection_rate x Binomial(...) without truncation; this has not been checked against the paper's text. Detection affects only what agents perceive, never recorded deaths. No Δ delay added (H/T_H already supplies it) |
| A26 | Mortality: **per-agent f_D = IFR_10age[age_band]** (population mean 0.009718), replacing A2's flat 0.01 for the model runs | [Decision, planning chat (Max), C23] Gozzi's age-based IFR adopted; the DDE reference uses the population-weighted mean, exact in expectation while r is shared (C23) |
| A27 | **[SUPERSEDED by A31]** **Pass mark (b) rule, fixed for all future steps:** FAIL only if relative error > 6% AND gap > 2 SEM. Relative error > 6% with gap ≤ 2 SEM is **INCONCLUSIVE** → re-run that config at 90 seeds and apply the same rule. Applies identically to every config | [Decision, planning chat (Max), C23] At N=3,000 / 30 seeds, 1 SEM of final S is ~6.8% of the reference, wider than the 6% band itself (C23: config 2 read 13.12% / +1.93 SEM at 30 seeds, 1.52% / +0.47 SEM at 90) |
| A28 | **Pass mark (a), unchanged:** lower peak I and higher final S than the config's own no-behaviour control, each by > 2 SEM of the paired (same-seed) difference | [Decision, planning chat (Max), C23] |
| A29 | **Arm-level physics uses flat r = 0.5 for all agents** (Gozzi). `response_efficacy` is **retained as a Perception field** available to all arms as a decision input; arm 1 (CBF) ignores it, as Gozzi's original does. Applies to arms 2–4 too: Act must be identical across arms | [Decision, planning chat (Max), C24] The PMT construct is sourced as a determinant of protective-behaviour ADOPTION (Think), not of protective EFFECTIVENESS (Act); the C21 mapping `r_i = 1 − response_efficacy_i` is unsourced and conflated the two. C24 measured that mapping's effect as +0.0101 final S (+9.47 SEM, n=90) at N=3,000 — recorded as the measured cost of the removed modification. Supersedes A13's wiring and C21's mapping |
| A30 | **N stays 3,000** (A7 reaffirmed); N=1,000 rejected | [Decision, planning chat (Max), C26/C27] N=1,000 fails the pre-set C26/C27 decision rule on pass mark (a): at γ_beh=0.5 and in S3 the peak-I reduction is not detectable at 30 seeds (−1.92 and −1.75 SEM). Detecting the effect at N=1,000 would need ~3× the seeds, which removes the arm-2 cost saving (N=1,000 × 90 seeds ≈ N=3,000 × 30 seeds in agent-days). This also closes the gap that N was originally chosen under the old 7-day window (C5/C7/D3): it is now re-checked with the real CBF mechanism and the 28-day window. Limitation: the 7-day window itself was not re-tested under CBF (section F) |
| A31 | **Pass mark (b) rule, REVISED (supersedes A27):** the 30-seed run is a SCREEN only. A config at ≤ 6% relative error at 30 seeds PASSES. Any config > 6% at 30 seeds (whether A27 would have called it FAIL or INCONCLUSIVE) is re-run at 90 seeds, and the 90-seed result is the verdict: FAIL if relative error > 6% AND gap > 2 SEM at 90 seeds, otherwise PASS | [Decision, planning chat (Max), C26/C27] **This rule was revised AFTER observing the pattern below, not fixed in advance.** Under A27 both C26/C27 FAILs were borderline (~2.1 SEM) and vanished at 90 seeds. All five N=3,000 points re-run at 90 seeds moved toward the DDE: seeds 0–29 run high, and the configs share seeds, so their 30-seed errors are correlated, not independent. With 20+ configs per step, false FAILs at a 2-SEM line are expected. Re-scored in C28 |
| A32 | **Run length stays 600 days for production** runs, pending C28's day-600 check. **900 days remains the convention for mean-field (DDE) reference comparisons** | [Decision, planning chat (Max)] C23–C27 ran at 900 days for comparability with C18 |

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

**C8 — Test 1 under the 12-substep scheme.** N=100,000, 10/10 seeds, behaviour off, 900 days:
mean final S = 0.05801 vs ODE target 0.0594 (2.34% relative error); implied R0 = 3.0225
(per-seed mean 3.0226 ± 0.0124). [Speculation, high confidence] SEM ≈ 0.0124/√10 ≈ 0.0039; the
0.0226 gap from R0=3.0000 is ~5.8 SEMs, too large to attribute to sampling noise alone. Likely a
small residual bias from discretisation error compounding across the E→I→H→D chain (three
sequential sub-stepped transitions), distinct from the single-transition check in D1 that gave
3.006. Not yet distinguished from an implementation issue — see E15.

**C9 — Substep convergence, resolved.** N=100,000, 30/30 seeds, behaviour off, 900 days
(ODE reference final S = 0.05952 at R0=3.0000 exactly):

| substeps | mean final S | implied R0 | R0 std | SEM | gap (SEM units) |
|---|---|---|---|---|---|
| 12 | 0.05807 | 3.0216 | 0.0150 | 0.0027 | 7.92 |
| 24 | 0.05858 | 3.0140 | 0.0144 | 0.0026 | 5.30 |
| 48 | 0.05955 | 2.9997 | 0.0183 | 0.0033 | **-0.08** |

Gap shrinks monotonically (7.92 → 5.30 → -0.08) and is statistically indistinguishable from
zero at 48 — confirms genuine discretisation bias shrinking as dt→0, rules out an
implementation bug. In relative-error terms: 12 substeps → 2.44% (fails even the old 2%
tolerance), 24 → 1.58% (fails 1%), 48 → 0.05% (passes 1% comfortably). **A20 revised: 48
sub-steps/day, not Gozzi's default of 12.** Gozzi's own model has one fewer sequential
sub-stepped compartment (no H/death-delay chain), so their published default does not carry
enough precision for this model's extra compartment. Convergence order not identifiable from
3 points (bias drops 35% then far more than either O(dt) or O(dt²) predicts — seed noise
contributes at 48), but not needed for the decision: 48 clears the tolerance with margin.

**C10 — Test 1 closed against `src/model.py`.** Repointed from the `experiments/abm.py` pilot
(G2 resolved) with the tolerance tightened 2% → 1% (G1 resolved). N=100,000, 30/30 seeds,
days=900, behaviour off: mean final S = 0.05926 vs ODE target 0.05952 — **0.431% relative
error**. Pass, with roughly 2.3× margin under the 1% gate.

**C11 — Mean-field recovery re-run at full Test 2 scale (N=100,000, 30/30 seeds, days=900, 48
sub-steps/day; `src/model.py`'s `run_weitz_behaviour` fixed to δ(t)=γ_H·H(t), continuous,
recomputed every sub-step, zero lag — D10's fix, now actually applied in `src/`, not just the
`experiments/verify_meanfield_delta_bug.py` diagnostic). ODE reference final S = 0.52502.
`experiments/meanfield_recovery_fullscale.py`, raw output in
`results/meanfield_recovery_fullscale.json`:

| Variant | seeds used | mean final S | relative error | gap in SEMs |
|---|---|---|---|---|
| a. direct-g (deterministic, no per-agent draws) | 30/30 | 0.50105 | 4.56% | −7.11 |
| b. continuous-q (two-sided, redrawn every sub-step — what `src/model.py` implements) | 30/30 | 0.50331 | 4.13% | −6.62 |
| c. daily-q (two-sided, decided once/day — original spec cadence) | 30/30 | 0.49401 | 5.91% | −8.05 |

All three are 6.6–8.1 SEMs below the ODE — statistically real at this scale, not sampling
noise, and **all three land outside even Test 1's 1% tolerance and outside the 2% tolerance
`tests/test_meanfield_recovery.py` currently states.** See D11 for why this contradicts the
5-seed diagnostic, and E16 for the consequence.

**C12 — δ_c sweep confirms the small-H-count hypothesis (D11).** Isolated to the deterministic
`direct-g` variant only (no per-agent draws, no q, no cadence question — cleanest signal),
N=100,000, 30/30 seeds, days=900, 48 sub-steps/day, `experiments/meanfield_deltac_sweep.py`,
raw output `results/meanfield_deltac_sweep.json`. ODE reference recomputed separately for each
δ_c (not reused from C11):

| δ_c | mean peak H (agents) | ODE final S | ABM mean final S | relative error | gap in SEMs |
|---|---|---|---|---|---|
| 0.5 (baseline, C11) | 23.0 | 0.52502 | 0.50105 | 4.56% | −7.11 |
| 2.0 | 66.5 | 0.29368 | 0.29399 | 0.10% | 0.26 |
| 3.5 | 104.8 | 0.27850 | 0.27810 | 0.14% | −0.36 |
| 7.0 | 172.5 | 0.25146 | 0.25347 | 0.80% | 2.23 |

**The bias collapses as δ_c grows: 4.56% → 0.10% → 0.14% → 0.80%, and only δ_c=0.5's gap is
large in SEM terms (the rest are within ~2 SEMs of zero).** [Fact] This confirms D11's
speculation: at δ_c=0.5 the behavioural throttle is being driven by an H-compartment stock that
peaks around 23 agents out of N=100,000 — small enough that the ABM's discrete, stochastic H(t)
diverges materially from the ODE's continuous H(t) feeding the same nonlinear g(·). At δ_c≥2.0,
where peak H is in the tens-to-hundreds, the discrepancy is gone. Note the measured peak H
values (23, 66.5, 104.8, 172.5) run noticeably higher than D11's naive threshold approximation
H≈δ_c·T_H (7, 28, 49, 98) — the epidemic overshoots the point where δ=δ_c before the throttle
turns it over, roughly by a factor of ~2–3×, so use the measured peak-H figures, not the naive
approximation, going forward. **Not yet done this round (deliberately — one variable isolated at
a time):** re-checking whether the two-sided `q` variants (continuous-q, daily-q) show the same
collapse at larger δ_c; whether Weitz's own N=10,000,000/δ_c=50 regime (peak H order ~10⁴–10⁵)
would ever hit this regime at all, versus it being an artifact specific to rescaling δ_c down for
smaller N; and what, if anything, this implies for Test 2's tolerance or for arm 1/2's actual
operating δ_c (register-sourced, not free to change on this basis alone). Reported, not decided.

**C13 — Arm 1's own trigger constant (CBF's γ_beh, not Weitz's δ_c) checked against N=3,000, the
project's actual settled population — higher priority follow-up to C12.**
`experiments/cbf_gamma_beh_scale_check.py`, raw output `results/cbf_gamma_beh_scale_check.log`.

*Sourced constant, verified directly against Gozzi's code* (`models/compartment_model_age_deaths.py`
and `example.ipynb` cell 10 at `github.com/ngozzi/covid-behavior-models`, the same repo already
used for A20/C9's substep-default verification): CBF's global mechanism is
`prob_S_to_SB = β_B·(1 − exp(−γ_beh·deaths_yesterday))`, i.e. `deaths_yesterday` is a raw,
previous-day death **count** (a flow), not a stock like Weitz's H. The only concrete numeric
values anywhere in the repo — `constants.py` carries none, and per-city ABC posteriors are not
published as one canonical number (E8, unchanged) — are the authors' own demo defaults in
`example.ipynb`, run against Madrid (N=6,779,888): **β_B=0.5, μ_B=0.01, r=0.5, γ_beh=10⁰=1**,
swept illustratively over γ_beh∈{1, 0.1, 0.01, 0.001}. [Fact] This is Gozzi's own code default,
same evidentiary status as the `daily_steps=12` default settled empirically in C9 — not a fitted
value.

*Translating γ_beh into "an equivalent count" the way δ_c was is NOT clean, and is reported
rather than decided, for two independent reasons:* (a) γ_beh is the rate constant of an
**exponential** saturating function, not a power-law threshold like `(δ/δ_c)^k` — there is no
single canonical "count" to read off; the half-saturation count `ln(2)/γ_beh` and the e-folding
count `1/γ_beh` differ by <1.5×, so this ambiguity doesn't change the conclusion below, but it is
a choice, not a fact. (b) Gozzi's γ_beh was demonstrated against a **raw same/previous-day death
count**; this project's own arm-1 design (`Design_Spec_Perception_and_Population.md` §3) drives
CBF from a **smoothed rolling-mean** death signal instead (`deaths_7day_mean` there; A8/C7 later
settled the project-wide window at 28 days) — reusing γ_beh unchanged against a differently-scaled
smoothed input is not well-defined without a re-derivation not attempted here.

*What IS clean — the calculation, both ways:* at Gozzi's own reference scale (Madrid,
N=6,779,888, γ_beh=1), the implied half-saturation count is **0.693 deaths/day** — already
sub-single-digit at the AUTHORS' OWN calibration population, before touching N=3,000 at all. If
γ_beh is rescaled the same proportional-to-N way δ_c was (`γ_beh_project = γ_beh_demo ×
N_demo/N_project`), at N=3,000 that gives γ_beh≈2,260 and an implied half-saturation count of
**0.00031 deaths/day** — saturating on the very first death. Both routes land far below
single-digit, i.e. in the *worse-than-broken* range, not the safe tens-to-hundreds range C12
established.

*What is clean regardless of the translation choice — direct simulation, N=3,000, 30/30 seeds,
600 days, 48 sub-steps/day, behaviour OFF (the upper bound; a working throttle only shrinks
these further):*

| Quantity | mean | std | min | max |
|---|---|---|---|---|
| peak H (stock, agents) | 12.93 | 2.61 | 6 | 19 |
| peak daily deaths (flow, raw count) | 2.53 | 0.56 | 2 | 4 |

**[Fact] At N=3,000, the raw counts ANY count-based behavioural trigger would see — Weitz's H
stock or CBF's daily-death flow, regardless of which specific rule or parameter value drives it
— are already in or below C12's "broken" regime (peak H≈23 there gave 4.56% error; N=3,000's own
disease-only ceiling is peak H≈13, peak daily deaths≈2.5), and this is the *ceiling*, not the
typical case, since a working behavioural throttle only suppresses transmission further and
shrinks these counts more.** This reframes the question: it is not only "did we pick a bad δ_c,"
but potentially "is N=3,000 itself too small for any death/hospitalisation-count-based
behavioural trigger to escape the small-count bias regime" — independent of arm 1's specific
rule. N=3,000 is a hard-settled constraint (A7/D3) chosen for a different reason (response
gradation, C5), so this is **reported, not decided**: whether this is a genuine problem for arm
1/Test 2, and if so whether the fix is a different N, a different trigger formulation, or
something else, is for the planning chat.

**C14 — Ceiling scaling check: is peak-H/peak-deaths growth linear in N?** Follow-up to C13,
`experiments/ceiling_scaling_check.py`, raw output `results/ceiling_scaling_check.log`. Same
disease-only (behaviour OFF), 30/30-seed, 600-day, 48-substep/day setup as C13, now also at
N=10,000 and N=30,000:

| N | peak H mean (std, min–max) | peak daily deaths mean (std, min–max) | N-ratio | peak-H-ratio | peak-deaths-ratio |
|---|---|---|---|---|---|
| 3,000 | 12.93 (2.61, 6–19) | 2.53 (0.56, 2–4) | 1.00× | 1.00× | 1.00× |
| 10,000 | 38.10 (4.27, 30–47) | 5.50 (0.92, 4–7) | 3.33× | 2.95× | 2.17× |
| 30,000 | 111.40 (9.91, 92–132) | 12.03 (1.72, 9–16) | 10.00× | 8.61× | 4.75× |

**[Fact] Growth is sub-linear in N for both quantities, and much more so for peak daily deaths
than peak H** (a 10× increase in N gives 8.61× peak H but only 4.75× peak daily deaths — H is a
~14-day-dwell stock accumulating a flow, so it smooths the same sub-linearity further). By
N=30,000, peak H (111.4) sits inside C12's "safe" range (66.5–172.5, ≤0.80% error there); peak
daily deaths (12.0) is still well below C12's H-based safe range, but C12 never tested a
deaths-flow-based trigger directly, so this is not a direct read-across — reported as raw scaling
data only, no N recommendation implied.

**C15 — State-count check (Design_Spec_Perception_and_Population.md §5) at N=10,000/30,000, a
simple stand-in rule, no arm 1 built.** `experiments/state_count_check.py`, raw output
`results/state_count_check.log`. Fields used: `age_band` (10, quota-drawn), `occupation_flex`
and `response_efficacy` (3 bins each, Design_Spec §3/§4's already-decided provisional
Beta(2,2)/fixed defaults — not invented here), `own_health` (3, Sec 2a's fully-specified
mapping), and three population-wide dynamic fields binned with **hand-picked, explicitly
provisional edges** (Design_Spec §8 item 2 states bins are unsettled) — `deaths_28day_mean`
per-capita (8 bins, [0, 0.001]), `cumulative_deaths` per-capita (6 bins, [0, 0.01]), `social_norm`
(10 bins, [0.5, 1.0]). **Omitted:** `local_deaths_7d` (CBF's local/contact-weighted mechanism) —
no contact-network structure exists in the well-mixed `src/model.py` disease model (A5), so
"local" would trivially equal "global" here; this omission removes a factor of 4 from the
design spec's own combinatorial table and is flagged, not silently absorbed. Decision cadence:
every decision-eligible agent (not in H/D) logged every day (p=1, the upper bound on total
decisions — a lower cadence only shrinks the denominator, so this is the most conservative case
for the ratio). One seed per N (a single full run, as asked):

| N | distinct states | total decisions | ratio | compression if perfectly cached |
|---|---|---|---|---|
| 10,000 | 3,364 | 5,946,724 | 0.000566 | ~1,768× |
| 30,000 | 3,040 | 17,840,400 | 0.000170 | ~5,869× |

**[Fact] Distinct states realized (3,040–3,364) are a small fraction even of this stand-in's own
structurally-reachable ceiling** — only 60 of the 90 (age×occ×eff) static combinations are ever
realized (school-age and retired bands have a FIXED, not free, `occupation_flex` per Design_Spec
§3, so they contribute only 1 occ-bin each, not 3 — verified directly, not a bug), giving a
reachable ceiling of 60×3×8×6×10=86,400, of which ~3.5–3.9% is actually visited. **Distinct
states did not grow with N (3,364 at N=10,000 vs 3,040 at N=30,000) while total decisions grew
~3×** — larger N converges the epidemic trajectory closer to its deterministic (ODE-like) shape
(register C9's convergence story), so the number of distinct day-to-day dynamic-bin combinations
visited does not obviously increase with N. **This is a single seed per N, a stand-in rule (not
CBF), and hand-picked bins — reported as a first empirical read, not a settled caching
conclusion.** No N or caching decision made here.

**C16 — δ_c-sweep methodology repeated with CBF's OWN mechanism (not Weitz's) — does N=30,000
work for the real rule?** `experiments/cbf_deltac_sweep.py` (+ an inline extension to larger T,
`results/cbf_deltac_sweep_ext.log`/`.json`), deterministic direct-g only, no per-agent draws, no
S/S^B compartment split — same isolation principle as C12, but this time using CBF's actual
sourced formula (C13): `g_CBF(D) = 1 − β_B·(1 − exp(−γ_beh·D))`, with **D = deaths[t−1], a raw
one-day-LAGGED death count** (CBF's own published design — recomputed once per day, not every
sub-step; this is not the D10 bug being reintroduced, it is what CBF's formula actually
specifies). β_B held at Gozzi's sourced demo value 0.5 throughout (C13); γ_beh swept via its
characteristic count `T = 1/γ_beh`, at values chosen to extend past C12's progression once the
first four points didn't converge. 30/30 seeds, days=900, 48 sub-steps/day, ODE recomputed per
(N, T):

| N | T | mean peak daily deaths | ODE final S | ABM mean final S | relative error | gap (SEMs) |
|---|---|---|---|---|---|---|
| 30,000 | 0.5 | 8.2 | 0.31148 | 0.27435 | 11.92% | −17.92 |
| 30,000 | 2.0 | 9.5 | 0.23202 | 0.20841 | 10.17% | −16.11 |
| 30,000 | 3.5 | 10.2 | 0.18140 | 0.16703 | 7.92% | −12.58 |
| 30,000 | 7.0 | 10.9 | 0.12896 | 0.12282 | 4.76% | −9.02 |
| 30,000 | 15 | 11.6 | 0.09335 | 0.09126 | 2.24% | −4.56 |
| 30,000 | **30** | **11.8** | 0.07652 | 0.07618 | **0.45%** | −0.96 |
| 30,000 | **60** | **11.9** | 0.06800 | 0.06802 | **0.03%** | 0.06 |
| 30,000 | 120 | 12.0 | 0.06375 | 0.06393 | 0.28% | 0.56 |
| 30,000 | 250 | 12.0 | 0.06155 | 0.06190 | 0.57% | 1.10 |
| 10,000 | 0.5 | 4.7 | 0.25686 | 0.17944 | 30.14% | −26.29 |
| 10,000 | 2.0 | 5.1 | 0.13901 | 0.12183 | 12.36% | −11.56 |
| 10,000 | 3.5 | 5.3 | 0.10727 | 0.09984 | 6.92% | −6.92 |
| 10,000 | 7.0 | 5.4 | 0.08379 | 0.08097 | 3.37% | −3.79 |

**[Fact] At N=30,000, the bias does become small — but not until T≈30–60 (γ_beh≈0.017–0.033),
where it's statistically indistinguishable from zero (≤1 SEM).** Below that (T≤15), the error is
large and highly significant (2.2–17.9 SEMs), far worse at every matched T than Weitz's own
mechanism was in C12 (compare: Weitz needed only T≈2.0 to reach ≤0.3 SEMs; CBF needs T≈30–60, an
order of magnitude higher). **Critically, mean peak daily deaths barely changes across this
entire "safe" transition (11.6→11.8→11.9→12.0), sitting right at C14's disease-only ceiling for
N=30,000 (12.03)** — the bias only vanishes once γ_beh is so small that the behavioural effect is
nearly switched off (at T=60, peak transmission reduction is ~9%; at T=250, ~2%), i.e. the model
is converging to something close to Test 1's already-validated no-behaviour case, not to a
meaningfully-behavioural one. A γ_beh anywhere near Gozzi's own sourced demo value (γ_beh=1,
i.e. T=1, between this sweep's T=0.5 and T=2.0 points) shows 10–12% error at N=30,000 — nowhere
near safe.

**Confound, flagged not resolved:** CBF's one-day lag (a discrete, previous-day count, unlike the
corrected zero-lag continuous Weitz mechanism) is itself a plausible independent contributor to
the residual — D10 showed a bare 1-day lag alone produced ~26% error even with H-based δ at
N=100,000. This sweep does not separate "small flow-count" from "one-day lag" as two effects; it
tests CBF's mechanism exactly as published, which has both. Isolating them (e.g. a zero-lag,
continuous-flow variant of CBF's formula) has not been done and is a natural next step, not taken
here since it wasn't asked for this round.

**Answer to "does N=30,000 work for the real rule, not just Weitz's": only for a weak
behavioural effect (T≳30, close to no-behaviour). For anything resembling Gozzi's own
demonstrated γ_beh, N=30,000 is not safe by this measure.** Reported, not decided — no N,
tolerance, or arm-1 design choice has been made on this basis.

**C17 — CBF exactly as arm 1 is actually specified to run (not Gozzi's literal formula): the
bias resolves at both N=10,000 and N=30,000.** Single test, not a sweep — the one configuration
the project actually intends: `experiments/cbf_28day_mean_test.py`. `g_CBF(D) = 1 −
β_B·(1−exp(−γ_beh·D))`, **β_B=0.5 and γ_beh=1 held exactly at Gozzi's sourced value (C13), not
substituted** — the only change from C16 is that **D is the project's actual settled signal, a
28-day rolling mean of daily deaths (A8/C7, Design_Spec §2/§3), using days strictly before today
(shrinking window for the first 28 days), not Gozzi's literal single-day-lagged raw count.**
Deterministic direct-g only, no per-agent draws. The ODE reference is a genuine delay
differential equation (a trailing 28-day integral, `N·(Dcum(t)−Dcum(t−28))/28`) implemented as a
fixed-step (dt=0.25 d) RK4 integrator with a stored cumulative-death history — sanity-checked
against the known Test 1 ODE target with β_B=0 (behaviour off): reproduced 0.05952 to 5 decimals,
confirming the integrator itself is correct before trusting its behavioural-mode output. 30/30
seeds, days=900, 48 sub-steps/day:

| N | mean peak daily deaths | ODE final S | ABM mean final S | relative error | gap (SEMs) |
|---|---|---|---|---|---|
| 10,000 | 5.3 | 0.13260 | 0.12973 | 2.16% | −1.10 |
| 30,000 | 10.0 | 0.21761 | 0.21428 | 1.53% | −1.76 |

**[Fact] Both gaps are within ~2 SEMs of zero — statistically indistinguishable from no bias,
at Gozzi's own sourced γ_beh, unmodified.** This is a dramatic change from C16, where the same
γ_beh=1 (T=1) against Gozzi's own literal one-day-lag signal showed 10,000: ~21% and 30,000:
~11% error (interpolating C16's T=0.5/T=2.0 points), each 15+ SEMs from zero. **The 28-day
averaging — adopted in A8/C7 for an unrelated reason (response gradation at small N, C5/C7) —
also resolves the small-flow-count bias this session has been chasing since C11.** [Speculation,
medium confidence] This is consistent with the working hypothesis all along (C12/D11/C13): the
problem was never γ_beh specifically, it was feeding a nonlinear saturating function a raw,
high-variance single-sample count; a 28-day mean is a ~28x variance-reduction on exactly that
count, so this is the expected mechanism, not a coincidental fix.

**Not yet answered, and not tested this round (not asked):** whether this also holds at
N=3,000 — the project's actual settled operating population (A7/D3), not the N=10,000/30,000
explored this session. C13 already showed N=3,000's own disease-only ceiling (peak daily
deaths≈2.5) is smaller than N=10,000's here (5.3) — smaller than either point in this clean
result — so this is not a foregone conclusion at N=3,000 and would need its own test. Also not
tested: the two-sided (stochastic, per-agent) version of CBF's S/S^B mechanism — this remains a
deterministic direct-g isolation only, per C12/C16's methodology.

**C18 — CBF's REAL S/S^B mechanism (not `direct-g`) built and tested at N=3,000/10,000/30,000
(D12/E17's requested follow-up).** `src/model.py`'s new `run_cbf_behaviour` implements S and
S^B as separate tracked compartments with genuine sub-step competing-hazards transitions,
verified directly against Gozzi's `compartment_model_age_deaths.py` (fetched and read in full
this round): from S, one joint "leave" draw split by relative hazard between adoption
(`prob_S_to_SB = beta_B*(1-exp(-gamma_beh*D(t)))`) and infection (full force of infection); from
S^B, one joint "leave" draw split between relaxation (`prob_SB_to_S = mu_B*(S+R)/N`) and
infection at the reduced rate `r*foi`. With individual agents rather than Gozzi's age-group
binomial counts, the equivalent is two sequential per-agent Bernoulli draws (leave, then
destination) — distributionally identical by multinomial thinning, not an approximation.
beta_B=0.5, mu_B=0.01, r=0.5, gamma_beh=1 (Gozzi's own sourced demo values, C13, unmodified);
D(t) is the project's actual settled signal — a 28-day rolling mean of daily deaths, shrinking
window, days strictly before today (A8/C7, C17's convention) — not Gozzi's own literal
yesterday-count.

Reference: a genuine 7-state (S, S^B, E, I, H, R, D) delay-differential-equation system,
fixed-step RK4 (dt=0.25d), same delay-history convention as the ABM. Sanity-checked first (as
C17's reference was): with beta_B=0, S^B never receives inflow and the system collapses exactly
to Test 1's validated 6-state system — reproduced 0.05952 to 5 decimals (0.0002% relative
error), confirming the integrator before trusting its behavioural-mode output.

`experiments/cbf_real_mechanism_test.py`, raw output `results/cbf_real_mechanism_test.json`/
`.log`. Real per-agent stochastic S/S^B ABM (not `direct-g`), 30/30 seeds, days=900 (C16/C17's
convergence-testing convention, not the 600-day production run length), 48 sub-steps/day:

| N | mean peak daily deaths | ODE final S | ABM mean final S | relative error | gap (SEMs) |
|---|---|---|---|---|---|
| 3,000 | 2.6 | 0.14643 | 0.13979 | 4.54% | −0.90 |
| 10,000 | 4.8 | 0.22199 | 0.23182 | 4.43% | 1.13 |
| 30,000 | 9.2 | 0.29849 | 0.28169 | 5.63% | −3.12 |

**[Fact] Unlike C16/C17's `direct-g` results (which improved or stayed flat as N grew — C17:
2.16%/1.53% relative error at N=10,000/30,000, both gaps <2 SEMs), the real mechanism's relative
error does NOT shrink monotonically with N (4.54% → 4.43% → 5.63%), and the sign of the gap
flips between N=10,000 (+1.13 SEMs) and N=30,000 (−3.12 SEMs).** All three N show a
similar-magnitude relative error (~4.4-5.6%), roughly double C17's `direct-g` error at the
matching N, and N=30,000's gap is the only one exceeding ~2 SEMs.

**[Fact] This is NOT a small-count artifact of the kind C12/D11 found for Weitz's H-stock.** A
diagnostic run (10 seeds/N, not part of the committed batch) measured mean peak S^B population:
555 (N=3,000), 3,999 (N=10,000), 16,122 (N=30,000) — two to four orders of magnitude above C12's
"broken" threshold (peak H≈23-172, where the bias was shown to collapse). The bias here persists
at S^B counts large by C12's own standard, so C12's explanation does not transfer to this
mechanism.

[Speculation, low confidence] The magnitude (~4-6%) and its failure to shrink with N instead
resembles E16's still-open C11 residual — Weitz's own two-sided `q` mechanism (continuous-q)
showed a statistically real 4.13% gap at N=100,000 (30 seeds, large H counts throughout) that
was never explained by small counts either. If the two are related, the common thread may be an
intrinsic mean-field-approximation gap in how a stochastic compartment split interacts with a
nonlinear saturating adoption function, independent of N — but this is not established, only
noted as a parallel worth checking.

**Not decided here (per CLAUDE.md's working convention):** whether ~4-6% is an acceptable
tolerance for Test-2-style closure of the real CBF mechanism; whether N=3,000 (arm 1's actual
operating population, A7/D3) is "safe" by this measure — its own gap (−0.90 SEMs) is not
significant, but its relative error (4.54%) is comparable to N=30,000's significant one, a case
where the SEM criterion and the relative-error criterion disagree, itself worth flagging; what,
if anything, explains the non-monotonic-in-N pattern; and whether any of this changes arm 1's
viability or design. Reported to the planning chat, not decided.

**C19 — C18 re-run at 90 seeds for N=3,000/10,000 (N=30,000 left alone; already >2 SEMs at 30
seeds) to check whether the ~4.5% gap was noise a 30-seed SEM couldn't rule out.**
`experiments/cbf_real_mechanism_seed_check.py` (imports C18's own `_worker`/`ode_final_S`
unchanged — no model or reference change, seeds 0-29 identical to C18's, 60 more added), same
parameters, days=900, 48 sub-steps/day. Raw output `results/cbf_real_mechanism_seed_check.json`/
`.log`:

| N | seeds | mean final S | ODE final S | relative error | gap (SEMs) |
|---|---|---|---|---|---|
| 3,000 | 30 (C18) | 0.13979 | 0.14643 | 4.54% | −0.90 |
| 3,000 | **90** | 0.13906 | 0.14643 | **5.03%** | **−1.66** |
| 10,000 | 30 (C18) | 0.23182 | 0.22199 | 4.43% | +1.13 |
| 10,000 | **90** | 0.23005 | 0.22199 | **3.63%** | **+1.55** |

**[Fact] Neither point estimate collapsed toward the ODE with 3x the seeds** (N=3,000's relative
error rose slightly, 4.54%→5.03%; N=10,000's fell somewhat, 4.43%→3.63%, but not toward zero).
**Both gaps grew in SEM terms** (0.90→1.66; 1.13→1.55) — roughly consistent with a persistent,
non-shrinking bias viewed through a tightening SEM (√(90/30)=1.73× predicts 1.56 and 1.96
respectively from pure variance-reduction alone; observed growth, 1.66 and 1.55, is in the same
range). **Neither individually crosses the "several SEMs" bar C18/this round's request used as
the marker of a confirmed bias** — so this round does not, by itself, settle the question on
the pre-registered criterion. But the direction is uniform across all three N and both seed
counts now measured: no configuration's relative error has approached 0%, and the trend with
more seeds is toward greater statistical confidence in a nonzero gap, not away from it. [Speculation,
medium confidence] Combined with N=30,000's already-significant −3.12 SEMs (C18, unchanged) and
the seed-count trend here, the evidence leans toward "a real, roughly N-independent bias of a
few percent" over "N=30,000 was a 30-seed outlier" — but this is a read of a trend, not a
result that has itself cleared the bar. **Not decided here:** whether to run further seeds to
settle N=3,000/10,000 individually, what magnitude of bias would be tolerable for Test
2-style closure of the real CBF mechanism, and what (if anything) explains a bias that neither
grows nor shrinks with N. Reported to the planning chat.

**C20 — Final interpretation of C18/C19: the ~4-6% gap is real, N-independent, and not a coding
artifact — accepted as a documented limitation, not chased further.** [Decision, planning chat,
informed by C18/C19] Two separate concerns raised by this investigation are now resolved:

1. **C13's small-count concern is resolved.** C13 warned that N=3,000's own raw death/H counts
   sit in or below C12's "broken" small-count regime, raising doubt about whether ANY
   count-based trigger (Weitz's H-stock or CBF's own mechanism) could work at N=3,000 without a
   Jensen's-gap-style bias. C18's diagnostic measured the actual stock at risk for CBF's real
   two-compartment mechanism — peak S^B population — at 555 (N=3,000), 3,999 (N=10,000), 16,122
   (N=30,000): two to four orders of magnitude above C12's threshold (peak H≈23-172) at every N
   tested, including N=3,000. Combined with C17's finding that the 28-day mean already smooths
   the raw death-count input enough to avoid the same bias on the trigger side, both halves of
   the small-count concern are closed. **This is confirmed NOT what explains the remaining gap.**

2. **The remaining ~4-6% relative-error gap between the real CBF ABM and its DDE mean-field
   reference is real and does not shrink with N.** C18 measured 4.54%/4.43%/5.63% relative error
   at N=3,000/10,000/30,000 (30 seeds); C19's 90-seed re-run of the two smaller N moved the point
   estimates to 5.03%/3.63% and pushed both further from zero in SEM terms (0.90→1.66;
   1.13→1.55), while N=30,000 already stood at −3.12 SEMs. No N tested shows the gap collapsing
   toward zero the way Test 1's disease-only convergence does.

3. **Confirmed not a coding bug**, checked two ways, independent of the N-sweep itself: (a) a
   1,000,000-trial Monte Carlo of the competing-hazards two-sequential-Bernoulli-draw code
   against the theoretical joint-multinomial split, across four representative hazard-rate pairs
   including an edge case (zero adoption rate), matched theory within 3× sampling SEM in every
   case; (b) the 28-day rolling-mean window computation, fed the identical death sequence from
   an actual beta_B>0 ABM run, reproduced the DDE reference's cumulative-difference formula to
   within floating-point precision (max diff = 0.0) at every day of a 200-day run, including the
   shrinking-to-full-window transition at day 28.

**[Decision]** Given (1) and (3) rule out the two most likely mechanical explanations, and (2)
shows the gap is stable in magnitude and persistent (though not monotonic in sign) across three
population sizes and two seed counts, this is recorded as a genuine, modest limitation of
comparing this stochastic two-compartment model against its mean-field DDE reference — similar
in kind (though not confirmed in cause) to E16's separately-open Weitz-mechanism residual.
**Recommendation, adopted: treat the ~4-6% gap as a documented, accepted feature of this
comparison rather than a defect to keep chasing with more seeds, more N, or further mechanism
audits.** This closes E18.

**C21 — Per-agent `response_efficacy` wired into CBF's `r`, replacing the flat r=0.5 used
throughout C13-C20's validation round.** `src/model.py` gains
`cbf_r_from_response_efficacy(response_efficacy) = 1 - response_efficacy`, computed once per
agent (static, not recomputed per day — response_efficacy does not change over an agent's
lifetime) inside `run_cbf_behaviour`, which now REQUIRES a length-N `response_efficacy` array
(normally `Population.response_efficacy` from `src/population.py`) in place of the old scalar
`r_factor` parameter.

**[Decision, unsourced]** The mapping itself — higher response_efficacy (an agent's belief that
precautions work) gives a lower residual transmission rate `r_i` while that agent is in S^B —
is a stated modelling choice, not a sourced formula: no paper specifies how response_efficacy
maps onto CBF's `r`, only that response_efficacy is the PMT construct (β=+0.251) that maps to it
(Sourcing_Pack_v3.md Sec 3a, Design_Spec_Perception_and_Population.md Sec 2). **Same
evidentiary status as occupation_flex's own values (A13/A14 area): sourced construct, unsourced
mapping/values.**

Verified before calling this done (`tests/test_cbf_response_efficacy.py`): (a) `r_i == 1 -
response_efficacy_i` checked directly against a handful of values and against a real built
population; (b) the effective cautious transmission rate `r_i * beta` is confirmed strictly
decreasing as response_efficacy rises from 0 to 1 (101-point sweep); (c) `run_cbf_behaviour` now
rejects a `response_efficacy` array of the wrong length instead of silently misaligning it; (d)
a smoke run with the real quota-drawn population wires through end to end without error.

**Realised population-average `r_i`, measured not assumed** (N=3,000, Beta(2,2), seed=0 — the
same population `tests/test_population.py` exercises): response_efficacy mean 0.4992 (SD
0.2216), so **mean r_i = 0.5008**. This lands close to Gozzi's flat demo default (r=0.5, C13)
because Beta(2,2)'s expectation is exactly 0.5 — but this is the realised finite-N draw, not a
guarantee, and would differ under a different seed or a different swept Beta shape (Design_Spec
Sec 6 Step 3's stated later sweep).

**Not done this round (deliberately, per instruction): the N=3,000/10,000/30,000 validation
battery (C18/C19/C20's own tests) has NOT been re-run with per-agent r.**
`experiments/cbf_real_mechanism_test.py` and `experiments/cbf_real_mechanism_seed_check.py`
still call the old `r_factor=` keyword and will error if run as-is — they need updating (build a
`Population` per N, pass `response_efficacy` through) before they can run again. That update,
and the re-run itself, are a separate step.

**C22 — CBF with per-agent response_efficacy-derived r, validated at N=3,000/10,000/30,000
against the same flat-r=0.5 DDE reference used in C18/C19. [Measured, closed]**

**N=3,000 (operating size for all four arms): clean at every seed count tried (10, 30, 90) and
across 5 independent population draws** — relative error 2.59-8.43%, all within 1 SEM of the
reference. No evidence of a problem at the size actually used by the project.

**N=10,000: real, non-zero gap**, confirmed by 5 independent population draws (10 seeds each,
20.0-23.3%) and by extending one population from 30 to 90 seeds (17.34%→16.48%, gap growing
from 3.49 to 5.48 SEMs — stable magnitude, increasing certainty it's real, not noise).

**N=30,000: real but not yet converged** — extending 30→90 seeds moved the estimate itself
(7.53%→12.29%, 3.47→7.54 SEMs), unlike N=10,000 where the estimate held steady. The true
magnitude at this N is unresolved; that it is non-zero was already established (>3 SEMs at 30
seeds, before the instability was found).

**Ruled out as causes, each independently checked:** a bug in `build_population` (independently
re-derived, exact match); a bug in the array-based per-agent hazard rewrite (bit-exact match to
the old scalar code when every agent is given r=0.5); an unusual specific population draw at
N=10,000 (5 independent draws, same result); response_efficacy=0 being mishandled as "no seed"
(checked the literal source, no such branch exists); the hazard formula misbehaving at extreme
response_efficacy values (isolated test at 0.0001/0.9999, correct direction, no NaN/inf/negative
values); a pile-up of extreme agents at N=30,000 (1 agent above 0.999, 0 below 0.001).

**Working hypothesis, unconfirmed:** the DDE reference assumes one shared r for the whole S^B
compartment and has never been rebuilt for per-agent r; mixing many different r values is not
guaranteed to average to the same dynamics as one shared r. Confirming this would require
building a heterogeneous-r mean-field reference — separate, larger scope, not undertaken here.

**Decision:** since no arm in this project runs above N=3,000, and N=3,000 shows no problem,
this is recorded as a documented, accepted limitation of the N=10,000/30,000 stress test only —
not chased further, same treatment as the earlier flat-r gap (C20). Revisit only if a future
stage requires a validated arm 1 above N=3,000 (not currently planned).

**C23 — "Gozzi as-is" arm-1 baseline (step 1 of the supervisor's one-modification-at-a-time
plan): 28-day mean vs yesterday's-deaths signal, with Gozzi's 70% reporting and age-based IFR.
[Measured facts only; no decision taken.]** Planning-chat inputs (not re-decided): flat r=0.5
for every agent; detection 0.7 and per-agent f_D = IFR_10AGE[age_band] adopted; Weitz disease
parameters and 48 sub-steps kept; Gozzi's 14-day Δ NOT added (H with T_H=14 already supplies
the infection-to-death delay).

*Code.* `src/model.py`: `run()` and `run_cbf_behaviour()` accept `f_D` as a scalar (default
0.01) or a length-N per-agent array; `run_cbf_behaviour()` gains `detection_rate` (default 1.0)
and optional `truncate_by_age_band`. Agents perceive reported deaths; the recorded `deaths`
series is always the realised count. Tests: `tests/test_mortality_and_reporting.py` (defaults
bit-identical to the pre-change HEAD code, loaded via git; per-agent f_D mean 0.009718; signal
= window mean of 0.7 × realised; literal-cast mode; detection never changes realised deaths).

*How Gozzi applies 0.7 — from source.* `models/compartment_model_age_deaths.py` line 152
(default `deaths_delay="fixed"`; repo commit 7ddda64):
`deaths[:, (t-1)+int(Delta)] = (detection_rate * np.random.binomial(new_R_day, ifr)).astype(int)`.
It is a **multiplier on the count, not binomial thinning**, followed by an **integer cast per age
group per day**. (The `"gamma"` delay branch, lines 154–163, applies no detection at all.) At
Gozzi's city scale the cast is negligible; at N=3,000 a single death in a band becomes
floor(0.7)=0. [Decision, Max, this session] Main configs use the plain multiplier (no cast); the
literal cast was added as an extra measured config (2T) rather than assumed away.

*Setup.* `experiments/step1_gozzi_baseline.py`, `results/step1_gozzi_baseline.{json,log}`.
N=3,000 quota population (seed 0), r=0.5 flat, β_B=0.5, μ_B=0.01, γ_beh=1, 48 sub-steps, R0=3,
latent 2 d, infectious 6 d, T_H=14, 10 initial infected, 900 days, seeds 0–29 for every config.
Controls are `run_cbf_behaviour` with β_B=0 (identical to the no-behaviour model in
distribution, and same random-number pattern as the behavioural runs, so seeds pair). DDE
reference: C18's `ode_final_S`, now parameterised by `f_D` and `detection_rate` (detection
scales the signal inside γ_beh·D); age-based configs use f_D = 0.009718. DDE sanity check with
β_B=0 reproduced 0.05952 (0.0002% error); default arguments reproduce C18's 0.14643.

| config | window | detection | f_D | final S | peak I | peak S^B | peak daily deaths |
|---|---|---|---|---|---|---|---|
| 1 | 1 | 0.7 | age | 0.18214 ± 0.00647 | 543.1 ± 14.1 | 918.6 ± 47.3 | 2.47 ± 0.10 |
| 2 | 28 | 0.7 | age | 0.14438 ± 0.00868 | 592.5 ± 16.6 | 567.2 ± 62.1 | 2.50 ± 0.11 |
| 3 | 28 | 1.0 | flat 0.01 | 0.13979 ± 0.00740 | 606.5 ± 13.3 | 534.0 ± 47.1 | 2.60 ± 0.10 |
| 2T | 28 | 0.7, per-band floor | age | 0.06533 ± 0.00178 | 676.5 ± 5.1 | 89.4 ± 13.9 | 2.70 ± 0.13 |
| ctrl A | — | — | age | 0.05850 ± 0.00104 | 679.2 ± 4.9 | — | 2.73 ± 0.14 |
| ctrl B | — | — | flat 0.01 | 0.05850 ± 0.00104 | 679.2 ± 4.9 | — | 2.73 ± 0.17 |

Mean ± SEM, n=30 for every cell. Peak I and peak S^B are agent counts. Controls A and B have
identical S and I trajectories because, with no behaviour, f_D only routes I-leavers to H or R
(both non-infectious), and the random draws are the same; only deaths differ (29.3 vs 28.0
total).

*Pass mark (a)* — paired difference from control (same seed), n=30:

| config | Δ peak I | Δ final S | (a) |
|---|---|---|---|
| 1 | −136.2 ± 12.8 (−10.61 SEM) | +0.1236 ± 0.0063 (+19.57 SEM) | pass |
| 2 | −86.8 ± 15.8 (−5.48 SEM) | +0.0859 ± 0.0086 (+10.00 SEM) | pass |
| 3 | −72.7 ± 13.4 (−5.43 SEM) | +0.0813 ± 0.0074 (+11.02 SEM) | pass |
| 2T | −2.7 ± 1.8 (−1.52 SEM) | +0.0068 ± 0.0019 (+3.68 SEM) | fail (peak I) |

*Pass mark (b)* — ABM mean final S vs the continuous-signal DDE, n=30:

| config | DDE | rel. error | gap | (b) ≤6% |
|---|---|---|---|---|
| 1 | 0.20675 | 11.90% | −3.80 SEM | fail |
| 2 | 0.12763 | 13.12% | +1.93 SEM | fail |
| 3 | 0.14643 | 4.54% | −0.90 SEM | pass |
| 2T | 0.12763 (not like-for-like) | 48.81% | −34.95 SEM | fail |

**[Fact] Config 2's (b) failure is within noise at 30 seeds.** At N=3,000, one SEM of final S
is ~6.8% of the reference — larger than the 6% band itself, so a 30-seed run cannot resolve
it. Supplementary run (`experiments/step1_supplement.py`, `results/step1_supplement.{json,log}`;
seeds 0–29 identical to the main run, extended to 0–89):

| config | n=30 rel. error (gap) | n=90 rel. error (gap) |
|---|---|---|
| 1 | 11.90% (−3.80 SEM) | **17.07% (−9.13 SEM)** |
| 2 | 13.12% (+1.93 SEM) | **1.52% (+0.47 SEM)** |
| 3 | 4.54% (−0.90 SEM) | 5.03% (−1.66 SEM) — identical to C19 |
| det 0.7 only, flat f_D | 3.48% (−0.76 SEM) | 4.25% (−1.56 SEM) |
| age f_D only, det 1.0 | 14.97% (+1.99 SEM) | 1.46% (+0.40 SEM) |

The one-at-a-time split shows the high 30-seed config-2 value came from seeds 0–29 running high
under age-based f_D, not from a reference mismatch: both single changes sit within the C18–C20
band at 90 seeds. **Config 1's gap is real and grows with seeds.**

*Other measured items.*
- Runs with any E or I agent at day 600: 0/30 in every config; at day 900: 0/30 in every config.
- **Config 3 vs C18: bit-identical on 30/30 seeds** (mean 0.13979 both; paired diff 0). At 90
  seeds it also reproduces C19 exactly (0.13906).
- Config 2 − config 3 (effect of 70% reporting + age-based f_D together), paired, n=30: final S
  +0.0046 ± 0.0095 (+0.48 SEM); peak I −14.1 ± 17.6 (−0.80 SEM). Not distinguishable from zero.
- Reported/realised deaths, pooled over 30 runs: 0.7000 (configs 1, 2); **0.0668 for 2T** — the
  literal per-band cast removes ~90% of the signal at N=3,000, and behaviour is nearly switched
  off (peak S^B 89 vs 567).
- Diagnostic DDE holding the signal fixed within each day (the ABM's own convention) instead of
  updating it every RK4 step: config 1 ref 0.20331 (rel. error 10.41%, −3.27 SEM), config 2
  0.12539, config 3 0.14368 (2.71%). The convention difference does not explain config 1's gap.
- Mean-field f_D: using f_D = 0.009718 is exact in expectation here, since with flat r the
  infection hazard does not depend on age. It would not be exact with per-agent r (C21/C22).

*Recorded predictions (planning chat, written before running) vs outcome.* Config 1: "passes
(a), fails (b) with relative error > 10%" — **as predicted** (11.90% at n=30, 17.07% at n=90).
Config 2: "passes both" — **(a) pass; (b) fail at the pre-registered n=30 (13.12%, +1.93 SEM)**,
but 1.52% (+0.47 SEM) at n=90.

**Not decided here:** whether yesterday's-deaths is dropped; whether the literal per-band cast
or the plain multiplier is the "as-is" baseline; whether pass mark (b)'s seed count should be
raised given its 30-seed resolution at N=3,000. No settled value was changed.

**C24 — Modification A: per-agent r vs flat r, on the C23-config-2 foundation. [Measured facts
only; no decision taken.]** `experiments/step2_personal_r.py` (+ `step2_common.py`),
`results/step2_personal_r.{json,log}`. Foundation (F): N=3,000 frozen quota population (seed 0),
real CBF, flat r=0.5, β_B=0.5, μ_B=0.01, γ_beh=1, window 28, detection 0.7 (A25), per-agent f_D
(A26), Weitz disease, 48 sub-steps, 10 initial infected, 900 days. PR changes only r:
r_i = 1 − response_efficacy_i (C21), from the same population (response_efficacy mean 0.4992 →
mean r_i 0.5008). Control A = β_B=0. Seeds 0–89 for every config. F and A are bit-identical to
C23's config 2 / Control A on seeds 0–29 (30/30 each).

| | F (flat r) | PR (per-agent r) | A (no behaviour) |
|---|---|---|---|
| final S | 0.12957 ± 0.00412 | 0.13969 ± 0.00506 | 0.05912 ± 0.00063 |
| peak I | 620.7 ± 7.7 | 618.1 ± 8.1 | 679.8 ± 2.6 |
| peak S^B | 463.6 ± 26.2 | 472.7 ± 26.2 | — |
| peak daily deaths | 2.50 ± 0.07 | 2.54 ± 0.07 | 2.69 ± 0.08 |

n=90 for every cell; runs with E or I agents at day 900: 0/90 in each config.

**Primary — paired difference PR − F (same seed), n=90:** final S **+0.01012 ± 0.00107
(+9.47 SEM)**; peak I **−2.63 ± 0.84 (−3.12 SEM)**; peak S^B +9.08 ± 1.48 (+6.13 SEM); peak daily
deaths +0.044 ± 0.027 (+1.65 SEM). **[Fact] Detectable by the stated criterion** (|diff| > 2 SEM
in both final S and peak I). In relative terms: final S +7.8% of F's value, peak I −0.4%.

**Pass mark (a), n=90:** PR vs A: peak I −61.7 ± 8.0 (−7.76 SEM), final S +0.0806 ± 0.0051
(+15.70 SEM) → pass. F vs A: −59.1 ± 7.5 (−7.90 SEM), +0.0704 ± 0.0042 (+16.78 SEM) → pass.

**Pass mark (b):** not applied to PR (the DDE assumes one shared r, C22). F, for continuity
under A27: n=30 13.12% / +1.93 SEM → INCONCLUSIVE; n=90 1.52% / +0.47 SEM → PASS (as C23).

**Recorded prediction (planning chat, written before running):** "PR has slightly higher final S
than F; whether the difference exceeds 2 SEM at N=3,000 is uncertain." **Outcome:** higher
final S, as predicted, and the difference exceeds 2 SEM (+9.47 SEM).

[Speculation, medium confidence] Mean r_i is essentially 0.5, so the shift comes from the
spread of r, not its mean: agents with low r_i (high response_efficacy) are both better
protected and, being uninfected longer, stay in S/S^B, so infection selectively depletes the
high-r agents — the same kind of heterogeneity effect C22 hypothesised for the N=10,000/30,000
gap. Not tested.

**C25 — Modification B: Gozzi disease parameters vs Weitz. Step 3a convergence check FAILED;
3b not run. [Measured facts only.]** Gozzi disease set, checked against source
(`models/constants.py`: `mu = 1/2.5` → infectious_period_days=2.5; `eps = 1/4` →
latent_period_days=4; `example.ipynb`: R0=2.5); transmission rate R0/infectious = 1.0/day.
T_H=14 and everything else unchanged. `experiments/step2_gozzi_disease.py`,
`results/step2_gozzi_disease.{json,log}`. The DDE reference (`ode_final_S`) now also takes the
disease parameters; defaults still reproduce C18 (0.14643) and C23 config 2 (0.12763).

Step 3a (behaviour off, N=100,000, 30 seeds, 48 sub-steps, 900 days; analytical final size
s = exp(−2.5(1−s)) = 0.10736):
- DDE with β_B=0: 0.10736 (0.0046% relative error) — passes.
- **ABM: mean final S 0.10624 ± 0.00040 (n=30), relative error 1.043%, gap −2.79 SEM — FAILS
  the < 1% tolerance.** Per instruction, 3b was not run.

For comparison, the same check under the Weitz set (C9, 48 sub-steps) gave 0.05% relative
error. [Speculation, medium confidence] The ABM sits below the target (more infection than the
continuous model), the same direction as the sub-step discretisation bias C9 measured. The
Gozzi set's rates are larger per step (infectious rate 0.4/day vs 0.167/day, transmission
1.0/day vs 0.5/day), so 48 sub-steps may no longer be enough for it. Not tested — e.g. a
96-sub-step run of the same check would confirm or rule this out. Not decided here.

**C25 addendum — Gozzi disease set at 96 sub-steps: convergence passes; Step 3b run. [Measured
facts only.]** `python experiments/step2_gozzi_disease.py --substeps 96`,
`results/step2_gozzi_disease_96sub.{json,log}`. Only the Gozzi-set configs (3a check, G, CG) use
96 sub-steps; the Weitz foundation F and its control A stay at 48 (main setup unchanged). The
sub-step counts differ because at 48 the Gozzi set failed the < 1% convergence check (above),
while 48 already converges for the Weitz set (C9).

*3a re-check* (behaviour off, N=100,000, same 30 seeds as C25, 96 sub-steps): ABM mean final S
**0.10701 ± 0.00035 (n=30) vs 0.10736 — relative error 0.329%, gap −1.02 SEM → PASS**
(48 sub-steps: 1.043%, −2.79 SEM). Recorded prediction ("passes, well under 1%"): as predicted.

*3b* (N=3,000, seeds 0–29 = C24's first 30; foundation otherwise unchanged; flat r=0.5):

| n=30 | Weitz F (48 sub-steps) | Weitz control A | Gozzi G (96) | Gozzi control CG (96) |
|---|---|---|---|---|
| final S | 0.1444 ± 0.0087 | 0.0585 ± 0.0010 | 0.1984 ± 0.0098 | 0.1038 ± 0.0019 |
| peak I | 592.5 ± 16.6 | 679.2 ± 4.9 | 253.9 ± 6.2 | 281.0 ± 3.5 |
| peak S^B | 567.2 ± 62.1 | — | 602.1 ± 40.2 | — |
| peak daily deaths | 2.50 ± 0.11 | 2.73 ± 0.14 | 2.47 ± 0.12 | 2.43 ± 0.13 |

Runs with E or I agents at day 900: 0/30 in every config.

Behavioural effect (paired vs own control, n=30):
- final S: Weitz +0.0859 ± 0.0086 (+10.00 SEM); Gozzi +0.0946 ± 0.0096 (+9.89 SEM).
- peak I: Weitz −86.8 ± 15.8 (−5.48 SEM, −12.8% of control); Gozzi −27.1 ± 5.1 (−5.34 SEM,
  −9.7% of control).

**Pass mark (a), G vs CG: PASS** (peak I −5.34 SEM, final S +9.89 SEM). Recorded prediction
("G passes (a)"): as predicted.
**Pass mark (b), G vs Gozzi-parameterised DDE (0.20318): relative error 2.37%, gap −0.49 SEM
(n=30) → PASS** under A27; no 90-seed re-run needed. (F at n=30 reads INCONCLUSIVE, 13.12%; at
n=90 it is PASS, 1.52% — C23/C24.)

Other measured facts: Gozzi peak prevalence is ~0.4× Weitz's (shorter infectious period, 2.5 vs
6 d). The N=3,000 no-behaviour final S sits below the analytical value for both sets (CG 0.1038
vs 0.10736, −3.3%; A 0.0585 vs 0.05952, −1.7%). [Speculation, medium confidence] A finite-N effect, since at
N=100,000 both converge; not separately tested.

**C26 — Gradation sweep over γ_beh at N=1,000 and N=3,000. [Measured facts only; no decision on
N or γ_beh.]** `experiments/step2_gradation.py`, `results/step2_gradation.{json,log}`.
Foundation (flat r=0.5 per A29; detection 0.7; per-agent f_D; Weitz disease; 48 sub-steps; 10
initial infected; 900 days). γ_beh ∈ {0.25, 0.5, 1, 2, 4} × Gozzi's sourced default — a
sensitivity sweep, not a calibration. Seeds 0–29 for every config; one no-behaviour control per N.

*Prerequisite code (committed):* `run_cbf_behaviour` now defaults to flat r=0.5, and the C21
mapping sits behind `experimental_r_from_response_efficacy`. C23 config 2 reproduces
bit-identically (30/30 seeds), as do C24's F and PR (90/90 each). The N=1,000 quota population
uses the Design Spec's largest-remainder method. On Gozzi's raw New York `pop_data_Nk.csv`
counts, the same method reproduces the published N=3,000 table exactly. At N=1,000 it gives
**[110, 112, 63, 80, 157, 126, 125, 111, 74, 42]** (same from the raw CSV or from the spec's
2-decimal shares; no near-ties), realised mean IFR **0.971836%** (N=3,000: 0.971791%).

| N | γ_beh | final S | peak I | peak S^B | adoption rate at peak signal (/day) | (a) | (b) |
|---|---|---|---|---|---|---|---|
| 1,000 | ctrl | 0.0554 ± 0.0020 | 233.7 ± 3.2 | — | — | | |
| 1,000 | 0.25 | 0.0650 ± 0.0032 | 229.8 ± 3.7 | 34.1 ± 5.2 | 0.0231 ± 0.0022 | pass | pass (5.28%) |
| 1,000 | 0.5 | 0.0733 ± 0.0043 | 229.0 ± 4.1 | 57.6 ± 9.8 | 0.0443 ± 0.0041 | **fail** (peak I −1.92 SEM) | pass (4.19%) |
| 1,000 | 1 | 0.0857 ± 0.0061 | 225.1 ± 5.0 | 85.4 ± 15.9 | 0.0837 ± 0.0071 | pass | pass (4.73%) |
| 1,000 | 2 | 0.1030 ± 0.0086 | 219.6 ± 6.3 | 122.3 ± 23.0 | 0.1487 ± 0.0105 | pass | inconcl. → pass at n=90 (2.85%) |
| 1,000 | 4 | 0.1277 ± 0.0105 | 215.0 ± 6.7 | 169.5 ± 28.2 | 0.2479 ± 0.0122 | pass | inconcl. → pass at n=90 (1.22%) |
| 3,000 | ctrl | 0.0585 ± 0.0010 | 679.2 ± 4.9 | — | — | | |
| 3,000 | 0.25 | 0.0888 ± 0.0030 | 655.6 ± 7.3 | 227.5 ± 15.5 | 0.0564 ± 0.0022 | pass | inconcl. → pass at n=90 (0.92%) |
| 3,000 | 0.5 | 0.1078 ± 0.0046 | 634.0 ± 10.4 | 347.6 ± 31.6 | 0.1037 ± 0.0038 | pass | inconcl. → pass at n=90 (0.18%) |
| 3,000 | 1 | 0.1444 ± 0.0087 | 592.5 ± 16.6 | 567.2 ± 62.1 | 0.1761 ± 0.0054 | pass | inconcl. → pass at n=90 (1.52%) |
| 3,000 | 2 | 0.1903 ± 0.0130 | 538.3 ± 24.6 | 893.3 ± 98.9 | 0.2761 ± 0.0091 | pass | **FAIL** (16.36%, +2.06 SEM, n=30) |
| 3,000 | 4 | 0.2277 ± 0.0159 | 478.0 ± 30.1 | 1227.4 ± 126.8 | 0.3817 ± 0.0101 | pass | inconcl. → pass at n=90 (4.56%) |

n=30 per cell (the n=90 re-runs affect only the (b) column). Runs with E or I agents at day 900:
0/30 everywhere. Adoption rate = β_B(1 − exp(−γ_beh·D_max)), with D_max the run's maximum
28-day reported-death signal; β_B cap = 0.5/day.

**Gradation (paired adjacent steps in final S, n=30):**
- N=1,000: +5.08, +4.18, +6.18, +6.76 SEM; monotonic → **GRADED** (4/4 steps significant).
- N=3,000: +9.08, +8.37, +9.36, +9.70 SEM; monotonic → **GRADED** (4/4).
- Peak I steps at N=3,000: −4.37, −5.44, −5.57, −8.15 SEM. At N=1,000: −0.83, −2.70, −2.69,
  −2.17 SEM.

**[Fact] The peak death signal scales with N** (raw counts, C13): D_max ≈ 0.19 at N=1,000 vs
0.39–0.48 at N=3,000. So the same γ_beh gives a weaker response at N=1,000: the S1
final-S effect is +0.030 there vs +0.086 at N=3,000.

**Recorded prediction (planning chat):** "steps below γ_beh=1 significant, steps above 1 small
(adoption already near the β_B cap); GRADED at N=3,000." **Outcome:** GRADED at N=3,000, as
predicted. **But steps above 1 are not small** (+9.36, +9.70 SEM; peak-I steps grow), and
adoption at the peak signal is not near the cap: 0.38 of 0.5 at γ_beh=4, 0.18 at γ_beh=1.

*Diagnostic outside the A27 rule (verdict unchanged):*
`results/step2_fail_diagnostic_90.log`. N=3,000 γ_beh=2 extended to seeds 0–89 gives 0.16460
± 0.00645 vs DDE 0.16355: 0.64%, +0.16 SEM. Of the five distinct N=3,000 behavioural points re-run or
diagnosed at 90 seeds (γ_beh 0.25, 0.5, 1, 2, 4; S1 is the γ_beh=1 point), all five moved
closer to the DDE, and all five 30-seed means sat above their 90-seed means. These are not independent observations: common random numbers make
the configs correlated across seeds.

**C27 — Scenario separation S1/S2/S3 with the real CBF arm 1, N=1,000 and N=3,000 (closes the
measurement asked for in E4). [Measured facts only; no decision on N or scenarios.]**
`experiments/step2_scenarios.py`, `results/step2_scenarios.{json,log}`. Scenario_Spec §3:
S1 R0=3/T_H=14, S2 R0=2/T_H=14, S3 R0=3/T_H=28. Each has behaviour (foundation, γ_beh=1) and
its own no-behaviour control. Seeds 0–29. Run length is 900 days (foundation), not the spec's
600. S1 is the same configuration as C26's γ_beh=1 point, and the numbers match.

| N | scen. | final S beh / ctrl | peak I beh / ctrl | peak day beh / ctrl | peak S^B | effect final S | effect peak I | (a) | (b) |
|---|---|---|---|---|---|---|---|---|---|
| 1,000 | S1 | 0.0857 / 0.0554 | 225.1 / 233.7 | 27.3 / 27.2 | 85.4 | +0.0304 ± 0.0055 (+5.49) | −8.6 ± 3.7 (−2.33) | pass | pass (4.73%) |
| 1,000 | S2 | 0.2720 / 0.1969 | 123.2 / 134.2 | 40.3 / 40.2 | 217.8 | +0.0751 ± 0.0111 (+6.79) | −11.0 ± 3.5 (−3.13) | pass | **FAIL** (9.01%, −2.11 SEM, n=30) |
| 1,000 | S3 | 0.0757 / 0.0554 | 227.6 / 233.7 | 27.2 / 27.2 | 74.2 | +0.0203 ± 0.0059 (+3.47) | −6.2 ± 3.5 (−1.75) | **fail** (peak I) | pass (5.12%) |
| 3,000 | S1 | 0.1444 / 0.0585 | 592.5 / 679.2 | 32.4 / 32.2 | 567.2 | +0.0859 ± 0.0086 (+10.00) | −86.8 ± 15.8 (−5.48) | pass | inconcl. → pass at n=90 (1.52%) |
| 3,000 | S2 | 0.4075 / 0.2045 | 268.8 / 352.0 | 50.7 / 52.6 | 1217.8 | +0.2029 ± 0.0169 (+12.03) | −83.1 ± 13.6 (−6.12) | pass | pass (1.59%) |
| 3,000 | S3 | 0.1094 / 0.0585 | 631.7 / 679.2 | 31.7 / 32.2 | 380.1 | +0.0509 ± 0.0066 (+7.74) | −47.5 ± 11.2 (−4.23) | pass | pass (1.88%) |

n=30 for every statistic. Effects are paired differences from the scenario's own control (in
SEMs). Runs with E or I agents at day 900: 0/30 everywhere.

**Separation (difference of behavioural effects vs S1, per seed, n=30):**
- N=1,000: S2 final S +0.0447 ± 0.0082 (+5.43 SEM), peak I −2.4 ± 2.9 (−0.81); S3 final S
  −0.0100 ± 0.0026 (−3.91 SEM), peak I +2.5 ± 1.3 (+1.87). Both separate on final S → **PASS**.
- N=3,000: S2 final S +0.1171 ± 0.0129 (+9.09 SEM), peak I +3.6 ± 9.8 (+0.37); S3 final S
  −0.0350 ± 0.0060 (−5.82 SEM), peak I +39.3 ± 9.9 (+3.96 SEM). Both separate → **PASS**.

**[Fact] S1 and S3 controls are identical in infections on the same seeds** (final S, peak I,
peak day, total incidence identical on 30/30 seeds at both N). Only deaths move: peak daily
deaths S3 − S1 = −0.20 ± 0.11 (N=1,000), −0.30 ± 0.16 (N=3,000).

**Recorded predictions (planning chat) vs outcome:**
- "S3 has a higher peak I than S1 (later reaction)" — N=3,000: yes (631.7 vs 592.5; the effect
  differs by +39.3, +3.96 SEM). N=1,000: 227.6 vs 225.1, the effect difference not significant
  (+1.87 SEM).
- "S2 has a smaller behavioural effect than S1 (weaker death signal)" — **not as predicted.**
  S2's final-S effect is larger (N=3,000: +0.203 vs +0.086; N=1,000: +0.075 vs +0.030). Its
  absolute peak-I effect is not distinguishable from S1's (−83.1 vs −86.8, +0.37 SEM). As a
  fraction of its own control's peak, the reduction is larger in S2 (−23.6% vs −12.8%).
- "Both separate at N=3,000" — as predicted.

*Diagnostic outside the A27 rule (verdict unchanged):* N=1,000 S2 extended to seeds 0–89 gives
0.28934 ± 0.00735 vs DDE 0.29894: 3.21%, −1.31 SEM (`results/step2_fail_diagnostic_90.log`).

**N=1,000 vs N=3,000 on the four criteria (planning chat's decision rule; not applied here):**

| criterion | N=1,000 | N=3,000 |
|---|---|---|
| (a), all 8 behavioural configs | **2 fail**: γ_beh=0.5 (peak I −1.92 SEM), S3 (peak I −1.75 SEM) | all pass |
| (b), A27 rule | **1 FAIL**: S2 (9.01%, −2.11 SEM); passes at n=90 in the diagnostic | **1 FAIL**: γ_beh=2 (16.36%, +2.06 SEM); passes at n=90 in the diagnostic |
| GRADED | GRADED (4/4) | GRADED (4/4) |
| SEPARATION | PASS (on final S only) | PASS |

Not decided here: N, γ_beh, scenario set, or whether A27 should change given the two
borderline n=30 FAILs.

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
(2, 2, 3, 3 at T_H = 7, 14, 21, 28) *under one specific prominence threshold*. The ABM does not
reproduce this under any threshold tested. ⚠️ **This claim is now known to be threshold-fragile
even at the ODE level — see D9.** The integration scheme (D1/E11) has been ruled out as the
cause (E12, disconfirmed). Root cause remains unknown.

**D9 — The wave-count metric is unsourced and threshold-fragile, even on the ODE.** Unlike
Weitz's symmetry coefficient (extracted from their Fig 1C), "count peaks with
`scipy.signal.find_peaks`" is not a method described in either source paper — it was introduced
in this project as an analytical convenience. [Fact] On the *same deterministic ODE curve*,
three reasonable, independently-chosen prominence thresholds give three different qualitative
answers: 5% of the global peak → rising 2,2,3,3 (this register's original citation); 10% of the
global peak → flat 2,2,2,2; 10% of each local peak's own height → rising 2,3,3,4. Consequence:
**no sourced, robust, quantitative definition of "number of oscillations" currently exists in
this project**, at either the ABM or the ODE level. Peak height and final susceptible fraction
remain the only metrics that have been robust throughout, and they carry no shape information.

**D10 — Test 2's δ(t) specification was wrong; corrected.** Originally specified as "raw death
count from the running simulation" — a tally of realized D-transitions (tried both lagged,
δ(t)=deaths(t−1), and same-day via a two-pass split). Measured at ~26% relative error (lagged)
and ~48% (same-day two-pass — worse, not better) against the ODE at N=100,000, 30 seeds, far
outside Test 2's 2% tolerance. Confirmed NOT a two-sided/Bernoulli artifact: a deterministic
`direct-g` version (no `q`, no per-agent draws, transmission multiplied by g(δ) directly, same
lagged δ) gave essentially the same wrong answer (0.392 vs the q-based 0.388, 5 seeds).
**Root cause:** Weitz's own model defines δ(t) = γ_H·H(t) — a continuous instantaneous rate from
the *current* H-compartment stock — not a discrete count of deaths that already happened.
Recomputing δ this way (from the running H count each sub-step, no lag) drops the deterministic
`direct-g` version's error to ~1.6% (5 seeds) — confirms the diagnosis. **Not yet closed:** even
with this fix, the actual two-sided `q` mechanism still shows a residual gap against the ODE —
see E16. Diagnostic script: `experiments/verify_meanfield_delta_bug.py`.

**D11 — D10's 5-seed `direct-g` number (~1.6%) does not hold at full scale; withdrawn.** Re-run
at N=100,000, 30/30 seeds, days=900 (C11): `direct-g` measures **4.56%**, not ~1.6%, a
statistically real gap (−7.11 SEMs), not sampling noise. [Fact] Since `direct-g` has no
per-agent stay-home draws at all — the only mechanism is `transmission_rate × g(δ) × I/N` with δ
computed exactly as the ODE defines it — this rules out the two-sided `q`/Bernoulli mechanism
*and* decision cadence as the sole cause of the residual gap (E16), because the deterministic,
mechanism-free variant fails by nearly as much as the two `q`-based variants (4.13%/5.91%).
[Speculation, low confidence — CONFIRMED, see C12] One candidate: δ_c=0.5 corresponds to a small
H-compartment stock (measured peak ~23 agents, C12), so early in an epidemic `g(δ)` is being
evaluated on small integer H counts where the ABM's discreteness diverges most from the ODE's
continuous H(t) — a Jensen's-gap-style effect (E[g(H)] ≠ g(E[H]) for nonlinear g under
population-level stochastic fluctuation in H, distinct from the sub-step time-discretisation
bias C9 already ruled out as the cause here). **C12's δ_c sweep (direct-g only, N=100,000, 30
seeds) confirms this directly: 4.56% error at δ_c=0.5 (peak H≈23) collapses to 0.10-0.80% at
δ_c=2.0/3.5/7.0 (peak H≈66-172), tracking the H-count scale, not δ_c per se.** Root cause of the
C11 residual is no longer open for `direct-g`. **Still undecided (per CLAUDE.md's working
conventions, reported not decided):** whether the two-sided `q` variants show the same collapse
at larger δ_c (not tested this round — C12 deliberately isolated `direct-g` alone), and what this
implies for Test 2's δ_c=0.5 baseline, its tolerance, or arm 1/2's operating δ_c — see E16.

**D12 — C16/C17's `direct-g` simplification is confirmed NOT a valid stand-in for CBF's real
mechanism.** [Fact, verified directly against `models/compartment_model_age_deaths.py` lines
74–147, the same repo already used for A20/C9/C13.] CBF is explicitly a **5-compartment** model
(S, S^B, E, I, R) — S^B is a genuine tracked stock, not a derived instantaneous quantity. Each of
the `daily_steps` sub-steps runs a proper **competing-hazards** split: from S, agents race between
"→E" (force of infection, full rate) and "→S^B" (adoption, `prob_S_to_SB`), drawn as one joint
binomial then split by relative hazard (source lines 114–118); from S^B, agents race between "→S"
(relaxation, `prob_SB_to_S = μ_B·(S+R)/N`) and "→E" (force of infection at the *reduced* rate
`r·β`) (lines 120–126). **Relaxation is driven by μ_B alone, essentially independent of the death
signal.** With Gozzi's own sourced μ_B=0.01/day (C13), the relaxation half-life is
`ln(2)/0.01≈69 days` — far slower than the disease's own timescale (latent+infectious≈8 days,
T_H=14 days). Cautious agents stay cautious long after deaths subside: genuine memory/hysteresis
that an instantaneous, memoryless multiplier `g(D)` structurally cannot reproduce. `direct-g` was
a fair match for **Weitz's** mechanism (whose own published ODE literally *is* a direct
multiplicative modulation, no separate compartment) — that does not carry over to CBF, which has
a real two-compartment structure Weitz's does not.

**What the correct version needs (not built):** an explicit S^B stock evolved sub-step-by-sub-step
alongside S/E/I/H/R/D, with `prob_S_to_SB(t) = β_B·(1−exp(−γ_beh·D(t)))` (adoption, driven by
whatever death signal — 28-day mean per C17, or otherwise) and `prob_SB_to_S(t) = μ_B·(S(t)+R(t))/N`
(relaxation, driven by a roughly constant rate, *not* the death signal), with competing-hazards
transitions at each sub-step exactly as Gozzi's code implements them.

**Consequence for C16/C17: those results remain valid AS TESTS OF THE SIMPLIFIED `direct-g`
FORMULA (methodologically consistent with C12's isolation approach), but they do NOT establish
whether the REAL two-compartment CBF mechanism is safe at N=10,000/30,000 (let alone N=3,000).**
S^B is itself a new stock subject to its own small-N discreteness questions (C12's own finding
applied to a different compartment), and the adoption/relaxation timescale mismatch could produce
dynamics (e.g. hysteresis across epidemic waves) a memoryless multiplier cannot exhibit in either
direction — untested, either way. **The requested C17-style test at N=3,000 was deliberately NOT
run this round**, since it would have rested on the same unconfirmed premise. Reported, not
fixed — building the real S/S^B mechanism is a modelling/implementation decision for the planning
chat, not made here.

**D13 — N=3,000 reaffirmed; C13's motivating concern for possibly needing a larger N is
resolved.** C13 raised the possibility that N=3,000 might be structurally too small for arm 1's
own count-based trigger to escape a small-count bias regime, independent of the specific rule or
parameter — potentially requiring a larger operating N to make arm 1 viable at all. C18-C20
answer this: the real CBF mechanism's ~4-6% gap against its mean-field reference is present at
N=3,000, 10,000, AND 30,000 alike (C18/C19) and does not shrink with N, so a larger N would not
have removed it — the effect C13 worried about (small S^B/H-type counts) is confirmed absent at
every N tested (C20), and the gap that does exist is N-independent. **A7 (N=3,000) is
reaffirmed, not revised** — there is no reason to trade N=3,000's original justification (C5's
response-gradation requirement, D3) for a larger, more expensive population; doing so buys
nothing against the one concern that motivated considering it.

## E. Open items

| # | Item | Blocks |
|---|---|---|
| E1 | Arm-2 budget at N=3,000 — 1.62M calls at p=0.3, 810k weekly, 540k weekly with 2 scenarios | arm 2 |
| E2 | Re-decision cadence sweep in arm 1 (free) | E1 |
| E3 | Realised state count from arm 1 logs. **First read with a stand-in rule (C15, not real CBF): 3,040-3,364 distinct states out of millions of decisions (ratio ~0.0002-0.0006, ~1,768-5,869x compression) at N=10,000/30,000** — one seed, hand-picked bins, not yet with the real CBF rule or at N=3,000. **The option to build caching exists and looks promising on this first read, but whether to build it is Max's call, not a Claude Code decision — noted here, not acted on** | caching decision (Max's) |
| E4 | Re-measure C3 scenario separation with CBF at N=3,000 | scenario spec |
| E5 | **ANSWERED — yes.** See C7. N=3,000 + 28-day window adopted | closed |
| E11 | `experiments/abm.py` uses a single daily step with raw-rate transitions, contradicting A20 | correctness of the delay kernel |
| E12 | **DISCONFIRMED** — see D9/G3. Switching to 12 sub-steps did not change the T_H → wave-count direction under either definition | closed as a candidate cause; D6 itself remains open |
| E13 | Trend field horizon under a 28-day window — see Design Spec §2 | perception vector |
| E14 | Find a sourced, robust way to quantify "number of oscillations" — or drop oscillation as a target signature entirely and rely solely on peak-height reduction / final-S shift from control (both robust throughout) | shape metric, stated project contribution |
| E15 | **RESOLVED — see C9/A20-rev.** Bias confirmed (not a bug); 48 substeps adopted | closed |
| E16 | **Root cause of the C11 residual identified for `direct-g` (C12): small H-compartment stock at δ_c=0.5 (peak H≈23 agents) produces a Jensen's-gap-style bias that vanishes at larger δ_c (0.10-0.80% error at δ_c=2.0/3.5/7.0, vs 4.56% at 0.5).** Not yet resolved for the actual `q`-based variants: continuous-q (4.13%) and daily-q (5.91%) at δ_c=0.5 have NOT been re-swept across δ_c (C12 deliberately isolated `direct-g` only, one variable at a time) — it is not yet confirmed the same collapse happens once per-agent stochastic draws are added back in. Open questions for the planning chat: (a) does the `q`-mechanism residual also collapse at larger δ_c, or does the Bernoulli draw add its own scale-dependent bias on top; (b) Test 2's actual δ_c=0.5 comes from rescaling Weitz's N·δ_c=50 down to N=100,000 — if small-N/small-δ_c is intrinsically biased, does that indict the rescaling approach itself, or only this validation test's choice of N; (c) what cadence to adopt for arm 1 given neither has been shown to close the gap at the production δ_c; (d) whether Test 2's stated 2% tolerance is still the right gate; (e) **C13's higher-priority finding: at N=3,000 (arm 1's actual population, not Test 2's N=100,000), the raw counts behind EITHER Weitz's H-stock or CBF's own γ_beh/daily-deaths trigger are already at or below the "broken" scale even with behaviour off — this may not be a δ_c/γ_beh tuning problem at all, but an N=3,000 problem that affects arm 1 directly, not just this validation test** | Test 2 closure; E2; arm 1 cadence choice; **arm 1 viability at N=3,000 (C13); N=30,000 tested for the real CBF mechanism and found NOT safe except at weak-behaviour settings when using Gozzi's literal yesterday-count signal (C16) — but IS statistically clean at both N=10,000 and N=30,000 (gap <2 SEMs) once the project's own actual 28-day-mean signal is used instead, at Gozzi's own unmodified γ_beh (C17). N=3,000 itself still untested under C17's configuration. **D12: C16/C17 both used a `direct-g` simplification now confirmed NOT a valid stand-in for CBF's real 5-compartment, memory-laden mechanism — their results stand only as tests of that simplified formula, not of arm 1's actual planned dynamics; the N=3,000 test was withheld pending this** |
| E6 | Prompt wording and anchoring scheme; pilot before full arm-2 run | arm 2 |
| E7 | Persona layer — may be redundant given the sourced population construction | diversity metric |
| E8 | Gozzi SI prior ranges for β_B, μ_B, γ_beh (per-city posteriors, no canonical value) — confirmed directly against source (C13): no calibrated value exists anywhere in the repo, only the authors' own uncalibrated demo default (β_B=0.5, μ_B=0.01, r=0.5, γ_beh=1). C13 additionally finds this demo value implies a sub-single-digit death-count trigger even at the authors' own Madrid scale, before any rescaling | arm 1 calibration; Test 2 (E16) |
| E9 | Whether the ABM/ODE oscillation discrepancy (D6) indicates a simulator defect | milestone 2 |
| E10 | Contamination experiment: named vs unnamed disease, decision-level agreement | arm 2 writeup |
| E17 | **BUILT, TESTED, AND CLOSED — see C18/C19/C20.** `src/model.py`'s `run_cbf_behaviour` implements the real S/S^B two-compartment mechanism (adoption + relaxation, competing hazards). The ~4-6% relative-error gap against a sanity-checked DDE reference (N=3,000/10,000/30,000, 30 then 90 seeds) is confirmed real, N-independent, not a small-S^B-count artifact, and not a coding bug — adopted as a documented, accepted limitation (C20) rather than pursued further | closed |
| E19 | **PROPOSED, not decided:** arm 2 stops calling the LLM once E+I = 0 for the rest of the run. No further infections are then possible, so later decisions cannot change any outcome | arm-2 budget (E1) |
| E18 | **CLOSED — see C20.** The ~4-6% gap between the real CBF mechanism and its mean-field DDE reference is accepted as a documented, N-independent limitation of the ABM-vs-mean-field comparison, not chased further with more seeds, more N, or mechanism audits. (Whether it is mechanistically the same phenomenon as E16's separate Weitz-mechanism residual remains an open curiosity, not pursued — E16 itself stays open, it concerns Test 2/Weitz's own rule, not arm 1's CBF) | closed |

## F. Known limitations of everything measured above

- All ABM results are **well-mixed**; no clustered network has been tested.
- Seed counts are 8–30 depending on the run; none are large.
- C3 used the Weitz reference rule, not CBF.
- The 7-day awareness window was not re-tested under the real CBF mechanism. N=3,000 was
  originally justified with it (C5/C7); A30 re-checks N only with the 28-day window.
- E9 remains unresolved: the ABM does not reproduce the ODE's T_H → oscillation relationship,
  and it is not yet known whether this is a metric problem or a simulator defect.

---

## G. Build-phase state

Repo `fyp-abm` (GitHub). Layout: `docs/` · `src/` · `tests/` · `experiments/` · `results/` ·
`CLAUDE.md` · `requirements.txt` · `.gitignore`.

| Item | State |
|---|---|
| Verification Test 1 — ODE convergence | ✅ **CLOSED.** `tests/test_ode_convergence.py`, repointed to `src/model.py` (G2 resolved), 30/30 seeds, N=100,000, behaviour off, 1% relative tolerance (G1 resolved). Measured: mean final S=0.05926 vs ODE 0.05952, 0.431% relative error. See C10 |
| Verification Test 2 — mean-field recovery | ❌ **BLOCKED, not passing.** δ fix (D10) now applied in `src/model.py`'s `run_weitz_behaviour` (continuous, per-sub-step, zero-lag) and re-tested at full N=100,000/30 seeds (C11): 4.13% relative error for the actual (continuous-q) implementation, still outside the file's stated 2% tolerance. The deterministic sanity variant also fails at this scale (4.56%, D11) — the residual is not fully explained by cadence or the two-sided mechanism. Root cause of the remaining ~4-6% gap is open (E16) |
| Verification Test 3 — renderer totality | ❌ cannot exist — no `Perception` dataclass or renderer yet |
| `src/` | `model.py` — SEIR+H disease dynamics, behaviour off (`run`, Test 1); Weitz's own behaviour rule for simulator validation (`run_weitz_behaviour`, Test 2, A4/A19/A23); and arm 1's real CBF mechanism (`run_cbf_behaviour`, S/S^B compartments with competing hazards, C18/E17), now with per-agent heterogeneity in `r` via `cbf_r_from_response_efficacy` (C21). `perception.py` — the `Perception` dataclass (shape only, no renderer/computation yet). `population.py` — quota-drawn `Population` construction at N=3,000, `build_population` (age_band/vulnerability sourced and derived; occupation_flex/response_efficacy configurable free Beta draws) |
| `experiments/abm.py` | validated pilot; **contradicts A20** — single daily step with raw-rate transitions rather than 12 sub-steps. Untouched throughout the `src/model.py` build |
| `experiments/metrics.py` | shape-metric exploration; computes the symmetry coefficient, which D7/D8 show is unreliable. Do not build on it |
| `experiments/verify_substep_bias.py`, `verify_substep_scheme.py`, `verify_meanfield_delta_bug.py` | diagnostic scripts kept alongside the pilot, not part of `src/` — back C9, D9/G3, and D10 respectively |

**G1 — Tolerance note. RESOLVED.** Test 1 used 2% relative tolerance against CLAUDE.md's stated
"three decimals" while it guarded the pilot. Tightened to 1% when repointed to `src/model.py`
(C10) — measured at 0.431% relative error, comfortably inside it.

**G2 — Test 1 currently guards a pilot script, not the model. RESOLVED.** Repointed to
`src/model.py` (C10); the suite now validates the code that is actually run.

**G3 — [DISCONFIRMED, measured].** Switching to 12 sub-steps/day (A20's mandated scheme) did
not change the T_H → wave-count direction under either counting convention tested (prominence
relative to the run's global peak, or to each local peak's own height). Wave counts stayed
flat/noisy (~1.0–2.2) across T_H ∈ {7,14,21,28} under both the old and new integration schemes,
20/20 seeds, N=3,000. The wrong dwell-time distribution (D1/E11) is ruled out as the explanation
for D6. A20 still stands on its own merits — it matches Gozzi's published implementation and
gives the correct dwell-time distribution shape — independent of whether it explains D6. See D9
for why D6's own ODE reference is now in question too.

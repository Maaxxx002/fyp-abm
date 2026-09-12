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
| A8 | Perception signal: **28-day rolling mean** of reported deaths | C7 — a 7-day window leaves the response ungraded at N ≤ 3,000. Smoothing itself is sourced to Weitz Methods; the 28-day length is a stated finite-population correction, not a behavioural claim |
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
| A20 | Integration: **48 sub-steps per day** (revised from 12 — see C9) | Gozzi's own default (`daily_steps=12` — verified in their source: `compartment_model_age_deaths.py`, `function_model_age_deaths.py`, `mobility_model_age.py`, all `dt=1/12`) is insufficient for this model's precision; see C9 |
| A21 | Initial infected: **10 agents** (0.33% at N=3,000) | D8 — a 1% seed removes the exponential growth phase entirely |
| A22 | Repo `fyp-abm` is the build artefact; `docs/` holds the four specs and is authoritative | Claude Code sessions read `CLAUDE.md` + `docs/` |
| A23 | "Stay home" is **two-sided**: an agent who stays home neither catches nor spreads that day, so the population multiplier is (1−q)² | Formalises the assumption already baked into `q = 1 − (1+(δ/δ_c)^k)^(−1/2)` (CLAUDE.md Test 2 / Sourcing_Pack_v3.md's "Test 3" open point) — recorded as decided, not just assumed |

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
| E16 | **Root cause of the C11 residual identified for `direct-g` (C12): small H-compartment stock at δ_c=0.5 (peak H≈23 agents) produces a Jensen's-gap-style bias that vanishes at larger δ_c (0.10-0.80% error at δ_c=2.0/3.5/7.0, vs 4.56% at 0.5).** Not yet resolved for the actual `q`-based variants: continuous-q (4.13%) and daily-q (5.91%) at δ_c=0.5 have NOT been re-swept across δ_c (C12 deliberately isolated `direct-g` only, one variable at a time) — it is not yet confirmed the same collapse happens once per-agent stochastic draws are added back in. Open questions for the planning chat: (a) does the `q`-mechanism residual also collapse at larger δ_c, or does the Bernoulli draw add its own scale-dependent bias on top; (b) Test 2's actual δ_c=0.5 comes from rescaling Weitz's N·δ_c=50 down to N=100,000 — if small-N/small-δ_c is intrinsically biased, does that indict the rescaling approach itself, or only this validation test's choice of N; (c) what cadence to adopt for arm 1 given neither has been shown to close the gap at the production δ_c; (d) whether Test 2's stated 2% tolerance is still the right gate; (e) **C13's higher-priority finding: at N=3,000 (arm 1's actual population, not Test 2's N=100,000), the raw counts behind EITHER Weitz's H-stock or CBF's own γ_beh/daily-deaths trigger are already at or below the "broken" scale even with behaviour off — this may not be a δ_c/γ_beh tuning problem at all, but an N=3,000 problem that affects arm 1 directly, not just this validation test** | Test 2 closure; E2; arm 1 cadence choice; **arm 1 viability at N=3,000 (C13); N=30,000 tested for the real CBF mechanism and found NOT safe except at weak-behaviour settings (C16)** |
| E6 | Prompt wording and anchoring scheme; pilot before full arm-2 run | arm 2 |
| E7 | Persona layer — may be redundant given the sourced population construction | diversity metric |
| E8 | Gozzi SI prior ranges for β_B, μ_B, γ_beh (per-city posteriors, no canonical value) — confirmed directly against source (C13): no calibrated value exists anywhere in the repo, only the authors' own uncalibrated demo default (β_B=0.5, μ_B=0.01, r=0.5, γ_beh=1). C13 additionally finds this demo value implies a sub-single-digit death-count trigger even at the authors' own Madrid scale, before any rescaling | arm 1 calibration; Test 2 (E16) |
| E9 | Whether the ABM/ODE oscillation discrepancy (D6) indicates a simulator defect | milestone 2 |
| E10 | Contamination experiment: named vs unnamed disease, decision-level agreement | arm 2 writeup |

## F. Known limitations of everything measured above

- All ABM results are **well-mixed**; no clustered network has been tested.
- Seed counts are 8–30 depending on the run; none are large.
- C3 used the Weitz reference rule, not CBF.
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
| `src/` | `model.py` — SEIR+H disease dynamics, behaviour off (`run`, Test 1) and Weitz's own behaviour rule for simulator validation (`run_weitz_behaviour`, Test 2, A4/A19/A23) — not arm 1's CBF, which does not exist yet |
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

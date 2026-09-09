# Sourcing pack v3 — extraction complete

Supersedes v2. Everything marked **[Extracted]** was read from the full text or the authors'
own source code. Confidence labels: **[Fact]** verified against source or by running code ·
**[Speculation]** with confidence · **[Suggestion]** a recommendation to weigh.

---

## Part 1 — Disease model

**Weitz, Park, Eksin & Dushoff (2020), *PNAS* 117(51):32764–32771. [Extracted]**

Use **model B** (Eqs 9–14): SEIR plus a hospital compartment creating the infection-to-fatality
lag. Minimal variant that produces plateau, shoulder *and* oscillation. Model A cannot
oscillate; C adds a parameter you don't need; D (fatigue) exists to fit mobility data.

```
Ṡ = −βSI·g(·)      Ė = +βSI·g(·) − μE      İ = μE − γI
Ṙ = (1−f_D)·γI     Ḣ = f_D·γI − γ_H·H      Ḋ = γ_H·H
```

`g(·)` is the behavioural multiplier — the only thing that changes between arms.

| Symbol | Meaning | Weitz | Gozzi | Note |
|---|---|---|---|---|
| R₀ | basic reproduction number | 3 | 2.5 | |
| latent period | | **2 d** | **4 d** | ⚠️ conflict |
| infectious period | | **6 d** | **2.5 d** | ⚠️ conflict |
| IFR | | 0.01 flat | age-stratified (below) | |
| γ_H / Δ | infection→death lag | 7–28 d (14 default) | **14 d fixed** | agree |
| detection rate | fraction of deaths reported | 1.0 (implicit) | **0.7** | |
| k | response sharpness | 1–4 (2 typical) | 1 (code default) | |

⚠️ **[Fact] The two papers disagree on the disease parameters.** Weitz: 2 d latent, 6 d
infectious. Gozzi: 4 d latent, 2.5 d infectious. Generation time is comparable (8 vs 6.5 d) but
the infectious-period difference changes how fast prevalence responds to behaviour. **Pick one
set, state which, and sweep the other as a sensitivity check.** [Suggestion] Take Weitz's,
since Weitz supplies the referent and your gate is whether the signature reproduces.

⚠️ **[Fact] Gozzi's variable naming is inverted relative to Weitz's.** In Gozzi's code
`mu = 1/infectious period` and `eps = 1/latent period`; in Weitz `μ = 1/latent` and
`γ = 1/infectious`. Reading one paper's symbols into the other's equations swaps the two
periods silently. Write your own symbol table before coding.

⚠️ **Discrepancy inside Weitz:** Fig 6 text says R₀ = 2.5 while its caption lists β = 0.5,
γ = 1/6, i.e. R₀ = 3. Use Table 1.

### Weitz Table 1, verbatim [Fact]

β = 0.5 d⁻¹ · 1/μ = 2 d · 1/γ = 6 d · 1/γ_H = 7–28 d · f_D = 0.01 · N = 10⁷ ·
Nδ_c = 5–500 deaths/day (**50** in Figs 3, 6, 7) · ND_c = 2,500–10,000 · k = 1–4 · ε = 1/7 d⁻¹

### Age-stratified IFR — Gozzi `models/constants.py` [Extracted]

| Age | 0–9 | 10–19 | 20–29 | 30–39 | 40–49 | 50–59 | 60–69 | 70–79 | 80+ |
|---|---|---|---|---|---|---|---|---|---|
| IFR | 0.0000161 | 0.0000695 | 0.000309 | 0.000844 | 0.00161 | 0.00595 | 0.0193 | 0.0428 | 0.0780 |

**This is your `vulnerability` feature, fully sourced with numbers.** A 5,000-fold range from
youngest to oldest. Weitz's flat 0.01 sits between the 50–59 and 60–69 values.

### The observation model [Extracted]

Gozzi's implementation makes the perception signal explicit:

```
reported_deaths(t) = detection_rate × Binomial( removals(t − Δ), IFR_age )
detection_rate = 0.7      Δ = 14 d (fixed; gamma-distributed alternative, Δ_std = 1)
```

Three distortions between infection and what an agent perceives: the infectious period, a
14-day death delay, and **30% underreporting**. Sourced, and it matters — the agent responds to
a lagged, attenuated signal, and lag is what generates oscillations.

### Referent metric — Weitz Fig 1C [Extracted]

Symmetry coefficient: at the smoothed daily-death peak `t_P`, find `Δt` where the pre-peak
value equals 10% of peak; take `value(t_P − Δt) / value(t_P + Δt)`. Symmetric = 1, plateau < 1.
LOESS on log-transformed deaths, zero-death days excluded.

⚠️ **[Fact] Works on ODE output (control 0.48, awareness 0.10); did NOT discriminate in the
stochastic ABM pilot (control 0.65, awareness 0.97 — wrong direction).** Probable cause: peak
detection latching onto a stochastic local maximum plus a 600-day window too short for the
behavioural run to finish declining. **Do not gate on it until fixed.** Use peak-height
reduction and final susceptible fraction, which separate cleanly.

### Sourced no-behaviour control [Fact]

Weitz state their model converges to conventional SEIR as δ_c → ∞. The control is a limit case
of the same model, not a different model.

---

## Part 2 — Arm 1: the rule-based decision function

**Gozzi, Perra & Vespignani (2025), *PNAS* 122(24):e2421993122. [Extracted from source code
at `github.com/ngozzi/covid-behavior-models`]** — better than the SI, since it is what they ran.

### 2a. EFB — as implemented, not as printed

The paper prints `f = 1/(1 + ξ·D_rep(t−1) + ψ·ΣD_rep)`. **The code implements**

```python
bf = 1 / (1 + short_term*(last_day_deaths/dc)**k + long_term*(cumulative_deaths/Dc)**k)
#   k : int = 1        dc = 10**dc,  Dc = 10**Dc   (log-uniform priors)
```

**[Fact] This is Weitz's model C denominator, verbatim, with k defaulted to 1.** Not merely
algebraically equivalent — literally the same expression in code. Two independent PNAS groups
converge on one functional form; Weitz generalises it with the exponent.

⚠️ `last_day_deaths` is a raw **count**, not per-capita, so `dc` has units of reported
deaths/day and does **not** transfer across population sizes. Their sensitivity sweep spans
dc ∈ {10⁰, 10¹, 10², 10³} deaths/day. You must rescale for N = 1,000.

### 2b. CBF — recommended for arm 1 [Extracted]

Susceptibles are in `S` or `S^B` (risk-averse). `S^B` is infected at reduced rate `r·λ`.

```python
# adopt protective behaviour — GLOBAL mechanism
prob_S_to_SB = beta_B * (1 - exp(-gamma_beh * total_deaths_yesterday))

# adopt protective behaviour — LOCAL mechanism (contact-weighted)
prob_S_to_SB = sum_j( beta_B * C[i][j] * deaths_j(t-1) / N_j )

# relax
prob_SB_to_S = mu_B * (sum(S) + sum(R)) / N
```

Example values used by the authors: **β_B = 0.5, μ_B = 0.01, r = 0.5, γ_beh = 10^0**.
Sensitivity sweeps in their notebook: **r ∈ {0.25, 0.5, 0.75, 1}**, **γ_beh ∈ {10⁰, 10⁻¹,
10⁻², 10⁻³}** (log-uniform prior over the exponent). Calibrated posteriors are per-city — nine
regions, nine posteriors — so there is no single "true" value to lift.

**[Fact] CBF was the top performer in their evaluation** — best nMAE in 7/9 cities, best nWIS
in 6/9, highest BIC weight in 4/9 — attributed to its behavioural functional form.

**[Suggestion] Use CBF as arm 1, not EFB.** It is already agent-level; it sources `r` (your
precaution-efficacy parameter); its relaxation term replaces `days_since_last_outing`; and it
avoids circularity — if arm 1 *is* Weitz's rule, "does arm 1 reproduce the Weitz signature" is
nearly tautological.

**[Fact] The LOCAL mechanism sources your `known_infected_contacts` feature.** Adoption driven
by deaths among one's own contacts, weighted by the contact matrix — a published, implemented
alternative to the global signal, and directly comparable in an ABM where the contact structure
is explicit. It is also a natural A/B within arm 1: global signal vs local signal, both sourced.

**Strongest case against CBF**, stated because it is real: Gozzi's SI reports EFB and the
mobility model were *more accurate on peak intensity and timing* than CBF, even though CBF won
on nMAE, nWIS and BIC. Peak timing is closer to what your gate measures than nMAE is.

### 2c. Gozzi as a second instance of your central claim [Fact]

Their nine-city comparison produces different winners under different metrics, and their R₀
posteriors for Santiago de Chile run from 4.20 [3.96, 4.42] (DDB) to 1.87 [1.69, 2.04] (CBF) to
1.77 [1.59, 1.97] (EFB) — same data, same disease, three-fold spread depending only on which
behavioural mechanism is assumed. Deck slides 4–5 currently rest on one example inside the DFD
paper; this is a second, independent instance in a 2025 PNAS paper in your own domain.

---

## Part 3 — Feature set

### 3a. Empirical determinants — PMT meta-analysis [Extracted]

*Meta-analysis on application of Protection Motivation Theory in preventive behaviors against
COVID-19*, **Int. J. Disaster Risk Reduction** (2023), PII S2212420923002388. Random-effects,
studies 2019–2022, CMA2.

| PMT construct | β | Your feature |
|---|---|---|
| **Self-efficacy** | **+0.270** | ❌ **absent** |
| **Response efficacy** | **+0.251** | ❌ **absent** |
| Perceived severity | +0.197 | partly `vulnerability` |
| Perceived vulnerability | +0.160 | `vulnerability` |
| Response cost | **−0.074** | `occupation_flexibility` |

⚠️ **[Fact] This cuts against the current feature set in two directions.**

1. **Coping appraisal beats threat appraisal**, and self-efficacy is the single strongest
   determinant. Your perception vector has **no self-efficacy and no response-efficacy
   feature**. The two strongest published determinants are missing.
2. **Response cost is the weakest construct in the meta-analysis** (β = −0.074, described as a
   weak predictor). `occupation_flexibility`, which you carry as a response-cost proxy, is
   sourced but sourced to the weakest link in the theory.

**[Suggestion]** Add a **response-efficacy** feature — the agent's belief that precautions work.
It is cheap, it maps directly onto CBF's `r` (an agent who believes precautions work is an agent
with a high perceived `r`), and it is the second-strongest determinant. Self-efficacy is harder
to represent in a single-venue model with a three-level act, since there is no meaningful
barrier to "wear a mask"; [Speculation, medium confidence] I would name it as a deliberate
exclusion with the reason, rather than force it in.

**[Suggestion]** Keep `occupation_flexibility` but **predict it will fall out of the December
ablation**, and say so in advance. A pre-registered prediction that survives or fails is worth
more than a feature quietly retained.

### 3b. Behaviour tracks deaths, not cases [Extracted]

Urmi, Pant, Dewey et al., **PNAS** (2025) doi 10.1073/pnas.2500655122 (extracted from the
medRxiv preprint, doi 10.1101/2024.12.20.24319446 — check the published version for final
numbers). COVID States Project: **431,211 responses from 307,771 respondents, 19 waves,
April 2020 – June 2022**, 15 behaviours.

- **[Fact] Correlation between the oscillatory component of risk-averting behaviour and reported
  COVID deaths peaks at lag 0 (synchronous)**, in 40 of 41 states analysed. Correlations with
  cases and hospitalisations peak at lag 0 *and* with behaviour shifted a month earlier —
  i.e. behaviour leads cases but moves with deaths.
- The authors state directly that behaviour data correlated more with mortality than with
  hospitalisation or case data, and that it may therefore be more accurate to drive behaviour
  change in models as a response to deaths rather than cases or hospitalisations.

**This is the empirical citation for `reported_deaths` over `reported_cases`** — survey-measured
behaviour, not a modelling assumption.

### 3c. Behaviour has two components, not one ⚠️ [Extracted]

**[Fact]** They decompose each behaviour into a **linear trend plus an oscillation**:

| | avg slope (SD) | avg intercept (SD) |
|---|---|---|
| Risk-averting | **−1.300 (0.405)** pp/month | 72.627 (8.814) |
| Risk-exposing | **+0.366 (0.232)** pp/month | 10.943 (11.960) |

Risk-averting adherence fell ~70% → ~20% over two years. Desensitisation at *comparable*
mortality: "avoiding contact" was 68% in April 2020, 50% in September 2021, 30% in
February 2022.

⚠️ **The authors explicitly warn that mortality-only feedback is insufficient** for models
fitted over long periods, precisely because of this secular trend.

**[Suggestion]** This is a direct hit on your design and it argues *for* CBF over EFB. CBF has
both mechanisms — adoption driven by deaths, relaxation driven by `(S+R)/N` — whereas EFB has
only the death-driven term. Your run length is 600 days, comfortably inside the regime where
the warning applies. The slope above gives you a calibration target: −1.3 pp/month over 600 days
is roughly a 26-point secular decline.

### 3d. The action space is one-dimensional [Extracted]

**[Fact]** PCA over the 15 behaviour time series: **88% of variance in the first principal
component.** Mask-wearing loads on PC2 (10.44%) and behaved differently early on, which the
authors attribute to mask availability and shifting CDC guidance.

**[Suggestion] This empirically justifies the three-level ordinal act.** If protective behaviour
is essentially one latent dimension, collapsing "stay home / precautions / normal" onto a single
ordinal scale is what the data support, not a simplification you are apologising for.

⚠️ **Do not overclaim this.** The PCA is over *aggregate time series*, so strictly it says the
behaviours **co-move over time**, not that individuals are one-dimensional. The authors do offer
an individual-level reading, but the analysis does not establish it. If you cite this for the
action space, cite it for the *dimensionality of the behaviour*, not for agent homogeneity — and
note that it says nothing either way about your diversity metric.

### 3e. Feature table as it now stands

| Feature | Type | Source status |
|---|---|---|
| health state (S/E/I/R) | dynamic | Weitz **[Extracted]** |
| 7-day mean reported deaths | dynamic | Weitz Methods; Gozzi `D_rep`; Urmi et al. lag-0 **[Extracted]** |
| cumulative reported deaths | dynamic | Weitz model C `D_c`; Gozzi EFB long-term term **[Extracted]** |
| social norm (fraction taking precautions) | dynamic | CBF relaxation `(S+R)/N` **[Extracted]** |
| known infected contacts / local deaths | dynamic | CBF **local** mechanism, contact-weighted **[Extracted]** |
| vulnerability | static | Gozzi age-stratified IFR, exact values **[Extracted]**; PMT β=+0.160 **[Extracted]** |
| response efficacy | static | ⭐ **NEW** — PMT β=+0.251 **[Extracted]**; maps to CBF `r` |
| occupation flexibility | static | PMT response cost, β=−0.074 — ⚠️ weakest construct |
| ~~days since last outing~~ | — | **deleted** — replaced by CBF relaxation rate |
| self-efficacy | — | **deliberately excluded** — strongest determinant (β=+0.270) but no meaningful barrier in a single-venue three-level act. State the exclusion. |

---

## Part 4 — Still unsourced, and how to defend it

| Choice | Value | Defence |
|---|---|---|
| Number of venues | 1 | One transmission process to parameterise; smallest model carrying the mechanism |
| Agent count N | 1,000 | **Empirically defended** — measured floor, see Part 5 |
| Re-decision cadence | p ≈ 0.3/day | Sweep in arm 1 (free); report sensitivity |
| Persona count | TBD | Minimalism plus the diversity metric — report, don't assert |

The general answer remains ablation. Every remaining feature now has a source, so the ablation
tests whether each earns its place rather than compensating for a missing citation.

---

## Part 5 — Verification tests

**Test 1 — discretisation.** ⚠️ **[Fact]** Setting the daily transition probability to
`1 − exp(−rate)` with a one-day step gives a mean infectious period of 6.51 d instead of 6 and
**R₀ = 3.257 instead of 3.000**. Invisible in any single run. **Gozzi's fix is sub-daily
stepping: `daily_steps = 12`, `dt = 1/12`, transitions `1 − exp(−rate·dt)`.** Measured:

| daily_steps | mean infectious period | implied R₀ |
|---|---|---|
| 1 | 6.521 d | 3.260 |
| 4 | 6.148 d | 3.074 |
| **12** | **6.012 d** | **3.006** |
| 24 | 5.998 d | 2.999 |

Use 12. It is what the published implementation does and it costs 12× the inner loop, not 12×
the wall clock, since the loop is vectorised over agents.

**Test 2 — ODE convergence.** Behaviour OFF, well-mixed, N ≥ 100,000, compare final susceptible
fraction to the Weitz ODE. Should agree to three decimals (0.0594 both at R₀ = 3). Pure
simulator test, no behavioural claim. This is what caught Test 1.

**Test 3 — mean-field recovery.** If each agent independently stays home with probability *q*
and transmission needs **both** parties out, the population multiplier is `(1−q)²`, not `(1−q)`.
To recover Weitz's `1/(1+(δ/δ_c)^k)`:

```
q = 1 − (1 + (δ/δ_c)^k)^(−1/2)
```

Decide explicitly whether staying home removes contacts (two-sided) or reduces per-contact risk
(one-sided), write it down, and verify against the ODE at large N.

**Test 4 — minimum N.** [Fact, measured, 20 seeds, well-mixed, Weitz model B, T_H = 14 d]

| N | fadeout | peak I (control) | peak I (awareness) | final S (control) | final S (awareness) |
|---|---|---|---|---|---|
| 100 | 40% | 26.8 | 26.8 | 0.073 | 0.105 |
| 300 | 0% | 74.3 | 68.2 | 0.054 | 0.147 |
| 1,000 | 0% | 230.4 | 187.1 | 0.057 | 0.278 |
| 3,000 | 0% | 687.6 | 404.8 | 0.059 | 0.457 |
| 10,000 | 0% | 2293.8 | 819.3 | 0.058 | 0.658 |

At N = 100 the behavioural arm and the control are the same model. **N = 1,000 is the floor.**
Requires the 7-day mean signal — the raw daily count is zero on ~98% of days at N = 1,000.

---

## Part 6 — Where the reference sits

**[Suggestion] Split Weitz's role in two.**

- **Weitz's rule = simulator validation, not an arm.** Implement `g = 1/(1+(δ/δ_c)^k)`
  per-agent, run at large N, confirm it reproduces the published ODE. Proves the simulator can
  express the signature, independent of any encoding question.
- **CBF = arm 1**, the rule-based baseline — different published rule, agent-native,
  best-performing in Gozzi's own evaluation, and it carries both behavioural mechanisms Urmi
  et al. say a long-run model needs.
- **The Weitz signature stays the external referent** for all arms. Arm 1 hitting it is then a
  finding, not a restatement.

---

## Citations

**Fully extracted**
- Weitz, Park, Eksin & Dushoff (2020), *PNAS* 117(51):32764–32771, doi 10.1073/pnas.2009911117 — code `github.com/jsweitz/covid19-git-plateaus`
- Gozzi, Perra & Vespignani (2025), *PNAS* 122(24):e2421993122, doi 10.1073/pnas.2421993122 — code `github.com/ngozzi/covid-behavior-models`
- Urmi, Pant, Dewey, Quintana-Mathé, Lang, Druckman, Ognyanova, Baum, Perlis, Riedl, Lazer & Santillana (2025), *PNAS*, doi 10.1073/pnas.2500655122 — preprint doi 10.1101/2024.12.20.24319446; data `github.com/tam-urmi/behavior_covid_states`
- *Meta-analysis on application of Protection Motivation Theory in preventive behaviors against COVID-19*, *Int. J. Disaster Risk Reduction* (2023), PII S2212420923002388

**Identified, not extracted — supporting, not load-bearing**
- Abdulkareem et al. (2018), *Int. J. Health Geographics* 17 — PMT-grounded ABM, zero-intelligent vs intelligent agents; structurally closest precedent
- Funk, Salathé & Jansen (2010), *J. R. Soc. Interface* 7(50):1247–1256 — information taxonomy
- Rogers (1983) — PMT, original statement
- *Developing agent-based models of complex health behaviour* (2018) — three-factor threshold rule
- *Risk-taking unmasked*, *PLOS ONE* (2021) 16(5):e0251073
- Capasso & Serio (1978), *Mathematical Biosciences* 42(1):43–61
- Kerr et al., *Covasim*, *PLOS Comput. Biol.* (2021) 17(7):e1009149

# Scenario specification

Companion to `Sourcing_Pack_v3.md` and `Design_Spec_Perception_and_Population.md`.

---

## 1. What a scenario may vary

⚠️ **A scenario may only vary parameters shared by all four arms.**

`δ_c`, `k`, `r`, `β_B` and `γ_beh` are parameters of arm 1's rule. Arms 2, 3 and 4 have no
equivalent — an LLM has no calibration constant. Varying them varies the object under test and
makes the arms non-comparable.

| Parameter | Legal lever? | Why |
|---|---|---|
| R₀ (via β) | ✅ | property of the disease |
| T_H | ✅ | property of the disease |
| IFR / age structure | ✅ (but frozen, §4) | property of the population |
| initial seeding | ✅ | property of the world |
| δ_c, k | ❌ | inside arm 1's rule |
| r, β_B, μ_B, γ_beh | ❌ | inside arm 1's rule |
| N, run length | ❌ | must be constant for comparability |

## 2. What a scenario is for

Two purposes, both needed:

**Discrimination.** If every scenario produces the same referent shape, an arm that always
produces that shape passes trivially. Scenarios must separate.

**Generalisation.** Arms 3 and 4 are *fitted* — arm 3 writes a decision function once, arm 4
distils from arm 2's logs. A single scenario cannot distinguish "captured the mechanism" from
"happened to fit." **Arm 4 distils from scenario S1 only and is evaluated on S2 and S3 as
held-out.** This makes arm 4 a genuine generalisation test rather than a fit check, and it costs
nothing to arrange.

## 3. The three scenarios

| | S1 — Baseline | S2 — Milder | S3 — Delayed |
|---|---|---|---|
| R₀ | 3.0 | **2.0** | 3.0 |
| T_H | 14 d | 14 d | **28 d** |
| Role | training / calibration | held out | held out |
| Varies | — | signal **magnitude** | signal **timing** |

Everything else identical: N = 1,000, 600 days, the frozen population of §4, same seed set,
same initial seeding.

**Rationale.** The perception vector carries a level (`deaths_7day_mean`, `deaths_cumulative`)
and a trend (`deaths_prev_week`). S2 stresses the level, S3 stresses the trend. An arm must
track both to pass, and the two failure modes are distinguishable — an arm with an implicit
fixed threshold will fail S2 specifically.

**[Fact] Measured separation at N = 1,000, 25 seeds, 7-day mean signal, Weitz reference rule:**

| Scenario | peak I | final S | control final S |
|---|---|---|---|
| S1 (R₀=3, T_H=14) | 188.2 | 0.278 | 0.056 |
| S2 (R₀=2, T_H=14) | 101.9 | 0.443 | — |
| S3 (R₀=3, T_H=28) | 203.4 | 0.213 | 0.056 |

S2 separates strongly on both metrics. S3 separates on final S (0.278 → 0.213) but only weakly
on peak. **[Speculation, medium confidence] S3 is the weaker scenario** and is the one to drop
if budget forces a cut to two.

**Each scenario carries its own no-behaviour control as a standing run**, not a fallback. The
referent is the shift relative to that control, not the presence of a shape.

## 4. Frozen across all scenarios

- The 1,000-agent population (quota-drawn, §6 of the design spec) — identical agents everywhere
- The seed set — so cross-scenario differences are not seed differences
- N, run length, re-decision cadence, perception vector schema, prompt template

## 5. Cost

| Scenarios | arm-2 calls (p = 0.3/day) | with weekly cadence |
|---|---|---|
| 3 | 540,000 | 270,000 |
| 2 (drop S3) | 360,000 | 180,000 |

Arms 1, 3, 4 and all controls are free at any scenario count. **Sweep the re-decision cadence
in arm 1 before committing** — it is free there, and it decides whether three scenarios are
affordable.

## 6. Known limitations

⚠️ **Shape metrics are not yet reliable, and the referent is a shape.**

Two independent shape metrics have failed in the ABM while working on ODE output:

1. **Weitz's symmetry coefficient** — ODE: control 0.48, awareness 0.10 (clean separation).
   ABM: control 0.65, awareness 0.97 (wrong direction).
2. **Wave count** — Weitz's ODE reproduces their published result that waves rise with T_H
   (2, 2, 3, 3 at T_H = 7, 14, 21, 28). The ABM does not, and two reasonable prominence
   definitions give different answers on identical runs: peak-scaled gives a monotone decline
   (3.25 → 2.62 → 1.88), plateau-scaled gives no trend (6.00 → 4.38 → 5.00).

Ruled out as causes: the 7-day smoothing (inversion persists with raw daily deaths at
N = 30,000) and, partly, the metric artifact. **Not ruled out:** a structural difference between
per-agent discrete decisions and the ODE's continuous modulation of the force of infection.

**Consequences accepted in this spec:**
- Oscillation is **not** a scenario target and no scenario is designed around it.
- The gate rests on **peak-height reduction and final susceptible fraction**, which have been
  robust across every configuration tested.
- **Defining and validating a shape metric that works on stochastic ABM output is an explicit
  work item before the November gate**, not something to attempt at it. Until it exists, the
  project can measure *how much* behaviour changed the epidemic but not *what shape* it
  produced — and the latter is the stated contribution.

⚠️ Scenario separation figures in §3 were measured with the Weitz reference rule, not with
CBF (arm 1). They should be re-measured once CBF is implemented; there is no guarantee the
separation transfers.

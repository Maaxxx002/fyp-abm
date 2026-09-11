# CLAUDE.md — FYP CCDS26-0406

Read `docs/` before writing any code. `docs/Decision_Register.md` is authoritative; if
anything here conflicts with it, the register wins and this file should be corrected.

## What this project is

NTU Final Year Project comparing four ways of encoding agent decision-making in an epidemic
ABM, measured against an external referent that sits outside all four arms.

- **Arm 1** — rule-based (Gozzi's CBF)
- **Arm 2** — an LLM makes each decision
- **Arm 3** — an LLM writes the decision function once, with no simulation data
- **Arm 4** — a model distilled from arm 2's logs (stretch goal; may be dropped)
- **Referent** — Weitz et al. 2020 signature: awareness-driven behaviour shifts epidemics away
  from a single peak. Not an arm. Measured as the shift *relative to a no-behaviour control*.

**The single most important structural rule: the arms differ only in the decision function.**
Same population, same seeds, same perception vector, same scenarios. Any change that gives one
arm information another lacks breaks the entire comparison.

## Hard constraints — do not drift from these

1. **Never invent a parameter value.** Every constant traces to `docs/Sourcing_Pack_v3.md`.
   If a value is needed that isn't there, stop and say so rather than picking a plausible number.
2. **All four arms read the same `Perception` dataclass.** Arm 2 reads a deterministic text
   rendering of it. The renderer is total — every field appears exactly once, covered by a test.
3. **Ablation = removing a field from the dataclass**, which must propagate to rule and prompt
   together. Never implement ablation separately in two places.
4. **The disease is never named in the arm-2 prompt.** Arm 1's rule has no disease identity;
   naming it in arm 2 is an input asymmetry, not a decision-function difference.
5. **Agents never read their own latent compartment.** `own_health` is
   `never_ill` / `currently_ill` / `recovered`; E collapses into `never_ill` deliberately.
6. **The population is drawn once by quota and frozen.** Identical agents across every arm,
   scenario and seed.

## Settled numbers

| | Value | Source |
|---|---|---|
| N | 3,000 | measured floor, register C5/C7 |
| Run length | 600 days | |
| Initial infected | 10 agents | register D8 — larger seeds destroy the growth phase |
| Integration | **48 sub-steps/day**, `1 − exp(−rate·dt)` | measured convergence, register C9 (Gozzi's own default of 12 is insufficient for this model's extra H-compartment chain) |
| R₀ / latent / infectious | 3.0 / 2 d / 6 d | Weitz Table 1 |
| f_D | 0.01 flat (aggregate); per-agent from `IFR_10age` | Weitz / Gozzi |
| T_H | 14 d default | Weitz Fig 6 |
| Awareness signal | **28-day rolling mean** of reported deaths | register C7 |
| Detection rate | 0.7 | Gozzi |
| Death delay Δ | 14 d | Gozzi |
| Age structure | New York `pop_data_Nk.csv`, 10 bands | Gozzi repo |
| Population-weighted IFR | 0.9718% (vs Weitz's 1.000%) | computed |
| Scenarios | S1 R₀=3/T_H=14 · S2 R₀=2 · S3 T_H=28 | `docs/Scenario_Spec.md` |

⚠️ **Symbol collision.** Gozzi's `mu` = 1/infectious period, `eps` = 1/latent period. Weitz's
`μ` = 1/latent, `γ` = 1/infectious. Same letters, opposite meanings. Use explicit names
(`latent_period_days`, `infectious_period_days`) and never the bare Greek letters.

## Verification tests — write these before the model

**Test 1 — ODE convergence.** Behaviour off, well-mixed, N ≥ 100,000. Final susceptible
fraction must match the Weitz ODE to three decimals (0.0594 at R₀ = 3). This test caught a
discretisation bug that inflated R₀ to 3.257 and was invisible in single runs.

**Test 2 — mean-field recovery.** With a per-agent stay-home probability *q* and transmission
requiring both parties out, the population multiplier is `(1−q)²`. To recover Weitz's
`1/(1+(δ/δ_c)^k)`, use `q = 1 − (1 + (δ/δ_c)^k)^(−1/2)`. Verify against the ODE at large N.

**Test 3 — renderer totality.** Every `Perception` field appears in the rendered prompt exactly
once. Fails if a field is added to the dataclass and not to the renderer.

## Known unsolved problem

**There is no working shape metric.** The referent is a curve shape, and every peak-referenced
metric tried so far fails on stochastic output — Weitz's symmetry coefficient is undefined on
roughly half of awareness runs, because it is measured relative to a peak and the awareness
regime is defined by the absence of one. Peak height and final susceptible fraction are robust
and are the current gate. Finding a non-peak-referenced shape metric is open work; see register
D2, D7, D8.

Do not build analysis code that assumes the symmetry coefficient works.

**`experiments/abm.py` contradicts A20.** It uses a single daily step with raw-rate transitions,
not 12 sub-steps. It passes Test 1 because `p = rate` gives the correct mean dwell time, but the
distribution is geometric rather than exponential. Treat it as a pilot, not as the reference for
the integration scheme. Register E11/G3.

**Update:** switching integration schemes (12, then 24, then 48 sub-steps) did NOT close the
oscillation discrepancy (D6) — that hypothesis is disconfirmed (register G3). Separately, D9
shows the wave-count metric itself is unsourced and threshold-fragile even on the ODE. There is
currently no working shape metric of any kind. Do not attempt to fix D6 by further
integration-scheme changes; the cause is unknown.

**Resolved:** the substep count is now 48, not Gozzi's default of 12 (register C9). Measured
convergence: 12 substeps carries a 2.44% relative-error bias at N=100,000 (statistically real,
7.92 SEM from zero across 30 seeds), 24 gives 1.58%, 48 gives 0.05% — indistinguishable from
zero. Use 48 sub-steps in `src/`, and Test 1's 1% tolerance (G1) is now honestly achievable.

## Working conventions

- **If a question is a design or strategic choice (which metric to use, which parameter to
  change, whether a finding changes the plan) rather than an implementation detail, stop and
  report it back rather than deciding it inline.** This project is deliberately split: Claude
  Code implements and measures; the planning chat interprets and decides. Numeric results,
  test outcomes and code go back to the planning chat before being treated as settled.
- Label claims **[Fact]** / **[Speculation, confidence]** / **[Suggestion]**. Do not present
  speculation as fact.
- **Verify empirically before asserting.** Run the code, print the number. An uncalculated
  estimate is worse than no estimate — one was quoted in this project and had to be withdrawn.
- **Report the denominator.** When summarising across seeds, always print how many runs the
  statistic is defined on. A metric silently undefined on 28 of 30 runs once produced a
  headline result that was wrong.
- Own errors plainly and correct the register.
- Prefer small commits. Run the verification tests before claiming anything works.

## Repo layout

```
docs/          the four spec documents — read first, treat as authoritative
src/           model, arms, perception, rendering
tests/         verification tests 1-3 plus unit tests
experiments/   sweep scripts; outputs to results/
results/       generated, git-ignored
```

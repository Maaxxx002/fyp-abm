# Design spec — perception vector and synthetic population

Companion to `Sourcing_Pack_v3.md`. That document says what is sourced; this one says what
gets built. Where the literature runs out, this document says so rather than inventing a
citation.

Labels: **[Fact]** verified · **[Speculation]** with confidence · **[Suggestion]** ·
**[Unsourced]** a design choice with no literature behind it, requiring a stated defence.

---

## 1. Design principles

**P1 — One canonical vector, four consumers.** A single typed numeric structure is produced by
the simulator each time an agent in arms 2–4 decides. Arms 3 and 4 read the structure. Arm 2
reads a deterministic text rendering of the same structure. Arm 1 (CBF) has no discrete decision
points: it runs CBF's continuous per-sub-step rates on the same world signals (register A37,
A41). Nothing reaches any arm that is not in the vector.

**P1a — One shared world (register A37–A39, A42).** All arms act in one world with three
actions — stay home / precautions / normal — and the same physics. An action changes only the
agent's own susceptibility (normal ×1, precautions ×r, stay home ×0). Only agents who have never
been ill decide: currently-ill agents (A38) and recovered agents (A42) do not decide in any arm
and act normal; H and D agents do not decide. Arm 1 maps CBF's S → normal and S^B → precautions
and never chooses stay home.

**P2 — Arms differ in the function, not the inputs.** Every arm is offered all fields. Arm 1
happens to ignore most of them; that is what makes it the rule-based baseline, not a defect.

**P3 — Derive rather than invent.** Every attribute that can be a deterministic function of a
sourced primitive is one. Free distributions are a last resort and each is swept.

**P4 — Agents know only what they could know.** No agent reads its own latent compartment or
any population quantity that is not published in the model.

---

## 2. The perception vector

```python
@dataclass(frozen=True)
class Perception:
    # ---- dynamic: recomputed each decision ----
    # own_health is NOT a field of the main design (register A43) -- see §2a.
    deaths_28day_mean: float   # reported deaths/day, 28-day rolling mean (register A8)
    deaths_cumulative: int     # reported deaths since day 0
    deaths_28day_mean_7d_ago: float  # the same 28-day mean as it stood 7 days earlier (A47)
    # local_deaths_7d is NOT a field (A46): well-mixed model, agents have no contacts.
    current_action:    Literal["stay_home", "precautions", "normal"]  # own current action (A40)
    social_norm:       float   # [0,1] CBF's (S_normal + R) / N (A44); wording A48

    # ---- static: fixed at population construction ----
    age_band:          int     # 0..9, index into the IFR table
    vulnerability:     float   # = IFR_10age[age_band], deterministic
    occupation_flex:   float   # [0,1] ability to avoid going out
    response_efficacy: float   # [0,1] belief that precautions work

    # ---- context: identical for all agents ----
    population:        int     # 3000 (A7)
    day:               int
```

### Field justification

| Field | Source | Status |
|---|---|---|
| ~~`own_health`~~ | observation model, §2a | **Not in the main design (A43)**: constant `never_ill` for every deciding agent under A38 + A42. Kept in code for variant A (E21) |
| `current_action` | world state, not a determinant (A40) | **[Unsourced]** — needed so a re-asked agent knows its current choice; arm 1 ignores it |

| `deaths_28day_mean` | smoothing sourced (Weitz Methods, Gozzi `D_rep`, Urmi lag-0); **28-day length is a finite-population correction, not sourced** | partly sourced |
| `deaths_cumulative` | Weitz model C `D_c`; Gozzi EFB long-term term | **sourced** |
| `deaths_28day_mean_7d_ago` | trend for anchoring, §4; replaces `deaths_prev_period` (28-day mean lagged 28 days, reaching back 56 days) — E13 resolved by A47 | **[Unsourced]** 7-day horizon (motivation: S1's T10–90 ≈ 23 d, so a 28-day lag is too blunt); no normal-times baseline |
| ~~`local_deaths_7d`~~ | Gozzi CBF *local* mechanism (contact-weighted) | **Dropped (A46)**: well-mixed model, agents have no contacts |
| `social_norm` | CBF relaxation term, exactly `(S_normal + R)/N` (A44): susceptibles acting normal plus recovered, over N; stay home is not normal | **sourced**; rendered as "About X% of people in your town are going about their lives normally." (A48) — undercounts: infected agents acting normally are excluded |
| `age_band` | Gozzi `pop_data_Nk.csv` (New York) | **sourced** |
| `vulnerability` | Gozzi `IFR_10age` | **sourced** |
| `occupation_flex` | PMT response cost (β = −0.074) | **sourced construct, unsourced values** |
| `response_efficacy` | PMT response efficacy (β = +0.251) | **sourced construct, unsourced values** |

### 2a. The own-health observation model ⚠️

**[Unsourced]** Neither Weitz nor Gozzi models symptom awareness — their agents have no
self-knowledge because they aren't agents. Handing an agent its true SEIR compartment would
give it information no person has: an exposed-but-not-yet-infectious individual does not know
they are exposed.

The mapping used here:

| True compartment | `own_health` | decides? (main design) |
|---|---|---|
| S | `never_ill` | yes |
| E | `never_ill` | yes |
| I | `currently_ill` | **no** — acts normal in every arm (A38) |
| R | `recovered` | **no** — acts normal (A42) |
| H, D | — | no |

**Main design (A43):** since only `never_ill` agents decide, `own_health` is not a field of the
main-design Perception vector; the world uses this mapping only to decide who decides. The
field returns in variant A (ill agents may decide, E21).

E collapses into `never_ill` deliberately. This is a modelling choice, not a citation, and it
should be stated. [Speculation, medium confidence] It also matters more than it looks: it is
the mechanism by which pre-symptomatic agents keep circulating, which is a real driver of
spread and would be silently removed if agents read their true state.

---

## 3. What each arm consumes — the nested ladder

| Arm / model | fields used | of 9 |
|---|---|---|
| Weitz rule (simulator validation, not an arm) | `deaths_7day_mean` | 1 |
| **Arm 1 — CBF** | `deaths_28day_mean`; `social_norm` | 2 |
| Arms 2 / 3 / 4 | all | 9 |

(The 9 decision fields since A40/A43/A46/A47: `own_health` and `local_deaths_7d` out,
`current_action` in, `deaths_prev_period` → `deaths_28day_mean_7d_ago`. Arm 1 ignores
`current_action`; CBF keeps its S/S^B state internally.)

**[Suggestion] This ladder is the spine of the December ablation, and it is worth presenting
that way.** The ablation is not "which of my invented features matter." It is: a published
rule uses one input; a better published rule uses two; do the remaining seven, all drawn from
published determinants of protective behaviour, buy anything a two-input rule cannot? That
question has a clean answer either way and does not depend on any feature being *your* idea.

~~**Free A/B inside arm 1, no extra cost:** CBF's global mechanism versus its local mechanism
(`local_deaths_7d`).~~ **Lost (A46):** the model is well-mixed, so the local mechanism has no
contacts to act on and `local_deaths_7d` is dropped.

---

## 4. Rendering for arm 2, and the anchoring problem ⚠️

**[Unsourced, and the highest-risk choice in the design.]** Arm 1 divides the death signal by
`δ_c`, a calibration constant. Arm 2 has no such constant. An LLM shown
`deaths_28day_mean = 0.8` cannot know whether that is catastrophic or trivial. Whatever anchor
the prompt supplies is doing δ_c's job without δ_c's provenance.

**Decisions:**

1. **The disease is not named.** Arm 1's rule contains no disease identity; naming it in arm 2's
   prompt would give arm 2 information arm 1 lacks, which is an asymmetry of *inputs* rather
   than of decision *function*. ⚠️ [Speculation, high confidence] This does **not** eliminate
   contamination — an LLM will pattern-match R₀ ≈ 3 with a 1% fatality rate to COVID whether or
   not the word appears. It removes the explicit cue only. See §7.

2. **Counts, never per-capita rates.** "12 of the 3,000 people in your community have died"
   anchors scale concretely. "80 deaths per 100,000 per day" is both harder to reason about and
   the strongest available contamination cue, since it is the unit COVID reporting used.

3. **Trend, not just level.** `deaths_28day_mean_7d_ago` (A47) is carried purely so the
   prompt can express direction. Urmi et al. find the oscillatory component of behaviour tracks deaths at lag 0,
   so change is behaviourally load-bearing, and a level alone forces an absolute-scale
   judgement the model cannot make.

4. **The renderer is total and pure.** Every field appears exactly once; the function is
   deterministic and covered by a test asserting no field is silently dropped. Ablation is
   implemented by removing a field from the dataclass, which propagates to rule and prompt
   together with no chance of divergence.

Sketch, not final wording:

> You live in a town of 3,000 people. An infectious disease is spreading.
> Over the past four weeks an average of 0.8 people have died each day; a week ago that
> four-week average was 0.3. 12 people have died in total.
> About X% of people in your town are going about their lives normally.
> You are 71 years old. For someone your age this disease is fatal in about 4 cases in 100.
> You can work from home if you choose to. You are currently going out with precautions.
> Choose one: stay home / go out with precautions / go out without precautions.

⚠️ Since A43 the sketch has no "You have not been ill." line (it would be identical in every
prompt); since A46 it has no "person you know has died" line; it gains a `current_action` line
(A40); the trend line uses `deaths_28day_mean_7d_ago` (A47); the social-norm line is A48's
wording, which undercounts (infected agents acting normally are excluded from CBF's term).

⚠️ The `vulnerability` rendering is itself a fork. "4 cases in 100" and "your age band is 8"
and "your risk is high" will not produce the same behaviour from the same model. **[Suggestion]**
Fix the natural-frequency form ("4 in 100"), state it, and treat alternatives as a robustness
check on a subsample rather than a full arm.

---

## 5. Discretisation and caching — correcting an earlier claim

⚠️ **I previously told you caching identical perception vectors would yield roughly a 4×
saving in arm 2. That figure was not calculated and I should not have quoted it.**

The combinatorial state space under reasonable bins — 10 age bands × 3 occupation levels ×
3 efficacy levels × 3 health states × 8 death-level bins × 6 cumulative bins × 10 norm deciles
× 4 local-death bins — is about **5.2 × 10⁵** (518,400; corrected from 4.6 × 10⁵, register
D16), against roughly **5.4 × 10⁵** decisions across
three scenarios. On those numbers caching saves almost nothing.

(Since A43 the vector has no health-state field and since A46 no local-death field, so the
"× 3 health states" and "× 4 local-death bins" factors no longer apply; the figures above are left as originally computed. Since A38/A42 only never-ill agents
decide, so the decision count above is also an upper bound.)

The realised state space is far smaller, because the dynamic fields are heavily correlated with
each other and with time: cumulative deaths, the 28-day mean and the social norm all move
together. But by how much is an empirical question, and **it is answerable for free before any
money is spent on arm 2**:

> Run arm 1 at N = 3,000 for the full 600 days across all three scenarios, log the discretised
> perception vector at every decision point, and count distinct states.

(Arm 1 has no discrete decision points under A37/A41; read "decision point" as one per day per
never-ill agent, the agents who would be asked in arms 2–4.)

That is the measurement that decides whether caching is worth building. Do it before
committing the arm-2 budget, not after.

---

## 6. Population construction

**Draw once, by quota, freeze forever.** [Fact, measured at N=1,000; the effect shrinks with N
but does not vanish] Multinomial sampling of 1,000 agents
from New York's age structure gives a mean IFR of 0.970% with SD 0.057% — a 5.9% relative
swing, because 60+ agents are 22.7% of the population but produce 88.3% of deaths, and the
80+ band is only 42 agents. Quota sampling removes this noise entirely at no cost, and a frozen
population is required anyway so that all four arms face identical agents.

### Step 1 — age (sourced)

`data/new_york/population-data/pop_data_Nk.csv`, 10 bands. Counts at **N = 3,000**, by quota:

| Band | 0–9 | 10–19 | 20–24 | 25–29 | 30–39 | 40–49 | 50–59 | 60–69 | 70–79 | 80+ |
|---|---|---|---|---|---|---|---|---|---|---|
| Share | 11.02% | 11.23% | 6.25% | 8.00% | 15.72% | 12.59% | 12.52% | 11.11% | 7.34% | 4.23% |
| Agents | 330 | 337 | 187 | 240 | 472 | 378 | 376 | 333 | 220 | 127 |

(Largest-remainder rounding to exactly 3,000. Realised mean IFR **0.9718%**.)

### Step 2 — vulnerability (derived, zero free parameters)

`vulnerability = IFR_10age[age_band]`, from Gozzi `constants.py`:

| Band | 0–9 | 10–19 | 20–24 | 25–29 | 30–39 | 40–49 | 50–59 | 60–69 | 70–79 | 80+ |
|---|---|---|---|---|---|---|---|---|---|---|
| IFR | 0.00161% | 0.00695% | 0.0309% | 0.0309% | 0.0844% | 0.161% | 0.595% | 1.93% | 4.28% | 7.80% |
| Share of deaths | 0.0% | 0.1% | 0.1% | 0.3% | 1.4% | 2.1% | 7.7% | 22.1% | 32.3% | 33.9% |

Population-weighted IFR = **0.9716%**, against Weitz's flat f_D of 1.000% — within 3%. This is
what allows the aggregate death curve to reproduce the referent while individual agents differ
5,000-fold in vulnerability.

⚠️ Use `IFR_10age` (10 values) with `pop_data_Nk.csv` (10 bands). The 9-band `IFR` list in the
same file, quoted in sourcing pack v3, does **not** align with the population file.

### Step 3 — occupation flexibility (partly derived) **[Unsourced values]**

| Age band | Interpretation | `occupation_flex` |
|---|---|---|
| 0–19 | school-age | 0.5 (fixed) |
| 20–64 | working age | **free distribution** |
| 65+ | retired | 1.0 (fixed) |

Only the working-age distribution is free — one parameter, not ten. Proposed default:
Beta(2, 2) on [0, 1], i.e. centred with moderate spread. Sweep: Beta(1,1) uniform,
Beta(2,2) centred, Beta(0.5,0.5) polarised.

[Suggestion] Predict in advance that this feature falls out of the December ablation. It is a
response-cost proxy, and response cost is the weakest PMT construct (β = −0.074). A stated
prediction that then survives or fails is worth more than a feature quietly retained.

### Step 4 — response efficacy (free) **[Unsourced values]**

No published distribution exists. Beta(2, 2) default, same three-way sweep. This is the only
attribute with no derivation at all, and it exists because it is the second-strongest PMT
determinant (β = +0.251) and maps directly onto CBF's `r`.

### Free parameters, total: **two distributions**, both swept.

---

## 7. The contamination experiment

**[Suggestion]** A decision-level comparison, not a fifth arm. Sample a few thousand distinct
perception vectors from arm 1's logs; query the LLM on each under two framings — unnamed
disease versus named COVID-19 — and report decision agreement, plus agreement under a third
condition with vulnerability rendered differently (§4).

Cost is a few thousand calls, not hundreds of thousands. It converts the most obvious reviewer
objection to arm 2 — *is this reasoning from the state or retrieving 2020?* — from something you
must concede into a number you already measured.

---

## 8. Open decisions

| # | Decision | Status |
|---|---|---|
| 1 | Exact prompt wording | sketch only; needs drafting and a pilot |
| 2 | Number of bins per dynamic field | provisional; settle with the §5 state-count run |
| 3 | Persona count | still open — the distributions above may make explicit personas redundant |
| 4 | Re-decision cadence *p* | p = 0.3/day provisional for arms 2–4, unsourced (A41); sweep p ∈ {0.1, 0.3, 1} with **arm 3** once built, not arm 1 or a stand-in (E2). Arm 1 keeps continuous rates |
| 5 | Scenario definitions (the three runs) | not yet specified anywhere |

⚠️ Item 3 deserves attention. Steps 1–4 above already generate heterogeneous agents from a
sourced age structure plus two swept distributions. **[Speculation, medium confidence] An
explicit persona layer on top may be redundant, and redundant heterogeneity would make the
diversity metric harder to interpret**, not easier — you would not know whether measured
diversity came from the population construction or the persona text. Worth deciding
deliberately rather than by inheritance from the original plan.

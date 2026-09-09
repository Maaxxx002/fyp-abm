# Design spec — perception vector and synthetic population

Companion to `Sourcing_Pack_v3.md`. That document says what is sourced; this one says what
gets built. Where the literature runs out, this document says so rather than inventing a
citation.

Labels: **[Fact]** verified · **[Speculation]** with confidence · **[Suggestion]** ·
**[Unsourced]** a design choice with no literature behind it, requiring a stated defence.

---

## 1. Design principles

**P1 — One canonical vector, four consumers.** A single typed numeric structure is produced by
the simulator each time an agent decides. Arms 1, 3 and 4 read the structure. Arm 2 reads a
deterministic text rendering of the same structure. Nothing reaches any arm that is not in the
vector.

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
    own_health:        Literal["never_ill", "currently_ill", "recovered"]
    deaths_7day_mean:  float   # reported deaths/day, 7-day rolling mean
    deaths_cumulative: int     # reported deaths since day 0
    deaths_prev_week:  float   # same 7-day mean, lagged 7 days
    local_deaths_7d:   int     # reported deaths among this agent's contacts, last 7 d
    social_norm:       float   # [0,1] fraction of population currently taking precautions

    # ---- static: fixed at population construction ----
    age_band:          int     # 0..9, index into the IFR table
    vulnerability:     float   # = IFR_10age[age_band], deterministic
    occupation_flex:   float   # [0,1] ability to avoid going out
    response_efficacy: float   # [0,1] belief that precautions work

    # ---- context: identical for all agents ----
    population:        int     # 1000
    day:               int
```

### Field justification

| Field | Source | Status |
|---|---|---|
| `own_health` | observation model, §2a | **[Unsourced]** — see below |
| `deaths_7day_mean` | Weitz Methods (7-d rolling avg); Gozzi `D_rep`; Urmi lag-0 | **sourced** |
| `deaths_cumulative` | Weitz model C `D_c`; Gozzi EFB long-term term | **sourced** |
| `deaths_prev_week` | anchoring, §4 | **[Unsourced]** |
| `local_deaths_7d` | Gozzi CBF *local* mechanism (contact-weighted) | **sourced** |
| `social_norm` | CBF relaxation term `(S+R)/N` | **sourced** |
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

| True compartment | `own_health` |
|---|---|
| S | `never_ill` |
| E | `never_ill` |
| I | `currently_ill` |
| R | `recovered` |
| H, D | agent no longer decides |

E collapses into `never_ill` deliberately. This is a modelling choice, not a citation, and it
should be stated. [Speculation, medium confidence] It also matters more than it looks: it is
the mechanism by which pre-symptomatic agents keep circulating, which is a real driver of
spread and would be silently removed if agents read their true state.

---

## 3. What each arm consumes — the nested ladder

| Arm / model | fields used | of 10 |
|---|---|---|
| Weitz rule (simulator validation, not an arm) | `deaths_7day_mean` | 1 |
| **Arm 1 — CBF** | `deaths_7day_mean` *or* `local_deaths_7d`; `social_norm` | 2 |
| Arms 2 / 3 / 4 | all | 10 |

**[Suggestion] This ladder is the spine of the December ablation, and it is worth presenting
that way.** The ablation is not "which of my invented features matter." It is: a published
rule uses one input; a better published rule uses two; do the remaining eight, all drawn from
published determinants of protective behaviour, buy anything a two-input rule cannot? That
question has a clean answer either way and does not depend on any feature being *your* idea.

**Free A/B inside arm 1, no extra cost:** CBF's global mechanism (`deaths_7day_mean`) versus
its local mechanism (`local_deaths_7d`). Both published, both implemented in Gozzi's code.

---

## 4. Rendering for arm 2, and the anchoring problem ⚠️

**[Unsourced, and the highest-risk choice in the design.]** Arm 1 divides the death signal by
`δ_c`, a calibration constant. Arm 2 has no such constant. An LLM shown
`deaths_7day_mean = 0.8` cannot know whether that is catastrophic or trivial. Whatever anchor
the prompt supplies is doing δ_c's job without δ_c's provenance.

**Decisions:**

1. **The disease is not named.** Arm 1's rule contains no disease identity; naming it in arm 2's
   prompt would give arm 2 information arm 1 lacks, which is an asymmetry of *inputs* rather
   than of decision *function*. ⚠️ [Speculation, high confidence] This does **not** eliminate
   contamination — an LLM will pattern-match R₀ ≈ 3 with a 1% fatality rate to COVID whether or
   not the word appears. It removes the explicit cue only. See §7.

2. **Counts, never per-capita rates.** "12 of the 1,000 people in your community have died"
   anchors scale concretely. "80 deaths per 100,000 per day" is both harder to reason about and
   the strongest available contamination cue, since it is the unit COVID reporting used.

3. **Trend, not just level.** `deaths_prev_week` is carried purely so the prompt can express
   direction. Urmi et al. find the oscillatory component of behaviour tracks deaths at lag 0,
   so change is behaviourally load-bearing, and a level alone forces an absolute-scale
   judgement the model cannot make.

4. **The renderer is total and pure.** Every field appears exactly once; the function is
   deterministic and covered by a test asserting no field is silently dropped. Ablation is
   implemented by removing a field from the dataclass, which propagates to rule and prompt
   together with no chance of divergence.

Sketch, not final wording:

> You live in a community of 1,000 people. An infectious disease is spreading.
> Over the past week an average of 0.8 people have died each day; the week before it was 0.3.
> 12 people have died in total. 1 person you know has died in the past week.
> About 34% of people are currently taking precautions.
> You are 71 years old. For someone your age this disease is fatal in about 4 cases in 100.
> You have not been ill. You can work from home if you choose to.
> Choose one: stay home / go out with precautions / go out without precautions.

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
× 4 local-death bins — is about **4.6 × 10⁵**, against roughly **5.4 × 10⁵** decisions across
three scenarios. On those numbers caching saves almost nothing.

The realised state space is far smaller, because the dynamic fields are heavily correlated with
each other and with time: cumulative deaths, the 7-day mean and the social norm all move
together. But by how much is an empirical question, and **it is answerable for free before any
money is spent on arm 2**:

> Run arm 1 at N = 1,000 for the full 600 days across all three scenarios, log the discretised
> perception vector at every decision point, and count distinct states.

That is the measurement that decides whether caching is worth building. Do it before
committing the arm-2 budget, not after.

---

## 6. Population construction

**Draw once, by quota, freeze forever.** [Fact, measured] Multinomial sampling of 1,000 agents
from New York's age structure gives a mean IFR of 0.970% with SD 0.057% — a 5.9% relative
swing, because 60+ agents are 22.7% of the population but produce 88.3% of deaths, and the
80+ band is only 42 agents. Quota sampling removes this noise entirely at no cost, and a frozen
population is required anyway so that all four arms face identical agents.

### Step 1 — age (sourced)

`data/new_york/population-data/pop_data_Nk.csv`, 10 bands. Counts at N = 1,000, by quota:

| Band | 0–9 | 10–19 | 20–24 | 25–29 | 30–39 | 40–49 | 50–59 | 60–69 | 70–79 | 80+ |
|---|---|---|---|---|---|---|---|---|---|---|
| Share | 11.02% | 11.23% | 6.25% | 8.00% | 15.72% | 12.59% | 12.52% | 11.11% | 7.34% | 4.23% |
| Agents | 110 | 112 | 62 | 80 | 157 | 126 | 125 | 111 | 74 | 43 |

(Largest-remainder rounding to exactly 1,000.)

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
| 4 | Re-decision cadence *p* | sweep in arm 1 (free) before committing arm-2 budget |
| 5 | Scenario definitions (the three runs) | not yet specified anywhere |

⚠️ Item 3 deserves attention. Steps 1–4 above already generate heterogeneous agents from a
sourced age structure plus two swept distributions. **[Speculation, medium confidence] An
explicit persona layer on top may be redundant, and redundant heterogeneity would make the
diversity metric harder to interpret**, not easier — you would not know whether measured
diversity came from the population construction or the persona text. Worth deciding
deliberately rather than by inheritance from the original plan.

"""
The frozen, quota-drawn synthetic population (Design_Spec_Perception_and_Population.md Sec 6;
CLAUDE.md hard constraint 6: "the population is drawn once by quota and frozen... identical
agents across every arm, scenario and seed").

Produces only the STATIC subset of Perception's fields (age_band, vulnerability,
occupation_flex, response_efficacy). Dynamic fields (deaths_28day_mean, social_norm, ...) and
the context fields (population, day) are supplied per-decision by the simulation/rendering
layer, which is not built yet -- see src/perception.py and this build's report for what is and
isn't in scope.

⚠️ One design choice this module makes explicit rather than silent (see the accompanying
report): Design_Spec Sec 6 Step 3 splits occupation_flex by age into school-age (0-19, fixed),
working-age (20-64, free Beta draw) and retired (65+, fixed) -- but the sourced 10-band age
structure this project uses (0-9, 10-19, 20-24, 25-29, 30-39, 40-49, 50-59, 60-69, 70-79, 80+)
has no band edge at 65; band 7 (60-69) straddles it. `build_population`'s
`retired_age_bands`/`school_age_bands` defaults below pick ONE resolution (band 7 = retired,
matching the only prior precedent in this repo, experiments/state_count_check.py, which itself
labels the choice "a stand-in approximation, not a sourced rule") -- NOT a settled decision.
Override the arguments once the planning chat picks one.
"""
from dataclasses import dataclass

import numpy as np

# Design_Spec Sec 6 Step 1: New York age-band quota (Gozzi pop_data_Nk.csv), exact agent
# counts for N=3,000 -- these are the design spec's OWN computed integers (largest-remainder
# rounding of the sourced shares), used verbatim rather than re-derived here: re-deriving from
# the printed 2-decimal-percent shares does not reproduce them exactly (a 3-way tie in the
# remainder step resolves two different ways), and the underlying raw CSV is not vendored in
# this repo, so re-deriving without it would mean inventing a tie-break. Verified below (test)
# to reproduce the register's own published population-weighted IFR (0.9718%, CLAUDE.md /
# Decision_Register B2) to 4 decimal places, which stands as the sourcing check.
AGE_BAND_LABELS = [
    "0-9", "10-19", "20-24", "25-29", "30-39",
    "40-49", "50-59", "60-69", "70-79", "80+",
]
AGE_BAND_COUNTS_N3000 = [330, 337, 187, 240, 472, 378, 376, 333, 220, 127]
N_AGE_BANDS = len(AGE_BAND_LABELS)

# Design_Spec Sec 6 Step 2: IFR_10age (Gozzi constants.py), paired with pop_data_Nk.csv's
# 10-band structure -- NOT the 9-band `IFR` list quoted elsewhere in Sourcing_Pack_v3.md, which
# does not align with this population file (Decision_Register B5/D5). Values as fractions
# (e.g. 0.00161% -> 0.0000161).
IFR_10AGE = np.array([
    0.0000161,  # 0-9
    0.0000695,  # 10-19
    0.000309,   # 20-24
    0.000309,   # 25-29
    0.000844,   # 30-39
    0.00161,    # 40-49
    0.00595,    # 50-59
    0.0193,     # 60-69
    0.0428,     # 70-79
    0.0780,     # 80+
])

# Design_Spec Sec 6 Step 3 provisional default (see module docstring's caveat): 0-9/10-19
# school-age (fixed 0.5), 60-69/70-79/80+ retired (fixed 1.0), the rest working-age (free draw).
DEFAULT_SCHOOL_AGE_BANDS = frozenset({0, 1})
DEFAULT_RETIRED_AGE_BANDS = frozenset({7, 8, 9})

# Design_Spec Sec 6 Steps 3-4: proposed default, explicitly flagged for a later sweep
# (Beta(1,1) uniform / Beta(2,2) centred / Beta(0.5,0.5) polarised) -- not hardcoded into the
# function below, only used as its default argument.
DEFAULT_OCCUPATION_FLEX_BETA = (2.0, 2.0)
DEFAULT_RESPONSE_EFFICACY_BETA = (2.0, 2.0)


@dataclass(frozen=True)
class Population:
    """N agents' frozen static attributes -- the subset of Perception's fields fixed at
    construction (Design_Spec Sec 6). Arrays are length N and index-aligned: agent i's
    attributes are `age_band[i]`, `vulnerability[i]`, `occupation_flex[i]`, `response_efficacy[i]`.
    """
    age_band: np.ndarray            # int64, shape (N,), 0..9
    vulnerability: np.ndarray       # float64, shape (N,) = IFR_10age[age_band]
    occupation_flex: np.ndarray     # float64, shape (N,), [0,1]
    response_efficacy: np.ndarray   # float64, shape (N,), [0,1]

    def __len__(self):
        return len(self.age_band)


def build_population(
    N=3000,
    seed=0,
    occupation_flex_beta=DEFAULT_OCCUPATION_FLEX_BETA,
    response_efficacy_beta=DEFAULT_RESPONSE_EFFICACY_BETA,
    school_age_bands=DEFAULT_SCHOOL_AGE_BANDS,
    retired_age_bands=DEFAULT_RETIRED_AGE_BANDS,
):
    """Build the frozen quota-drawn population (Design_Spec Sec 6).

    Age bands are an exact quota (AGE_BAND_COUNTS_N3000), not a random draw -- this is what
    "quota-drawn" means as opposed to the multinomial sampling the design spec rejects (Sec 6:
    multinomial sampling of 1,000 agents gave a 5.9% relative swing in mean IFR; quota removes
    that noise entirely). `vulnerability` is a zero-free-parameter deterministic function of
    `age_band`. Only `occupation_flex` (working-age agents) and `response_efficacy` (everyone)
    involve randomness, via `seed`, and only because Design_Spec Sec 6 Steps 3-4 name these as
    the project's two free distributions, both to be swept.

    Call this ONCE with a fixed seed and freeze the result -- CLAUDE.md hard constraint 6
    requires identical agents across every arm, scenario and simulation seed; `seed` here is a
    population-construction seed, unrelated to and not to be confused with a disease-run seed
    (src/model.py's `run`/`run_weitz_behaviour`/`run_cbf_behaviour` seeds).

    Raises NotImplementedError for any N other than 3,000: no other N has a sourced quota
    table, and inventing a generic rounding rule for arbitrary N is exactly the kind of
    unsourced parameter CLAUDE.md's hard constraint 1 rules out.
    """
    if N != 3000:
        raise NotImplementedError(
            f"No sourced age-band quota table exists for N={N}. "
            "AGE_BAND_COUNTS_N3000 is sourced only for the project's settled N=3,000 "
            "(register A7/D13); extending to other N would require inventing a rounding rule."
        )

    age_band = np.concatenate([
        np.full(count, band, dtype=np.int64)
        for band, count in enumerate(AGE_BAND_COUNTS_N3000)
    ])
    vulnerability = IFR_10AGE[age_band]

    rng = np.random.default_rng(seed)

    is_school = np.isin(age_band, list(school_age_bands))
    is_retired = np.isin(age_band, list(retired_age_bands))
    is_working = ~is_school & ~is_retired

    occupation_flex = np.empty(N, dtype=np.float64)
    occupation_flex[is_school] = 0.5
    occupation_flex[is_retired] = 1.0
    n_working = int(np.count_nonzero(is_working))
    occupation_flex[is_working] = rng.beta(*occupation_flex_beta, size=n_working)

    response_efficacy = rng.beta(*response_efficacy_beta, size=N)

    return Population(
        age_band=age_band,
        vulnerability=vulnerability,
        occupation_flex=occupation_flex,
        response_efficacy=response_efficacy,
    )

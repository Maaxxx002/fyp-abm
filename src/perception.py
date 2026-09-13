"""
The Perception vector -- the single canonical decision-input structure every arm is offered
(Design_Spec_Perception_and_Population.md Sec 1-2, principle P1).

P1: one typed structure, produced by the simulator each time an agent decides. Arms 1, 3, 4
read it directly; arm 2 reads a deterministic text rendering of the same structure (not built
yet -- the renderer is explicitly out of scope for this module, Design_Spec Sec 4).
P2: arms differ in which fields their decision FUNCTION uses, never in which fields they are
shown (CLAUDE.md hard constraint 2/3).
P4: agents never read their own latent compartment or any unpublished population quantity
(CLAUDE.md hard constraint 5) -- `own_health` is the published observation, not the true SEIR
state.

This module defines the SHAPE only. Nothing here computes a Perception from a running
simulation -- that is the (not-yet-built) rendering/arm layer, and two of the fields below
(`deaths_prev_period`, `local_deaths_7d`) cannot be correctly populated yet because their exact
definitions are still open (see field notes and the report accompanying this build).
"""
from dataclasses import dataclass
from typing import Literal

OwnHealth = Literal["never_ill", "currently_ill", "recovered"]


@dataclass(frozen=True)
class Perception:
    """One agent's full decision-input vector on one day.

    Every field is sourced or explicitly flagged where it is not (Design_Spec Sec 2's
    field-justification table). An agent in H or D does not decide, so no Perception is ever
    constructed for that state (Design_Spec Sec 2a).
    """

    # ---- dynamic: recomputed each decision ----

    own_health: OwnHealth
    # Observation model (Design_Spec Sec 2a, [Unsourced] but fully specified, not a free
    # parameter): true S or E -> "never_ill" (E collapses into "never_ill" deliberately --
    # CLAUDE.md hard constraint 5, since a not-yet-infectious agent has no symptoms to notice);
    # true I -> "currently_ill"; true R -> "recovered".

    deaths_28day_mean: float
    # Reported deaths/day, 28-day rolling mean, raw count (not per-capita). Smoothing sourced
    # (Weitz Methods / Gozzi D_rep / Urmi lag-0); the 28-day length is a finite-population
    # correction (register A8/C7), confirmed correct for CBF's own mechanism in register C17.

    deaths_cumulative: int
    # Reported deaths since day 0. Sourced: Weitz model C's D_c, Gozzi EFB's long-term term.

    deaths_prev_period: float
    # The same 28-day mean, lagged -- carried so a renderer can express a trend, not just a
    # level (Design_Spec Sec 4 point 3; Urmi et al.'s lag-0 behavioural tracking of deaths).
    # ⚠️ UNRESOLVED (Design_Spec register E13): lagging a further 28 days reaches back 56 days
    # total, which may be too stale to carry useful direction; a shorter trend horizon than the
    # level horizon is an alternative but asymmetric. NOT decided -- do not populate this field
    # from a running simulation until E13 is settled.

    local_deaths_7d: int
    # Reported deaths among this agent's contacts in the last 7 days -- Gozzi CBF's *local*,
    # contact-weighted mechanism (sourced). Requires a contact-network structure that does not
    # exist in src/model.py's well-mixed disease model (register A5/C15) -- cannot be correctly
    # populated until that structure (or an explicit decision to drop this field) exists.

    social_norm: float
    # [0,1] fraction of the population currently taking precautions. Sourced: CBF's relaxation
    # term (S+R)/N.

    # ---- static: fixed once at population construction, frozen for the agent's lifetime ----

    age_band: int
    # 0..9, index into IFR_10age. Sourced: Gozzi pop_data_Nk.csv (New York), Design_Spec Sec 6
    # Step 1. See src/population.py for the quota construction.

    vulnerability: float
    # = IFR_10age[age_band], zero free parameters. Sourced: Gozzi constants.py IFR_10age,
    # Design_Spec Sec 6 Step 2.

    occupation_flex: float
    # [0,1], ability to avoid going out. Sourced construct (PMT response cost, beta=-0.074);
    # UNSOURCED VALUES -- school-age/retired bands fixed, working-age a free Beta distribution,
    # provisional default Beta(2,2) (Design_Spec Sec 6 Step 3), swept later. See
    # src/population.py for the age-band boundary caveat flagged in this build's report.

    response_efficacy: float
    # [0,1], belief that precautions work. Sourced construct (PMT response efficacy,
    # beta=+0.251), maps to CBF's `r`. UNSOURCED VALUES -- no published distribution exists;
    # provisional default Beta(2,2) for every agent (Design_Spec Sec 6 Step 4), swept later.

    # ---- context: identical for every agent on a given day ----

    population: int
    # N, the frozen population size (register A7/D13: settled at 3,000). The design spec's own
    # field comment ("# 1000") is a stale leftover from before A7 revised N upward (D3) -- this
    # field should always carry the actual running N, not that literal value.

    day: int
    # Simulation day, 0-indexed, matching src/model.py's daily loop.

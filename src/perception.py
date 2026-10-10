"""
The Perception vector -- the single canonical decision-input structure every arm is offered
(Design_Spec_Perception_and_Population.md Sec 1-2, principle P1).

P1: one typed structure, produced by the simulator each time an agent decides. Arms 1, 3, 4
read it directly; arm 2 reads a deterministic text rendering of the same structure (not built
yet -- the renderer is explicitly out of scope for this module, Design_Spec Sec 4).
P2: arms differ in which fields their decision FUNCTION uses, never in which fields they are
shown (CLAUDE.md hard constraint 2/3).
P4: agents never read their own latent compartment or any unpublished population quantity
(CLAUDE.md hard constraint 5).

own_health is NOT a field of the main-design vector (register A43): ill agents do not decide
(A38) and recovered agents do not decide (A42), so every deciding agent is never_ill and the
field would be constant. The observation model and its type are kept -- `OwnHealth` below and
`shared_world.own_health_of` -- because the field returns if ill agents are later allowed to
decide (register E21, variant A).

local_deaths_7d is NOT a field (register A46): the model is well-mixed, so agents have no
contacts. deaths_prev_period was replaced by deaths_28day_mean_7d_ago (A47, resolving E13).

This module defines the SHAPE only. Nothing here computes a Perception from a running
simulation -- that is the (not-yet-built) rendering/arm layer.
"""
from dataclasses import dataclass
from typing import Literal

# Kept for variant A (E21); not a field of the main-design Perception (A43). Observation model
# (Design_Spec Sec 2a): true S or E -> "never_ill" (E collapses deliberately), I ->
# "currently_ill", R -> "recovered".
OwnHealth = Literal["never_ill", "currently_ill", "recovered"]
Action = Literal["stay_home", "precautions", "normal"]


@dataclass(frozen=True)
class Perception:
    """One agent's full decision-input vector on one day.

    Every field is sourced or explicitly flagged where it is not (Design_Spec Sec 2's
    field-justification table). An agent in H or D does not decide, so no Perception is ever
    constructed for that state (Design_Spec Sec 2a). Since register A38/A42, agents in I
    ("currently_ill") and R ("recovered") do not decide either, in any arm.
    """

    # ---- dynamic: recomputed each decision ----

    deaths_28day_mean: float
    # Reported deaths/day, 28-day rolling mean, raw count (not per-capita). Smoothing sourced
    # (Weitz Methods / Gozzi D_rep / Urmi lag-0); the 28-day length is a finite-population
    # correction (register A8/C7), confirmed correct for CBF's own mechanism in register C17.

    deaths_cumulative: int
    # Reported deaths since day 0. Sourced: Weitz model C's D_c, Gozzi EFB's long-term term.
    # ⚠️ Type mismatch, reported not fixed: under A25 reported deaths = 0.7 x realised, so the
    # cumulative reported count is generally not an integer.

    deaths_28day_mean_7d_ago: float
    # The same 28-day mean of reported deaths as it stood 7 days earlier (register A47, resolving
    # E13). Carried so a renderer can express the direction of change with low noise and a
    # one-week lag (Design_Spec Sec 4 point 3). The 7-day horizon is UNSOURCED (motivation: S1's
    # T10-90 is ~23 days, so a 28-day lag is too blunt). No normal-times baseline is added.

    current_action: Action
    # The agent's own current action in the shared world (register A37/A40): one of
    # "stay_home" / "precautions" / "normal". Offered to every arm; arm 1 (CBF) ignores it
    # because CBF keeps its S/S^B state internally. Without it a re-asked LLM has no memory of
    # its current choice. Not sourced from either paper -- it is world state, not a determinant.

    social_norm: float
    # [0,1] CBF's exact relaxation term (S_normal + R) / N (register A44): susceptibles acting
    # normal plus all recovered agents, over N (the dead stay in N). Staying home does not count
    # as normal; recovered count as normal. It is NOT "the fraction taking precautions" -- see
    # A44 for what this means for the arm-2 wording.

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
    # N, the frozen population size (register A7/D13: settled at 3,000). Always the actual
    # running N.

    day: int
    # Simulation day, 0-indexed, matching src/model.py's daily loop.

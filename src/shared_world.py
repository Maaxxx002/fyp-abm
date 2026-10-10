"""
The shared world every arm runs in (register A37-A45).

One world, three actions, one physics. Arms differ only in the decision function that sets
each agent's action (CLAUDE.md: "the arms differ only in the decision function").

Actions and their physics (register A39):
  normal       susceptibility multiplier 1
  precautions  susceptibility multiplier r = 0.5 (CBF's S^B effect: one-sided, flat r, A29)
  stay_home    susceptibility multiplier 0 (cannot be infected while at home)
A susceptible agent's infection hazard per sub-step is transmission_rate * (I/N) * m. Actions
change only the agent's OWN susceptibility; infectiousness is never reduced, because
currently-ill agents do not decide and always act normal (register A38). A23's two-sided stay
home therefore never acts on a spreader here (A39 records the relationship).

Who decides (A38): agents whose own_health is "currently_ill" (true compartment I) do not
decide in any arm and are reset to `normal` on becoming infectious. H and D agents do not
decide (Design_Spec Sec 2a). Recovered agents do not decide either and act normal (A42), which
matches CBF counting R as normal. So every deciding agent is never_ill, and own_health is not
in the main-design Perception (A43); `own_health_of` stays because the world uses it to decide
who is eligible, and the field returns if ill agents are later allowed to decide (E21).

social_norm (A44) = CBF's exact relaxation term (S_normal + R) / N: susceptibles acting normal
plus all recovered, over N. Staying home does not count as normal. Arm 1's relaxation rate is
mu_B times this same quantity.

Two kinds of decision function:
  * "hazard" (arm 1, CBF): continuous per-sub-step switching rates between actions, raced
    against infection exactly as run_cbf_behaviour does (same hazards, same competing-hazard
    order, same random-number order). Arm 1 never uses stay_home.
  * "discrete" (arms 2-4, forced test policies): actions are set at day 0 and, if the
    function re-decides, each eligible agent is re-asked at the start of each day with
    probability `redecide_prob` (A41: p = 0.3/day PROVISIONAL and UNSOURCED, so it is
    deliberately not defaulted here).

Random numbers. The disease stream (`np.random.default_rng(seed)`) is consumed exactly as in
model.run() for discrete functions and exactly as in model.run_cbf_behaviour() for the hazard
function, so: always-normal == run() and arm 1 == run_cbf_behaviour(), bit for bit, on the same
seed (tests/test_shared_world.py). Decisions draw from a separate stream seeded from
(seed, 1), so a decision function never shifts the disease stream.
"""
import numpy as np

from model import S, E, I, H, R, D, _check_f_D

NORMAL, PRECAUTIONS, STAY_HOME = 0, 1, 2
ACTION_NAMES = ("normal", "precautions", "stay_home")

NEVER_ILL, CURRENTLY_ILL, RECOVERED, NOT_DECIDING = 0, 1, 2, 3
OWN_HEALTH_NAMES = ("never_ill", "currently_ill", "recovered", None)

# r: Gozzi's demo value (Sourcing_Pack_v3.md Sec 2b; register C13), flat for every agent (A29).
PRECAUTION_MULTIPLIER = 0.5


def own_health_of(state):
    """Observation model (Design_Spec Sec 2a; CLAUDE.md hard constraint 5). S and E -> never_ill
    (E collapses deliberately), I -> currently_ill, R -> recovered, H/D -> not deciding."""
    out = np.full(state.shape, NOT_DECIDING, dtype=np.int8)
    out[(state == S) | (state == E)] = NEVER_ILL
    out[state == I] = CURRENTLY_ILL
    out[state == R] = RECOVERED
    return out


class DecisionFunction:
    """Base class. `mode` is "hazard" or "discrete"."""
    mode = "discrete"
    redecides = False

    def initial_actions(self, own_health, rng):
        """Day-0 actions, length N. Default: everyone normal (CBF starts with S^B empty)."""
        return np.full(own_health.shape, NORMAL, dtype=np.int8)

    def decide(self, day, agents, view, rng):
        """Discrete mode, re-deciding functions only: return actions for `agents`."""
        raise NotImplementedError

    def transitions(self, view):
        """Hazard mode only: ordered list of (from_action, to_action, rate per day)."""
        raise NotImplementedError


class AlwaysNormal(DecisionFunction):
    """No behaviour: every agent normal for the whole run (Check 1; arms 2-4's control)."""


class ForcedPrecautions(DecisionFunction):
    """Every agent who is never_ill at day 0 takes precautions for the whole run (Check 2a/c)."""

    def initial_actions(self, own_health, rng):
        a = np.full(own_health.shape, NORMAL, dtype=np.int8)
        a[own_health == NEVER_ILL] = PRECAUTIONS
        return a


class ForcedStayHomeFraction(DecisionFunction):
    """A fixed random `fraction` of the agents who are never_ill at day 0 stay home for the
    whole run; the rest act normal (Check 2b). Drawn once from the decision stream."""

    def __init__(self, fraction):
        self.fraction = fraction

    def initial_actions(self, own_health, rng):
        a = np.full(own_health.shape, NORMAL, dtype=np.int8)
        idx = np.flatnonzero(own_health == NEVER_ILL)
        k = int(round(self.fraction * len(idx)))
        a[rng.choice(idx, k, replace=False)] = STAY_HOME
        return a


class CBFArm1(DecisionFunction):
    """Arm 1: Gozzi's CBF, unchanged (register A3, A24-A29, A37). S -> normal, S^B -> precautions;
    never stay_home. Rates exactly as run_cbf_behaviour:
        adoption   normal -> precautions   beta_B * (1 - exp(-gamma_beh * D(t)))
        relaxation precautions -> normal   mu_B * (S + R) / N, with S = susceptibles acting
                                           normal and R = all recovered agents (CBF counts R
                                           as not-cautious)
    D(t) is the world's 28-day mean of reported deaths (A24/A25). Arm 1 ignores every
    Perception field it does not use, including current_action (A40): its state is the action
    array itself."""
    mode = "hazard"

    def __init__(self, beta_B=0.5, mu_B=0.01, gamma_beh=1.0):
        self.beta_B, self.mu_B, self.gamma_beh = beta_B, mu_B, gamma_beh

    def transitions(self, view):
        adoption_rate = self.beta_B * (1.0 - np.exp(-self.gamma_beh * view["awareness_signal"]))
        relax_rate = self.mu_B * (view["n_S_normal"] + view["n_R"]) / view["N"]
        return [(NORMAL, PRECAUTIONS, adoption_rate), (PRECAUTIONS, NORMAL, relax_rate)]


def run_shared_world(N, seed, decision, days=600, seeds_infected=10,
                     R0=3.0, latent_period_days=2.0, infectious_period_days=6.0,
                     f_D=0.01, T_H=14.0, n_substeps=48,
                     window=28, detection_rate=0.7,
                     precaution_multiplier=PRECAUTION_MULTIPLIER,
                     redecide_prob=None, stop_deciding_when_no_infection=False,
                     social_norm_def="cbf"):
    """Run one epidemic in the shared world with `decision` setting every agent's action.

    Disease, integration and death signal are those of run_cbf_behaviour (Weitz model B,
    48 sub-steps, 1 - exp(-rate*dt); 28-day mean of reported deaths over days strictly before
    today, reported = detection_rate * realised, no truncation, A24/A25). f_D is a scalar or a
    per-agent array (A26).

    stop_deciding_when_no_infection (A55): if True, no agent is re-asked on a day that starts
    with E + I = 0 (no further infection is possible). The decision stream is then not drawn
    on that day; the disease stream is unaffected.
    social_norm_def: "cbf" (A44, the default) = (S_normal + R) / N. "alive_not_home_not_H"
    (C39 supplementary only) = agents acting normal / agents in S, E, I or R who are not
    staying home. Only what decision functions are shown changes; arm 1's relaxation rate
    uses its own counts and is unaffected.
    """
    if social_norm_def not in ("cbf", "alive_not_home_not_H"):
        raise ValueError(f"unknown social_norm_def {social_norm_def!r}")
    if decision.mode == "discrete" and decision.redecides:
        if redecide_prob is None:
            raise ValueError("a re-deciding function needs redecide_prob set explicitly "
                             "(A41: p = 0.3/day is provisional and unsourced)")
    f_D = _check_f_D(f_D, N)
    mult = (1.0, float(precaution_multiplier), 0.0)  # indexed by action code

    dt = 1.0 / n_substeps
    latent_rate = 1.0 / latent_period_days
    infectious_rate = 1.0 / infectious_period_days
    death_delay_rate = 1.0 / T_H
    transmission_rate = R0 * infectious_rate

    p_e_to_i = 1 - np.exp(-latent_rate * dt)
    p_i_to_leave = 1 - np.exp(-infectious_rate * dt)
    p_h_to_d = 1 - np.exp(-death_delay_rate * dt)

    rng = np.random.default_rng(seed)                    # disease stream
    drng = np.random.default_rng([seed, 1])              # decision stream
    state = np.zeros(N, dtype=np.int8)
    state[rng.choice(N, seeds_infected, replace=False)] = I
    action = np.asarray(decision.initial_actions(own_health_of(state), drng), dtype=np.int8)
    action[state == I] = NORMAL                           # A38

    daily_deaths = np.zeros(days)
    reported_deaths = np.zeros(days)
    awareness_signal = np.zeros(days)
    daily_incidence = np.zeros(days)
    prevalence = np.zeros(days)
    exposed = np.zeros(days)
    recovered = np.zeros(days)
    S_frac = np.zeros(days)
    S_by_action = np.zeros((days, 3))
    E_by_action = np.zeros((days, 3))
    social_norm = np.zeros(days)

    for t in range(days):
        window_start = max(0, t - window)
        D_mean = reported_deaths[window_start:t].mean() if t > 0 else 0.0
        awareness_signal[t] = D_mean
        if social_norm_def == "cbf":
            social_norm[t] = (np.count_nonzero((state == S) & (action == NORMAL))
                              + np.count_nonzero(state == R)) / N  # A44, start of day t
        else:
            live = (state == S) | (state == E) | (state == I) | (state == R)
            out_ = live & (action != STAY_HOME)
            social_norm[t] = np.count_nonzero(out_ & (action == NORMAL)) / np.count_nonzero(out_)

        if (decision.mode == "discrete" and decision.redecides
                and not (stop_deciding_when_no_infection
                         and np.count_nonzero((state == E) | (state == I)) == 0)):
            oh = own_health_of(state)
            eligible = oh == NEVER_ILL                   # A38 (not ill), A42 (not recovered)
            agents = np.flatnonzero(eligible & (drng.random(N) < redecide_prob))
            if len(agents):
                # World-side data a Perception is built from. own_health is included only so
                # the eligibility rule can be checked; it is not in the main-design Perception
                # (A43).
                view = dict(day=t, N=N, awareness_signal=D_mean,
                            reported_deaths=reported_deaths[:t].copy(),
                            social_norm=social_norm[t], own_health=oh, action=action.copy())
                action[agents] = decision.decide(t, agents, view, drng)

        if decision.mode == "hazard":
            covered = [a for a, _, _ in decision.transitions(
                dict(N=N, awareness_signal=D_mean, n_S_normal=0, n_R=0))]
            if np.any((state == S) & ~np.isin(action, covered)):
                raise AssertionError("hazard-mode function leaves a susceptible's action uncovered")

        day_new_e = 0
        day_new_d = 0
        for _ in range(n_substeps):
            n_infectious = np.count_nonzero(state == I)
            foi = transmission_rate * n_infectious / N

            if decision.mode == "hazard":
                # Competing hazards per action, in the decision function's order (CBF:
                # normal first, then precautions) -- run_cbf_behaviour's exact draw order.
                s_mask = (state == S)
                view = dict(N=N, awareness_signal=D_mean,
                            n_S_normal=np.count_nonzero(s_mask & (action == NORMAL)),
                            n_R=np.count_nonzero(state == R))
                moves = []
                for from_a, to_a, switch_rate in decision.transitions(view):
                    foi_a = mult[from_a] * foi
                    rate_total = switch_rate + foi_a
                    if rate_total > 0:
                        p_leave = 1 - np.exp(-rate_total * dt)
                        frac_e = foi_a / rate_total
                    else:
                        p_leave = 0.0
                        frac_e = 0.0
                    leaving = s_mask & (action == from_a) & (rng.random(N) < p_leave)
                    to_e = leaving & (rng.random(N) < frac_e)
                    moves.append((to_e, leaving & ~to_e, to_a))
                new_e = np.zeros(N, dtype=bool)
                for to_e, _, _ in moves:
                    new_e |= to_e
            else:
                p_by_action = [1 - np.exp(-(foi * m) * dt) for m in mult]
                p_agent = np.choose(action, p_by_action)
                new_e = (state == S) & (rng.random(N) < p_agent)

            new_i = (state == E) & (rng.random(N) < p_e_to_i)
            leaving_i = (state == I) & (rng.random(N) < p_i_to_leave)
            to_h = leaving_i & (rng.random(N) < f_D)
            to_r = leaving_i & ~to_h
            new_d = (state == H) & (rng.random(N) < p_h_to_d)

            state[new_d] = D
            state[to_h] = H
            state[to_r] = R
            state[new_i] = I
            state[new_e] = E
            action[new_i] = NORMAL                       # A38: ill agents act normal
            if decision.mode == "hazard":
                for _, switched, to_a in moves:
                    action[switched] = to_a

            day_new_e += np.count_nonzero(new_e)
            day_new_d += np.count_nonzero(new_d)

        daily_incidence[t] = day_new_e
        daily_deaths[t] = day_new_d
        reported_deaths[t] = detection_rate * day_new_d
        prevalence[t] = np.count_nonzero(state == I)
        exposed[t] = np.count_nonzero(state == E)
        recovered[t] = np.count_nonzero(state == R)
        s_now = state == S
        S_frac[t] = np.count_nonzero(s_now) / N
        S_by_action[t] = np.bincount(action[s_now], minlength=3)
        E_by_action[t] = np.bincount(action[state == E], minlength=3)

        if (prevalence[t] == 0 and exposed[t] == 0
                and np.count_nonzero(state == H) == 0):
            daily_deaths[t + 1:] = 0
            daily_incidence[t + 1:] = 0
            prevalence[t + 1:] = 0
            S_frac[t + 1:] = S_frac[t]
            recovered[t + 1:] = recovered[t]
            S_by_action[t + 1:] = S_by_action[t]
            E_by_action[t + 1:] = E_by_action[t]
            if social_norm_def == "cbf":
                social_norm[t + 1:] = (S_by_action[t, NORMAL] + recovered[t]) / N
            else:
                n_out = S_by_action[t, NORMAL] + S_by_action[t, PRECAUTIONS] + recovered[t]
                social_norm[t + 1:] = (S_by_action[t, NORMAL] + recovered[t]) / n_out
            break

    return dict(
        S=S_frac, prevalence=prevalence, incidence=daily_incidence,
        deaths=daily_deaths, reported_deaths=reported_deaths,
        awareness_signal=awareness_signal, exposed=exposed, recovered=recovered,
        SB=S_by_action[:, PRECAUTIONS], S_by_action=S_by_action, E_by_action=E_by_action,
        social_norm=social_norm, N=N,
        total_infected=N - np.count_nonzero(state == S),
    )

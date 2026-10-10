"""
Arm 3 in the shared world: a frozen LLM-written rule (register A49-A54, C38) as a discrete,
re-deciding decision function.

Each frozen rule `src/arm3_rules/v1/rule_k.py` is loaded only after its SHA-256 matches the
manifest (A54: a rule is never edited), and executed with the same restricted builtins as the
A53 checks (imports limited to `math`).

On each day, every eligible agent (never_ill: S or E, A38/A42) is re-asked with probability
p = redecide_prob (A41). For each re-asked agent a Perception (src/perception.py) is built from
world data only:
  deaths_28day_mean         the world's 28-day mean of reported deaths at the start of the day
  deaths_28day_mean_7d_ago  the same mean as it stood 7 days earlier; 0 before day 7 (A58)
  deaths_cumulative         reported deaths on all days before today
  current_action            the agent's current action
  social_norm               the world's social_norm at the start of the day (A44)
  age_band, vulnerability, occupation_flex, response_efficacy   the frozen population
  population, day           N and the day index
The rule returns probabilities; the action is drawn from the decision stream (A52): one uniform
u per re-asked agent, in agent-index order; stay_home if u < P(stay_home), precautions if
u < P(stay_home) + P(precautions), otherwise normal. Day-0 actions are all normal (the
DecisionFunction default, as CBF's S^B starts empty); rules act from day 0 through re-asking.
"""
import hashlib
import json
import math
import os

import numpy as np

from perception import Perception
from shared_world import DecisionFunction, NORMAL, PRECAUTIONS, STAY_HOME

RULE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "arm3_rules", "v1")
ACTION_STR = {NORMAL: "normal", PRECAUTIONS: "precautions", STAY_HOME: "stay_home"}
_SAFE = ("abs", "min", "max", "sum", "round", "float", "int", "bool", "len", "range",
         "enumerate", "zip", "sorted", "dict", "list", "tuple", "str", "isinstance", "pow",
         "map", "filter", "any", "all", "reversed", "ValueError", "TypeError",
         "ZeroDivisionError", "ArithmeticError", "OverflowError", "Exception")


def _safe_import(name, *args, **kw):
    if name != "math":
        raise ImportError(f"import of {name!r} not allowed")
    return math


def load_rule(k):
    """Return the frozen rule k's decide(p), after checking its hash against the manifest."""
    man = json.load(open(os.path.join(RULE_DIR, "manifest.json"), encoding="utf-8"))
    entry = next(r for r in man["rules"] if r["rule"] == k)
    code = open(os.path.join(RULE_DIR, f"rule_{k}.py"), encoding="utf-8", newline="").read()
    if hashlib.sha256(code.encode("utf-8")).hexdigest() != entry["code_sha256"]:
        raise RuntimeError(f"rule {k}: code does not match its frozen hash")
    import builtins
    ns = {"__builtins__": dict({n: getattr(builtins, n) for n in _SAFE},
                               __import__=_safe_import),
          "__name__": f"arm3_rule_{k}"}
    exec(compile(code, f"rule_{k}.py", "exec"), ns)
    return ns["decide"]


class Arm3Rule(DecisionFunction):
    mode = "discrete"
    redecides = True

    def __init__(self, k, population):
        self.k = k
        self.rule = load_rule(k)
        self.pop = population

    def decide(self, day, agents, view, rng):
        rep = view["reported_deaths"]                      # reported deaths, days 0..day-1
        t7 = day - 7
        d7 = float(rep[max(0, t7 - 28):t7].mean()) if t7 > 0 else 0.0
        common = dict(deaths_28day_mean=float(view["awareness_signal"]),
                      deaths_cumulative=float(rep.sum()),
                      deaths_28day_mean_7d_ago=d7,
                      social_norm=float(view["social_norm"]),
                      population=int(view["N"]), day=int(day))
        pop, act = self.pop, view["action"]
        probs = np.empty((len(agents), 2))
        for j, i in enumerate(agents):
            o = self.rule(Perception(
                current_action=ACTION_STR[int(act[i])], age_band=int(pop.age_band[i]),
                vulnerability=float(pop.vulnerability[i]),
                occupation_flex=float(pop.occupation_flex[i]),
                response_efficacy=float(pop.response_efficacy[i]), **common))
            probs[j] = (o["stay_home"], o["stay_home"] + o["precautions"])
        u = rng.random(len(agents))
        return np.where(u < probs[:, 0], STAY_HOME,
                        np.where(u < probs[:, 1], PRECAUTIONS, NORMAL)).astype(np.int8)

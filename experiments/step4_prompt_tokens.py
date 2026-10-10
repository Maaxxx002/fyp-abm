"""
DRAFT renderer for the arm-2 template (prompts/DRAFT_arm2_arm3.md) and a token ESTIMATE per call.

No LLM is called and no model is chosen, so no model tokenizer is used. Tokens are estimated two
ways from the rendered text: characters / 4 and words x 1.33 (rules of thumb for English with
BPE tokenizers). The exact count must be taken with the chosen model's own token counter.

Perceptions are built from a real run (arm 1, S1, seed 0, foundation) at several days, for one
agent per age band 7 (60-69), so the numbers in the text are realistic.

Usage:  python experiments/step4_prompt_tokens.py
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))
from perception import Perception  # noqa: E402
from population import build_population, AGE_BAND_LABELS  # noqa: E402
from shared_world import CBFArm1, run_shared_world  # noqa: E402

OUT = os.path.join(HERE, "..", "results", "step4")
PROMPT_FILE = os.path.join(HERE, "..", "prompts", "DRAFT_arm2_arm3.md")

AGE_TEXT = ["under 10", "aged 10 to 19", "aged 20 to 24", "aged 25 to 29", "in your 30s",
            "in your 40s", "in your 50s", "in your 60s", "in your 70s", "aged 80 or over"]
ACTION_TEXT = {"stay_home": "staying at home",
               "precautions": "going out but taking precautions",
               "normal": "going out and carrying on as normal"}

TEMPLATE = """You live in a town of {population} people. An infectious disease has been spreading in your town for {day} days.

{deaths_recent} {deaths_earlier} In total, {deaths_cumulative} people in your town have died of it so far.

About {social_norm} of people in your town are going about their lives normally.

You are {age_band}. For someone your age, this disease is fatal in {vulnerability} cases.

How easily you could stay at home if you chose to: {occupation_flex} on a scale from 0 (not at all) to 10 (completely).
How much you believe that taking precautions protects you: {response_efficacy} on a scale from 0 (not at all) to 10 (completely).

Lately you have been {current_action}.

What will you do from today? The options are:
A) Stay at home.
B) Go out, but take precautions.
C) Go out and carry on as normal.

Give the probability, in percent, that you choose each option. Use whole numbers that add up to 100. Reply in exactly this form and nothing else:
A=<number>, B=<number>, C=<number>"""


def half_up(x):
    """A59: round half-up to a whole number, at render time only."""
    return int(math.floor(x + 0.5))


def natural_frequency(v):
    for m in (100, 1_000, 10_000, 100_000):
        if v * m >= 1:
            return f"about {half_up(v * m)} in {m:,}"
    return f"about {half_up(v * 100_000)} in 100,000"


def render(p):
    """Total and pure: every Perception field is used exactly once (A47, A48, A56-A60)."""
    w_now = min(28, p.day)
    n = half_up(w_now * p.deaths_28day_mean)
    recent = (f"In the past four weeks, {n} people in your town died of it." if p.day >= 28
              else f"Since the outbreak began, {n} people in your town have died of it.")
    m = half_up(min(28, max(p.day - 7, 0)) * p.deaths_28day_mean_7d_ago)
    if p.day >= 35:
        earlier = f"In the four weeks up to a week ago, {m} died."
    elif p.day >= 7:
        earlier = f"Between the start of the outbreak and a week ago, {m} died."
    else:
        earlier = f"A week ago, {m} people had died of it."
    return TEMPLATE.format(
        population=f"{p.population:,}", day=p.day,
        deaths_recent=recent, deaths_earlier=earlier,
        deaths_cumulative=half_up(p.deaths_cumulative),
        social_norm=f"{half_up(100 * p.social_norm)}%",
        age_band=AGE_TEXT[p.age_band], vulnerability=natural_frequency(p.vulnerability),
        occupation_flex=half_up(10 * p.occupation_flex),
        response_efficacy=half_up(10 * p.response_efficacy),
        current_action=ACTION_TEXT[p.current_action])


def estimate(text):
    chars, words = len(text), len(text.split())
    return dict(chars=chars, words=words, tok_chars4=chars / 4, tok_words133=words * 1.33)


def main():
    pop = build_population(N=3000, seed=0)
    out = run_shared_world(N=3000, seed=0, decision=CBFArm1(), days=600,
                           f_D=pop.vulnerability, window=28, detection_rate=0.7)
    sig, rep_d = out["awareness_signal"], out["reported_deaths"]
    agent = int(np.flatnonzero(pop.age_band == 7)[0])
    rows = []
    for day in (0, 5, 20, 45, 100, 300):
        p = Perception(
            deaths_28day_mean=float(sig[day]),
            deaths_cumulative=float(rep_d[:day].sum()),
            deaths_28day_mean_7d_ago=float(sig[day - 7]) if day >= 7 else 0.0,  # A58
            current_action="precautions", social_norm=float(out["social_norm"][day]),
            age_band=int(pop.age_band[agent]), vulnerability=float(pop.vulnerability[agent]),
            occupation_flex=float(pop.occupation_flex[agent]),
            response_efficacy=float(pop.response_efficacy[agent]),
            population=3000, day=day)
        text = render(p)
        rows.append(dict(day=day, **estimate(text), text=text))
        print(f"--- day {day}: {rows[-1]['chars']} chars, {rows[-1]['words']} words, "
              f"~{rows[-1]['tok_chars4']:.0f} / ~{rows[-1]['tok_words133']:.0f} tokens")
        if day == 45:
            print(text)
    reply = "A=20, B=60, C=20"
    r_est = estimate(reply)
    # chars/4 and words x 1.33 badly undercount a short string of digits and punctuation;
    # "A=20, B=60, C=20" is ~12 pieces (letters, "=", numbers, commas), so 10-15 tokens is used.
    print(f"--- reply {reply!r}: {r_est['chars']} chars; estimate used: 10-15 tokens")
    json.dump(dict(rows=rows, reply=r_est), open(os.path.join(OUT, "prompt_tokens.json"), "w"),
              indent=2)


if __name__ == "__main__":
    main()

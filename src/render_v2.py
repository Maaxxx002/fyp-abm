"""
DRAFT v2 arm-2 renderer (register A74): the v1 template text unchanged, with the two death
sentences rewritten as one-week totals from the world's 7-day window (A71). Everything else is
rendered exactly as v1 (experiments/step4_prompt_tokens.py, A47, A48, A56-A60); the helpers
below are copies of v1's, and tests/test_render_v2.py asserts they still equal v1's.

Not frozen: prompts/v2/ is a draft until the pilot checks pass (A74).
"""
import math
import os

from perception import PerceptionV2

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
TEMPLATE_FILE = os.path.join(ROOT, "prompts", "v2", "arm2_template_v2.txt")
TEMPLATE = open(TEMPLATE_FILE, encoding="utf-8", newline="").read()

AGE_TEXT = ["under 10", "aged 10 to 19", "aged 20 to 24", "aged 25 to 29", "in your 30s",
            "in your 40s", "in your 50s", "in your 60s", "in your 70s", "aged 80 or over"]
ACTION_TEXT = {"stay_home": "staying at home",
               "precautions": "going out but taking precautions",
               "normal": "going out and carrying on as normal"}

# Each PerceptionV2 field and the one placeholder that shows it (renderer totality, Test 3).
FIELD_PLACEHOLDER = {
    "population": "population", "day": "day",
    "deaths_7day_mean": "deaths_recent", "deaths_7day_mean_7d_ago": "deaths_earlier",
    "deaths_cumulative": "deaths_cumulative", "social_norm": "social_norm",
    "age_band": "age_band", "vulnerability": "vulnerability",
    "occupation_flex": "occupation_flex", "response_efficacy": "response_efficacy",
    "current_action": "current_action",
}


def half_up(x):
    """A59: round half-up to a whole number, at render time only."""
    return int(math.floor(x + 0.5))


def natural_frequency(v):
    for m in (100, 1_000, 10_000, 100_000):
        if v * m >= 1:
            return f"about {half_up(v * m)} in {m:,}"
    return f"about {half_up(v * 100_000)} in 100,000"


def death_sentences(day, deaths_7day_mean, deaths_7day_mean_7d_ago):
    """The two v2 death sentences (A74)."""
    n = half_up(min(7, day) * deaths_7day_mean)
    recent = (f"In the past week, {n} people in your town died of it." if day >= 7
              else f"Since the outbreak began, {n} people in your town have died of it.")
    m = half_up(min(7, max(day - 7, 0)) * deaths_7day_mean_7d_ago)
    if day >= 14:
        earlier = f"In the week before that, {m} died."
    elif day >= 7:
        earlier = f"Between the start of the outbreak and a week ago, {m} died."
    else:
        earlier = f"A week ago, {m} people had died of it."
    return recent, earlier


def render(p: PerceptionV2) -> str:
    """Total and pure: every PerceptionV2 field is used exactly once."""
    recent, earlier = death_sentences(p.day, p.deaths_7day_mean, p.deaths_7day_mean_7d_ago)
    return TEMPLATE.format(
        population=f"{p.population:,}", day=p.day,
        deaths_recent=recent, deaths_earlier=earlier,
        deaths_cumulative=half_up(p.deaths_cumulative),
        social_norm=f"{half_up(100 * p.social_norm)}%",
        age_band=AGE_TEXT[p.age_band], vulnerability=natural_frequency(p.vulnerability),
        occupation_flex=half_up(10 * p.occupation_flex),
        response_efficacy=half_up(10 * p.response_efficacy),
        current_action=ACTION_TEXT[p.current_action])


def perception_from_world(day, awareness_signal, reported_deaths, social_norm, N, agent_static,
                          current_action):
    """PerceptionV2 from a 7-day-window run_shared_world: awareness_signal[t] is the 7-day mean
    for day t, reported_deaths the daily series. agent_static = (age_band, vulnerability,
    occupation_flex, response_efficacy)."""
    age_band, vul, occ, eff = agent_static
    return PerceptionV2(
        deaths_7day_mean=float(awareness_signal[day]),
        deaths_cumulative=float(reported_deaths[:day].sum()),
        deaths_7day_mean_7d_ago=float(awareness_signal[day - 7]) if day >= 7 else 0.0,
        current_action=current_action, social_norm=float(social_norm[day]),
        age_band=int(age_band), vulnerability=float(vul), occupation_flex=float(occ),
        response_efficacy=float(eff), population=int(N), day=int(day))

import math

def decide(p):
    # Derived quantities mirroring what the description shows
    deaths_recent_total = round(p.deaths_28day_mean * min(28, p.day))
    deaths_earlier_total = round(p.deaths_28day_mean_7d_ago * min(28, max(p.day - 7, 0)))
    recent_rate = p.deaths_28day_mean
    earlier_rate = p.deaths_28day_mean_7d_ago

    # Perceived danger: how much deaths are rising, scaled by age-specific fatality
    rising = max(0.0, recent_rate - earlier_rate)
    trend = math.tanh(rising / max(1.0, earlier_rate + 1.0))
    level = math.tanh(recent_rate / max(1.0, p.population / 1000.0))
    fear = min(1.0, 0.5 * level + 0.3 * trend + 0.2 * min(1.0, p.vulnerability * 20))

    # Action propensities (log-space scores)
    # Stay home: driven by fear, eased by ability to stay home and belief in precautions
    s_home = 3.0 * fear + 0.4 * p.occupation_flex * 2 + 0.6 * p.response_efficacy * 2 - 1.0 * p.social_norm * 2
    # Precautions: moderate fear, benefits most from belief in efficacy
    s_prec = 1.5 * fear + 1.0 * p.response_efficacy * 2 + 0.2 * p.occupation_flex * 2 - 0.5 * p.social_norm * 2
    # Normal: pulled by social norm, dampened by fear
    s_norm = 2.5 * p.social_norm * 2 - 2.5 * fear - 0.5 * p.response_efficacy * 2

    # Inertia toward the action taken most recently
    inertia = 0.5
    if p.current_action == "stay_home":
        s_home += inertia
    elif p.current_action == "precautions":
        s_prec += inertia
    else:
        s_norm += inertia

    # Softmax
    m = max(s_home, s_prec, s_norm)
    e_home = math.exp(s_home - m)
    e_prec = math.exp(s_prec - m)
    e_norm = math.exp(s_norm - m)
    total = e_home + e_prec + e_norm

    return {
        "stay_home": e_home / total,
        "precautions": e_prec / total,
        "normal": e_norm / total,
    }

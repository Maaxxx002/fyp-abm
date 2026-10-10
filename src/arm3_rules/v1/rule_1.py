import math

def decide(p):
    # Perceived risk: rises with recent deaths, their trend, and cumulative toll,
    # scaled by age-specific fatality.
    recent_total = p.deaths_28day_mean * min(28, p.day)
    earlier_total = p.deaths_28day_mean_7d_ago * min(28, max(p.day - 7, 0))
    trend = max(recent_total - earlier_total, 0.0)

    pop = max(p.population, 1)
    recent_rate = recent_total / pop
    cum_rate = p.deaths_cumulative / pop
    trend_rate = trend / pop

    # Vulnerability-weighted risk signal (bounded).
    risk_raw = (
        40.0 * math.sqrt(recent_rate)
        + 25.0 * math.sqrt(cum_rate)
        + 30.0 * math.sqrt(trend_rate)
    ) * (0.3 + p.vulnerability)
    risk = 1.0 - math.exp(-risk_raw)  # in [0, 1)

    # Fear of infection pushes toward caution; concern grows with age band.
    age_factor = p.age_band / 9.0
    fear = risk * (0.6 + 0.4 * age_factor)

    # Ability to stay home and belief in precautions both make caution easier.
    flex = p.occupation_flex
    eff = p.response_efficacy

    # Social conformity: people follow what others are doing.
    conform = p.social_norm

    # Utilities for each option (higher = more attractive).
    u_home = 2.2 * fear + 1.0 * flex * (0.5 + fear) + 0.4 * (p.current_action == "stay_home") \
        - 0.6 * (1.0 - conform) * 0.0
    u_prec = 1.6 * fear * eff + 0.9 * (1.0 - flex) * 0.5 + 0.6 * eff \
        + 0.35 * (p.current_action == "precautions") \
        + 0.3 * conform * 0.2
    u_norm = 1.4 * (1.0 - fear) + 0.9 * conform + 0.6 * (1.0 - eff) * 0.5 \
        + 0.5 * (p.current_action == "normal") + 0.15 * (1.0 - flex)

    # Softmax over utilities, with a fixed temperature.
    temp = 1.0
    m = max(u_home, u_prec, u_norm)
    e_home = math.exp((u_home - m) / temp)
    e_prec = math.exp((u_prec - m) / temp)
    e_norm = math.exp((u_norm - m) / temp)
    s = e_home + e_prec + e_norm

    return {
        "stay_home": e_home / s,
        "precautions": e_prec / s,
        "normal": e_norm / s,
    }

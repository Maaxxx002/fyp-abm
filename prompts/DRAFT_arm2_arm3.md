# DRAFT v1 — arm-2 prompt template and arm-3 instruction (NOT FROZEN)

Status: draft, updated to register A55–A62. Not piloted; the pilot (E6, criteria approved in
A62) runs before the prompt is frozen. No LLM has been called. The draft renderer used for
token counts is `experiments/step4_prompt_tokens.py`.

Perception fields (11; `src/perception.py`): deaths_28day_mean, deaths_cumulative,
deaths_28day_mean_7d_ago, current_action, social_norm, age_band, vulnerability,
occupation_flex, response_efficacy, population, day. Each placeholder renders exactly one
field, and every field has exactly one placeholder (Test 3 totality).

---

## 1. Arm-2 prompt template

```
You live in a town of {population} people. An infectious disease has been spreading in your town for {day} days.

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
A=<number>, B=<number>, C=<number>
```

Actions are described in everyday words only; no effect sizes are stated (A57).

### Rendering rules (one per field)

`half_up(x)` = floor(x + 0.5), applied at render time only (A59).

| Placeholder | Field | Rendering |
|---|---|---|
| `{population}` | population | thousands separator: "3,000" |
| `{day}` | day | integer (A60) |
| `{deaths_recent}` | deaths_28day_mean | n = half_up(min(28, day) × value). day ≥ 28: "In the past four weeks, {n} people in your town died of it." day < 28: "Since the outbreak began, {n} people in your town have died of it." (A58, A59) |
| `{deaths_earlier}` | deaths_28day_mean_7d_ago | value = 0 before day 7 (A58). m = half_up(min(28, day − 7) × value). day ≥ 35: "In the four weeks up to a week ago, {m} died." 7 ≤ day < 35: "Between the start of the outbreak and a week ago, {m} died." day < 7: "A week ago, {m} people had died of it." |
| `{deaths_cumulative}` | deaths_cumulative | half_up(value) (A59) |
| `{social_norm}` | social_norm | half_up(100 × value) + "%" (A48) |
| `{age_band}` | age_band | "under 10", "aged 10 to 19", "aged 20 to 24", "aged 25 to 29", "in your 30s", "in your 40s", "in your 50s", "in your 60s", "in your 70s", "aged 80 or over" |
| `{vulnerability}` | vulnerability | "about k in M": M = smallest of 100, 1,000, 10,000, 100,000 with value × M ≥ 1; k = half_up(value × M) |
| `{occupation_flex}` | occupation_flex | half_up(10 × value) |
| `{response_efficacy}` | response_efficacy | half_up(10 × value) |
| `{current_action}` | current_action | stay_home → "staying at home"; precautions → "going out but taking precautions"; normal → "going out and carrying on as normal" |

`vulnerability` by age band: 0–9 about 2 in 100,000 · 10–19 about 7 in 100,000 · 20–24 and
25–29 about 3 in 10,000 · 30–39 about 8 in 10,000 · 40–49 about 2 in 1,000 · 50–59 about 6 in
1,000 · 60–69 about 2 in 100 · 70–79 about 4 in 100 · 80+ about 8 in 100.

### Reply handling (A56, A61)

- Parse `A=<a>, B=<b>, C=<c>` (whole numbers ≥ 0). Valid if the three parse and sum to 100;
  the probabilities are a/100, b/100, c/100 (A → stay_home, B → precautions, C → normal).
- The simulator samples the action from the decision random stream (A52/A56).
- Invalid reply: retry up to 2 times (same prompt); if still invalid, the agent keeps its
  `current_action`. Every invalid reply and fallback is logged; the invalid-reply rate is
  reported (A61).

### Example (rendered from a real run: arm 1, S1, seed 0, day 45, an agent aged 60–69)

```
You live in a town of 3,000 people. An infectious disease has been spreading in your town for 45 days.

In the past four weeks, 6 people in your town died of it. In the four weeks up to a week ago, 6 died. In total, 7 people in your town have died of it so far.

About 74% of people in your town are going about their lives normally.

You are in your 60s. For someone your age, this disease is fatal in about 2 in 100 cases.

How easily you could stay at home if you chose to: 10 on a scale from 0 (not at all) to 10 (completely).
How much you believe that taking precautions protects you: 7 on a scale from 0 (not at all) to 10 (completely).

Lately you have been going out but taking precautions.

What will you do from today? The options are:
A) Stay at home.
B) Go out, but take precautions.
C) Go out and carry on as normal.

Give the probability, in percent, that you choose each option. Use whole numbers that add up to 100. Reply in exactly this form and nothing else:
A=<number>, B=<number>, C=<number>
```

---

## 2. Arm-3 instruction (A49: the same description as arm 2, as a template, plus a coding
instruction; no simulation data or results; the disease is not named; deaths as counts)

```
Below is a description that is shown to people living in a town where an infectious disease
is spreading. Each person reads it with the parts in curly brackets filled in for their own
situation, and replies with the probability that they choose each option.

--- DESCRIPTION (template) ---
[the arm-2 template from section 1, verbatim, placeholders unfilled]
--- END ---

Write a Python function that, for any one person, gives the probability that they choose each
option.

def decide(p):
    ...
    return {"stay_home": ..., "precautions": ..., "normal": ...}

"stay_home" is option A, "precautions" is option B, "normal" is option C.

`p` has these attributes (raw values, before they are written into the description):
- p.population (int): number of people in the town; {population}.
- p.day (int, >= 0): days the disease has been spreading; {day}.
- p.deaths_28day_mean (float, >= 0): deaths per day, averaged over the past 28 days (over the
  days so far, if fewer than 28). {deaths_recent} shows this as a whole-number total: the
  average times min(28, day), rounded.
- p.deaths_28day_mean_7d_ago (float, >= 0): the same average as it was 7 days ago (0 before
  day 7). {deaths_earlier} shows this as a whole-number total: the average times
  min(28, day - 7), rounded.
- p.deaths_cumulative (float, >= 0): total deaths so far; {deaths_cumulative}, rounded.
- p.social_norm (float, 0 to 1): {social_norm} is 100 * p.social_norm, rounded, then "%".
- p.age_band (int, 0 to 9): 0 = under 10, 1 = 10-19, 2 = 20-24, 3 = 25-29, 4 = 30s, 5 = 40s,
  6 = 50s, 7 = 60s, 8 = 70s, 9 = 80 or over; {age_band}.
- p.vulnerability (float, 0 to 1): the chance the disease is fatal for someone this age;
  {vulnerability} writes it as "about k in M".
- p.occupation_flex (float, 0 to 1): {occupation_flex} is 10 * p.occupation_flex, rounded.
- p.response_efficacy (float, 0 to 1): {response_efficacy} is 10 * p.response_efficacy, rounded.
- p.current_action (str): "stay_home", "precautions" or "normal"; {current_action}.

Rules for the function:
- The three probabilities must be non-negative and sum to 1, for every valid input.
- Use only the attributes of `p` listed above. You may import `math`; no other imports.
- No randomness, no reading or writing files, no network, no printing.
- The same input must always give the same output.

Return only the code.
```

---

## 3. Remaining notes (not decisions)

1. Before day 28 the recent-deaths total equals the cumulative total (both count every death
   so far), so the two sentences repeat the same number. Totality is still satisfied.
2. At day 0 the day line reads "for 0 days" and every death sentence shows 0.
3. Rounding hides small totals: a 4-week total of reported deaths below 0.5 shows as 0.

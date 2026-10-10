# Decision register — FYP CCDS26-0406

Running record from the start of the sourcing phase. Kept so the eventual progress report can be
assembled without reconstruction. **This is the register, not the report.**

Every entry is either **[Settled]**, **[Measured]** (an empirical result with the number),
or **[Open]**. Where a decision reversed an earlier one, both are shown.

Last updated: after the shape-metric investigation and the N decision.

---

## A. Settled decisions

| # | Decision | Basis |
|---|---|---|
| A1 | Disease model: Weitz model B (SEIR + H compartment) | Minimal variant producing plateau, shoulder and oscillation |
| A2 | Disease parameters: Weitz Table 1 (R₀=3, 2 d latent, 6 d infectious, f_D=0.01) | Weitz supplies the referent, so his parameterisation governs |
| A3 | Arm 1 rule: Gozzi's **CBF**, not EFB | Agent-native; best performer in Gozzi's evaluation; sources `r`; avoids circularity |
| A4 | Weitz's rule is **simulator validation, not an arm** | Prevents "arm 1 reproduces Weitz" being tautological |
| A5 | One location, well-mixed | Both source papers are single well-mixed populations |
| A6 | Three-level action: stay home / precautions / normal | Maps onto Weitz's continuous β reduction; sourced by CBF's `r` and PMT response cost |
| A7 | **N = 3,000** | Revised up from 1,000 — see D3. Reaffirmed after C13's small-N/small-count viability concern was resolved (not the operative mechanism) — see D13/C20. **Reaffirmed again (A30)** after N=1,000 failed the pre-set C26/C27 decision rule |
| A8 | Perception signal: **28-day rolling mean** of reported deaths | C7 — a 7-day window leaves the response ungraded at N ≤ 3,000. Smoothing itself is sourced to Weitz Methods; the 28-day length is a stated finite-population correction, not a behavioural claim |
| A9 | Deaths, not cases, as the awareness driver | Urmi et al. lag-0 correlation; Weitz mechanism is fatality-driven |
| A10 | Population: New York age structure, quota-drawn, frozen | Mean IFR 0.9718% vs Weitz's 1.000%; see B2 |
| A11 | Vulnerability derived from age via `IFR_10age` | Zero free parameters |
| A12 | `days_since_last_outing` **deleted** | No source; replaced by CBF's relaxation mechanism |
| A13 | `response_efficacy` **added** — **implemented**, wired into CBF's `r` (`r_i = 1 - response_efficacy_i`). **The wiring into `r` is superseded by A29**; the field itself is retained | PMT β=+0.251, second-strongest determinant; wiring and its unsourced-mapping caveat recorded in C21 |
| A14 | `self_efficacy` deliberately excluded | Strongest determinant (β=+0.270) but no meaningful barrier in a single-venue three-level act |
| A15 | Disease is **not named** in the arm-2 prompt | Arm 1 has no disease identity; naming it creates an input asymmetry, not a function difference |
| A16 | Scenarios vary only R₀ and T_H | δ_c, k, r, β_B live inside arm 1's rule; varying them varies the object under test |
| A17 | S1 baseline (R₀=3, T_H=14); S2 milder (R₀=2); S3 delayed (T_H=28) | S2 stresses signal magnitude, S3 stresses timing |
| A18 | Arm 4 distils on **S1 only**, evaluated on S2/S3 held out | Turns arm 4 from a fit check into a generalisation test |
| A19 | **[SUPERSEDED by A33]** Shape metric: **Weitz symmetry coefficient computed on incidence** | See D2. Failed C29's known-case validation (P2) in both implementations |
| A20 | Integration: **48 sub-steps per day** (revised from 12 — see C9) | Gozzi's own default (`daily_steps=12` — verified in their source: `compartment_model_age_deaths.py`, `function_model_age_deaths.py`, `mobility_model_age.py`, all `dt=1/12`) is insufficient for this model's precision; see C9 |
| A21 | Initial infected: **10 agents** (0.33% at N=3,000) | D8 — a 1% seed removes the exponential growth phase entirely |
| A22 | Repo `fyp-abm` is the build artefact; `docs/` holds the four specs and is authoritative | Claude Code sessions read `CLAUDE.md` + `docs/` |
| A23 | "Stay home" is **two-sided**: an agent who stays home neither catches nor spreads that day, so the population multiplier is (1−q)² | Formalises the assumption already baked into `q = 1 − (1+(δ/δ_c)^k)^(−1/2)` (CLAUDE.md Test 2 / Sourcing_Pack_v3.md's "Test 3" open point) — recorded as decided, not just assumed. **Scope note (A39):** in the shared world (A37) its "does not spread" half never acts, because ill agents do not decide (A38); A23 still governs Weitz-rule validation (Test 2) |
| A24 | Awareness signal **stays the 28-day rolling mean** (A8 reaffirmed). Gozzi's literal one-day (yesterday's deaths) signal is **rejected** | [Decision, planning chat (Max), C23] With the real CBF mechanism at N=3,000 the one-day signal fails mean-field agreement: 17.07% relative error, −9.13 SEM (90 seeds). Supersedes C16's `direct-g`-based evidence for the same question |
| A25 | Death reporting: **detection_rate = 0.7 applied as a plain multiplier on realised deaths, NO integer truncation** | [Decision, planning chat (Max), C23] Deliberate deviation from Gozzi's code (`compartment_model_age_deaths.py:152`, `.astype(int)` per age group per day). At N=3,000 the truncation leaves agents seeing 6.7% of realised deaths instead of 70%, peak S^B falls from ~567 to 89, and behaviour fails pass mark (a). Treated as a city-scale bookkeeping artefact, not mechanism. Sourcing Pack v3 (observation-model section) records the formula as detection_rate x Binomial(...) without truncation; this has not been checked against the paper's text. Detection affects only what agents perceive, never recorded deaths. No Δ delay added (H/T_H already supplies it) |
| A26 | Mortality: **per-agent f_D = IFR_10age[age_band]** (population mean 0.009718), replacing A2's flat 0.01 for the model runs | [Decision, planning chat (Max), C23] Gozzi's age-based IFR adopted; the DDE reference uses the population-weighted mean, exact in expectation while r is shared (C23) |
| A27 | **[SUPERSEDED by A31]** **Pass mark (b) rule, fixed for all future steps:** FAIL only if relative error > 6% AND gap > 2 SEM. Relative error > 6% with gap ≤ 2 SEM is **INCONCLUSIVE** → re-run that config at 90 seeds and apply the same rule. Applies identically to every config | [Decision, planning chat (Max), C23] At N=3,000 / 30 seeds, 1 SEM of final S is ~6.8% of the reference, wider than the 6% band itself (C23: config 2 read 13.12% / +1.93 SEM at 30 seeds, 1.52% / +0.47 SEM at 90) |
| A28 | **Pass mark (a), unchanged:** lower peak I and higher final S than the config's own no-behaviour control, each by > 2 SEM of the paired (same-seed) difference | [Decision, planning chat (Max), C23] |
| A29 | **Arm-level physics uses flat r = 0.5 for all agents** (Gozzi). `response_efficacy` is **retained as a Perception field** available to all arms as a decision input; arm 1 (CBF) ignores it, as Gozzi's original does. Applies to arms 2–4 too: Act must be identical across arms | [Decision, planning chat (Max), C24] The PMT construct is sourced as a determinant of protective-behaviour ADOPTION (Think), not of protective EFFECTIVENESS (Act); the C21 mapping `r_i = 1 − response_efficacy_i` is unsourced and conflated the two. C24 measured that mapping's effect as +0.0101 final S (+9.47 SEM, n=90) at N=3,000 — recorded as the measured cost of the removed modification. Supersedes A13's wiring and C21's mapping |
| A30 | **N stays 3,000** (A7 reaffirmed); N=1,000 rejected | [Decision, planning chat (Max), C26/C27] N=1,000 fails the pre-set C26/C27 decision rule on pass mark (a): at γ_beh=0.5 and in S3 the peak-I reduction is not detectable at 30 seeds (−1.92 and −1.75 SEM). Detecting the effect at N=1,000 would need ~3× the seeds, which removes the arm-2 cost saving (N=1,000 × 90 seeds ≈ N=3,000 × 30 seeds in agent-days). This also closes the gap that N was originally chosen under the old 7-day window (C5/C7/D3): it is now re-checked with the real CBF mechanism and the 28-day window. Limitation: the 7-day window itself was not re-tested under CBF (section F) |
| A31 | **Pass mark (b) rule, REVISED (supersedes A27):** the 30-seed run is a SCREEN only. A config at ≤ 6% relative error at 30 seeds PASSES. Any config > 6% at 30 seeds (whether A27 would have called it FAIL or INCONCLUSIVE) is re-run at 90 seeds, and the 90-seed result is the verdict: FAIL if relative error > 6% AND gap > 2 SEM at 90 seeds, otherwise PASS | [Decision, planning chat (Max), C26/C27] **This rule was revised AFTER observing the pattern below, not fixed in advance.** Under A27 both C26/C27 FAILs were borderline (~2.1 SEM) and vanished at 90 seeds. All five N=3,000 points re-run at 90 seeds moved toward the DDE: seeds 0–29 run high, and the configs share seeds, so their 30-seed errors are correlated, not independent. With 20+ configs per step, false FAILs at a 2-SEM line are expected. Re-scored in C28 |
| A32 | **Run length stays 600 days for production** runs, pending C28's day-600 check. **900 days remains the convention for mean-field (DDE) reference comparisons** | [Decision, planning chat (Max)] C23–C27 ran at 900 days for comparability with C18 |
| A33 | **Frozen shape-metric list**, fixed from C29's known-case validation BEFORE any arm was scored. **PRIMARY:** M3, duration T10–90 (per-run, and on the aligned averaged curve with bootstrap CI). **SECONDARY:** M1, EpidemicKabu wave count (kernel 18); it over-counts on long, low curves (8.6 vs 4 waves, K2 vs K1). **SAFETY NET:** peak-I reduction and final-S increase vs own control | [Decision, planning chat (Max), C29] M3 and M1 are the only candidates that passed P1–P4 on the known cases; M2, M4 and both symmetry versions failed |
| A34 | **Reporting scale: STRETCH FACTOR** = arm duration ÷ own-control duration (same scenario, same seeds). ×1 = no flattening. Weitz's plateau (K1/K2) is a reference marker of **≥ ×20** (a lower bound, truncated at 600 days), NOT the top of the scale. Always reported alongside peak reduction: longer + lower = flattening; longer + same peak = likely separate waves. **No pass/fail threshold** | [Decision, planning chat (Max), C29] K1 ODE T10–90 23 → 461 d; K2 averaged 23 → 477 d, both truncated at day 600 |
| A35 | **Truncation rule:** M3 is valid for a config only if every run has E+I = 0 by day 600. Otherwise the config is flagged **TRUNCATED** and its M3 is not reported as a duration | [Decision, planning chat (Max), C29] C29's behaviour cases were all still active at day 600, so M3 there partly measures the window |
| A36 | **Stretch-factor reporting rule:** the stretch factor (A34) is always reported with its **median per-seed ratio** and the **share of runs with stretch > ×1.5**, alongside the mean | [Decision, planning chat (Max), C30] C30's S2 mean (×1.24) was driven by 4/30 runs (one at 311 d vs a control maximum of 52 d); its median per-seed ratio was ×0.964 |
| A37 | **One shared world for all arms (B1, option 2).** Three actions — stay home / precautions / normal — with the same physics for every arm. Arm 1 = CBF unchanged: S^B = "precautions", S = "normal"; arm 1 never chooses "stay home" | [Decision, planning chat (Max), 7 Oct 2026] In CBF's own two-state world the lowest transmission multiplier is r = 0.5, so at R₀ = 3 no decision rule can hold effective R near 1 while most people are susceptible (3 × 0.5 = 1.5): the Weitz signature would be unreachable in S1/S3 for every arm. Implemented as `src/shared_world.py` `run_shared_world` (C31) |
| A38 | **Who decides (variant "B"):** agents with own_health = `currently_ill` do NOT decide in ANY arm; they act "normal", as in Gozzi (infected agents have no behavioural state). H and D agents do not decide (Design_Spec §2a, unchanged). The only remaining difference between arm 1 and arms 2–4 in what is available: stay home exists and arm 1 never uses it. **Planned measured extension (not now):** arm 3 run with and without ill agents deciding | [Decision, planning chat (Max), 7 Oct 2026] Whether **recovered** agents decide is NOT decided here (reported, E20) |
| A39 | **Action physics (B2).** "Precautions" = CBF's S^B effect: one-sided (reduces the agent's own infection risk only), flat r = 0.5, consistent with A29. "Stay home" = the agent cannot be infected while staying home. Susceptible hazard per sub-step = β·(I/N)·m, m = 1 / 0.5 / 0 for normal / precautions / stay home. **Relationship to A23 (not overwritten):** A23 defines stay home as two-sided (neither catches nor spreads). Because ill agents do not decide (A38), no infectious agent ever stays home in the shared world, so A23's "does not spread" half never acts there; in practice stay home is one-sided for every agent who can choose it. A23 continues to govern Weitz-rule simulator validation (`run_weitz_behaviour`, Test 2), where every agent draws stay-home. If the A38 extension lets ill agents decide, whether their stay-home blocks transmission (A23) must be decided then | [Decision, planning chat (Max), 7 Oct 2026] r = 0.5: Gozzi demo value (C13), flat per A29 |
| A40 | **New Perception field `current_action`** (the agent's current action: stay_home / precautions / normal), offered to all arms. Arm 1 ignores it (CBF keeps its S/S^B state internally) | [Decision, planning chat (Max), 7 Oct 2026] Without it a re-asked LLM has no memory of its current choice. Added to `src/perception.py` (shape only; no renderer yet) |
| A41 | **Re-decision cadence (B3): p = 0.3/day kept PROVISIONALLY for arms 2–4, still UNSOURCED** (Sourcing_Pack_v3 Part 4 lists it as unsourced). Arm 1 keeps CBF's continuous per-sub-step rates. The cadence sweep (E2) will use **arm 3** once built, not a stand-in rule | [Decision, planning chat (Max), 7 Oct 2026] Stand-in rules misled this project three times (δ(t) definition, CBF lag, direct-g vs real S/S^B; CLAUDE.md) |
| A42 | **Recovered agents do not decide; they act "normal"** (E20 resolved, option (i)). Together with A38, only agents whose own_health is `never_ill` (true S or E) ever decide | [Decision, planning chat (Max), 10 Oct 2026] Matches CBF, whose relaxation term μ_B·(S+R)/N counts R as normal. A recovered agent's action has no physical effect (immune, not infectious) and would cost arm-2 calls |
| A43 | **`own_health` is dropped from the main-design Perception vector, but kept in the code.** Consequence of A38 + A42: every deciding agent is `never_ill`, so the field is constant and carries no information. Kept: the observation model (`shared_world.own_health_of`, used by the world for eligibility) and the `OwnHealth` type in `src/perception.py`, because the field is needed again if ill agents are later allowed to decide (E21). The main-design vector now has 12 fields: 10 decision fields (own_health out, current_action in) + population, day. What this changes in docs/ is listed in C31's report; the specs are NOT yet edited | [Decision, planning chat (Max), 10 Oct 2026] Ablation = removing a field from the dataclass (CLAUDE.md constraint 3), so the field is removed from the dataclass rather than hidden from one arm |
| A44 | **`social_norm` = CBF's exact relaxation term (S_normal + R) / N.** Denominator N (the dead stay in it); susceptibles acting normal count; staying home does NOT count as normal; recovered count as normal. Arm 1's relaxation rate is μ_B × this same quantity, so arm 1's one social input and the field arms 2–4 see are identical. Implemented in `run_shared_world` (start-of-day value, `social_norm` series) | [Decision, planning chat (Max), 10 Oct 2026] **Flagged, not resolved:** (1) the value is a share of people NOT taking precautions, the opposite of the current wording "fraction taking precautions" (Design_Spec §2, Sourcing_Pack 3e, the §4 sketch "About 34% of people are currently taking precautions"); (2) 1 − value is not "the share taking precautions" either: it also contains E, I, H, D and stay-home agents; (3) it leaves out E and I agents, who mostly act normal (I always, A38), so "X% are going about normally" undercounts by E+I_normal, largest near the peak; (4) it depends on the S/E split, a latent-compartment quantity no real person could observe (allowed by P4's wording, since CBF publishes it, but in tension with the spirit of constraint 5); (5) an accurate one-line LLM wording does not exist yet — the renderer must choose one deliberately (E6) |
| A45 | **A38 stays the MAIN design** (ill agents do not decide in any arm). **Considered and NOT adopted:** a fixed ill-isolation rule as part of the WORLD (identical in all arms and in the control). Reason: no sourced isolation probability was found; it would change the no-behaviour baseline; and it departs from Gozzi, whose behaviour applies to healthy agents only. The variant where ill agents may decide is a planned measured extension (E21); the limitation is recorded in section F | [Decision, planning discussion (Max), 10 Oct 2026] |
| A46 | **`local_deaths_7d` dropped from the Perception vector.** The model is well-mixed (A5): agents have no contacts, so "deaths among this agent's contacts" has no meaning. **Cost recorded:** this removes the free global-vs-local A/B inside arm 1 (Design_Spec §3; Gozzi's CBF has both mechanisms) | [Decision, planning chat (Max), Oct 2026] C15 had already omitted it for the same reason |
| A47 | **E13 resolved: `deaths_prev_period` is replaced by `deaths_28day_mean_7d_ago`** — the same 28-day mean of reported deaths as it stood 7 days earlier. Purpose: show the LLM the direction of change with low noise and a one-week lag. **The 7-day horizon is UNSOURCED**; motivation: S1's T10–90 is about 23 days (C30: control 23.10 d), so a 28-day lag (reaching back 56 days) is too blunt. **No normal-times death-rate baseline is added** | [Decision, planning chat (Max), Oct 2026] |
| A48 | **E22 resolved: `social_norm` keeps CBF's exact value (A44).** LLM-facing wording: **"About X% of people in your town are going about their lives normally."** **Recorded limitation:** this undercounts — agents who are infected (E, I) and act normally are excluded from CBF's term (S_normal + R)/N, and so are hospitalised and dead agents, who remain in the denominator | [Decision, planning chat (Max), Oct 2026] Option (1) of E22 |
| A49 | **Arm 3 input:** arm 3 gets the SAME description as arm 2 — the arm-2 prompt template with a placeholder for each Perception field — plus an instruction to write a Python function. No simulation data or results are shown. The disease is not named (A15). Deaths are given as counts | [Decision, planning chat (Max), Oct 2026] Keeps "arms differ only in the decision function": arm 3 sees what arm 2 sees, as a template rather than filled in |
| A50 | **Arm 3 uses the same LLM model as arm 2.** The model is not chosen yet | [Decision, planning chat (Max), Oct 2026] |
| A51 | **Arm 3 = K = 5 independently generated rules, all five together.** Report the mean and spread over the five. No rule is selected or discarded on simulation results. A rule is regenerated only if it fails a mechanical check (A53), and every regeneration is logged | [Decision, planning chat (Max), Oct 2026] K = 5 is a design choice, not sourced |
| A52 | **Each arm-3 rule returns probabilities for the three actions;** the simulator draws the action from the decision random stream (`run_shared_world`'s separate stream, seeded (seed, 1)) | [Decision, planning chat (Max), Oct 2026] |
| A53 | **Mechanical checks before an arm-3 rule is used:** (1) runs without error; (2) returns valid probabilities (non-negative, summing to 1) on a grid of extreme and typical inputs; (3) reads only Perception fields — no imports beyond `math`, no I/O, no internal randomness; (4) deterministic for a given input | [Decision, planning chat (Max), Oct 2026] |
| A54 | **Freeze each arm-3 rule before any simulation run:** code, exact prompt, model name and version, date. A rule is never edited afterwards | [Decision, planning chat (Max), Oct 2026] |
| A55 | **E19 adopted: arm 2 stops LLM calls once E + I = 0** for the rest of the run (no further infection is possible, so later decisions cannot change any outcome) | [Decision, planning chat (Max), Oct 2026] Call counts with and without it: C32 |
| A56 | **Arm 2 also returns probabilities** for A/B/C (stay home / precautions / normal); the simulator samples the action from the decision random stream, as for arm 3 (A52). Template answer format: three whole-number percentages, "A=<n>, B=<n>, C=<n>" | [Decision, planning chat (Max), Oct 2026] Makes arms 2 and 3 the same kind of policy |
| A57 | **The prompt does not state action effects** (×0.5, ×0). Actions are described in everyday words only | [Decision, planning chat (Max), Oct 2026] CBF's adoption rate does not depend on r, so arm 1's choice does not use the effect size either; `response_efficacy` stays a belief, not a stated fact |
| A58 | **Early-day rendering:** before day 28 the recent-deaths sentence says "since the outbreak began" instead of "in the past four weeks" (the 28-day mean covers only the days so far, A8/C17); `deaths_28day_mean_7d_ago` = 0 before day 7 | [Decision, planning chat (Max), Oct 2026] |
| A59 | **Deaths are rendered as whole-number 4-week TOTALS, not per-day averages:** "In the past four weeks, {n} people in your town died of it. In the four weeks up to a week ago, {m} died." n = window length × `deaths_28day_mean`, m = window length × `deaths_28day_mean_7d_ago`; cumulative deaths are rounded to a whole number. **Rounding (recorded):** reported deaths are 0.7 × realised (A25), so all three totals are generally fractional; each is rounded half-up to a whole number (floor(x + 0.5)) at render time only. The Perception values themselves are not rounded | [Decision, planning chat (Max), Oct 2026] Window length = min(28, day) for n and min(28, day − 7) for m, matching the world's shrinking window exactly |
| A60 | **The day line is kept** ("…has been spreading in your town for {day} days") | [Decision, planning chat (Max), Oct 2026] `day` is in the vector, so totality requires it |
| A61 | **Invalid arm-2 reply:** retry up to 2 times; if still invalid, the agent keeps its `current_action`. Every invalid reply and every fallback is logged, and the invalid-reply rate is reported | [Decision, planning chat (Max), Oct 2026] |
| A62 | **Pilot criteria (i)–(iv) in E6 APPROVED** | [Decision, planning chat (Max), Oct 2026] |
| A63 | **LLM for arms 2 and 3 (A50): Claude Haiku 5.5, API model string `claude-haiku-5-5`.** Verified 10 Oct 2026 in Anthropic's official docs (platform.claude.com, "Models overview": Claude API ID and alias both `claude-haiku-5-5`, a pinned snapshot; retirement not sooner than 7 Oct 2027). **Price, standard API, 10 Oct 2026: $0.10 / M input tokens, $0.50 / M output tokens** (official "Pricing" page; this tier applies to prompts up to 100,000 tokens — over 100,000 it is $0.50 / $2.50; Batch API is 50% off). Not called yet | [Decision, planning chat (Max), 10 Oct 2026] **Flagged, not decided:** Haiku 5.5 runs adaptive thinking by default (default effort `medium`), and thinking tokens are billed as output, so the effort / thinking setting must be fixed before the pilot and frozen with the prompt (A54) |
| A64 | **Reply parsing (amends A56/A61):** a reply "A=a, B=b, C=c" with whole numbers ≥ 0 is valid if 98 ≤ a + b + c ≤ 102; it is then rescaled to sum to 100 (probabilities a/(a+b+c), b/(a+b+c), c/(a+b+c)). Outside 98–102 it is invalid and handled by A61 (retry up to 2 times, then keep `current_action`) | [Decision, planning chat (Max), 10 Oct 2026] Replaces the draft's "must sum to exactly 100" |
| A65 | **LLM request settings for arms 2 and 3 (identical in both):** model `claude-haiku-5-5` (A63); **thinking OFF via the Messages API parameter `thinking: {"type": "disabled"}`** (docs: accepted on Claude Haiku 5.5 at effort `low`, `medium`, `high`; returns 400 at `xhigh`/`max`); `output_config.effort` NOT sent, so the API default applies (`medium` on Claude Haiku 5.5, docs); **`temperature`, `top_p`, `top_k` NOT sent, so the API default applies: temperature = 1** (docs: on Claude Haiku 5.5 any non-default sampling value returns 400 — temperature must be 1, top_p 0.99). No system prompt; the rendered prompt is the single user message. Arm-2 calls use `max_tokens` = 1024 (implementation cap so a reply cannot be cut off; arm 3's cap is set when arm 3 is built, since it returns code). **Pilot comparison only (not a production setting):** thinking ON = `thinking: {"type": "adaptive"}`, effort default, `max_tokens` 16000 | [Decision, planning chat (Max), 10 Oct 2026] Reasoning tokens are billed as output and could multiply arm 2's cost; the same setting must apply to arms 2 and 3. Noted from the docs, not acted on: the migration guide recommends lowering effort rather than disabling thinking on Claude Haiku 5.5 |
| A66 | **Prompt pilot CLOSED (E6); prompt template FROZEN as v1. Prompt rounds are closed.** **Pilot conclusion:** under Claude Haiku 5.5 the arm-2 prompt is age-sensitive and only weakly death-sensitive; the criterion (i) pass in C37 is fragile (margins within repeat noise). The wording W1 (the draft template, unchanged) is selected by the pre-registered rule (C37). **Frozen texts** (`prompts/frozen_v1/`, UTF-8, LF line endings, no trailing newline; written by `experiments/step5_freeze_prompts.py` from `prompts/DRAFT_arm2_arm3.md`, which it asserts equal to the renderer's TEMPLATE; `.gitattributes` marks the folder `-text` so the bytes never change): **arm-2 template `arm2_template_v1.txt`, 997 characters, SHA-256 `fc75ff228eec760454b2a63f98a09a7be756791a50d6b54395f5029152533259`**; **arm-3 instruction `arm3_instruction_v1.txt` (draft section 2 with the template inserted verbatim at its slot, A49), 3,286 characters, SHA-256 `fb28ae6f11f7468a25269c4d789995fb1d5ca5a6242723ec9cc843e7ebfb058f`**. Rendering rules and reply handling as in the draft (A56–A61, A64); request settings A65 | [Decision, planning chat (Max), 10 Oct 2026] Evidence C34–C37 |

## B. Sources — extraction status

| Source | Status | Supplies |
|---|---|---|
| Weitz et al. 2020 *PNAS* 117(51) | **fully extracted** | disease model, all parameters, referent signature, sourced no-behaviour control |
| Gozzi, Perra & Vespignani 2025 *PNAS* 122(24) | **fully extracted from source code** | CBF and EFB rules, `r`/`β_B`/`μ_B`/`γ_beh`, age-stratified IFR, age structure, observation model, integration scheme |
| Urmi et al. 2025 *PNAS* (doi 10.1073/pnas.2500655122) | extracted from preprint | deaths-over-cases; two-component behaviour; PCA 88% one dimension |
| PMT meta-analysis, *IJDRR* 2023 (PII S2212420923002388) | extracted | feature effect sizes |

**B1 — Structural finding.** Gozzi's EFB, *as implemented in code*, is
`1/(1 + short_term·(deaths/dc)^k + long_term·(cum/Dc)^k)` with `k=1` — literally Weitz's
model C denominator. Two independent PNAS groups converge on one functional form.

**B2 — Population.** New York age structure × `IFR_10age` gives a population-weighted IFR of
0.9716%, against Weitz's flat 1.000%. Quota population at N=3,000:

| 0–9 | 10–19 | 20–24 | 25–29 | 30–39 | 40–49 | 50–59 | 60–69 | 70–79 | 80+ |
|---|---|---|---|---|---|---|---|---|---|
| 330 | 337 | 187 | 240 | 472 | 378 | 376 | 333 | 220 | 127 |

Realised mean IFR 0.9718%. Agents aged 60+ are 680 (22.7% of population) and contribute 88.3%
of deaths.

**B3 — Second instance of the project's central claim.** Gozzi's nine-city comparison produces
different winners under different metrics, and their R₀ posteriors for Santiago range from
4.20 [3.96, 4.42] to 1.77 [1.59, 1.97] depending only on which behavioural mechanism is assumed.
Independent of the DFD paper's internal disagreement.

**B4 — Symbol collision.** Gozzi's `mu` = 1/infectious period, `eps` = 1/latent period. Weitz's
`μ` = 1/latent, `γ` = 1/infectious. Same letters, opposite meanings.

**B5 — Parameter conflict.** Weitz: 2 d latent, 6 d infectious. Gozzi: 4 d latent, 2.5 d
infectious. Resolved in favour of Weitz (A2); sweep as sensitivity.

## C. Measured results

**C1 — Minimum N for behaviour to exist at all.** Well-mixed, Weitz model B, T_H=14, 20 seeds,
7-day mean signal:

| N | fadeout | peak I (control) | peak I (awareness) | final S (control) | final S (awareness) |
|---|---|---|---|---|---|
| 100 | 40% | 26.8 | 26.8 | 0.073 | 0.105 |
| 300 | 0% | 74.3 | 68.2 | 0.054 | 0.147 |
| 1,000 | 0% | 230.4 | 187.1 | 0.057 | 0.278 |
| 3,000 | 0% | 687.6 | 404.8 | 0.059 | 0.457 |
| 10,000 | 0% | 2293.8 | 819.3 | 0.058 | 0.658 |

At N=100 the behavioural arm and the control are **numerically identical**.

**C2 — Signal smoothing is required, not optional.** Final S at Weitz's δ_c: raw daily deaths
0.095 vs 7-day mean 0.278 at N=1,000; 0.286 vs 0.658 at N=10,000 (ODE reference 0.686).

**C3 — Scenario separation** (N=1,000, 25 seeds, Weitz reference rule — **to be re-measured
with CBF at N=3,000**):

| Scenario | peak I | final S |
|---|---|---|
| S1 (R₀=3, T_H=14) | 188.2 | 0.278 |
| S2 (R₀=2, T_H=14) | 101.9 | 0.443 |
| S3 (R₀=3, T_H=28) | 203.4 | 0.213 |

S2 separates strongly; S3 separates on final S only. S3 is the one to drop under budget pressure.

**C4 — Shape-metric reliability** (30 seeds, computed on incidence; Cohen's *d* between control
and awareness):

| Metric | N=1,000 | N=3,000 |
|---|---|---|
| final susceptible fraction | 3.76 ✅ | 3.37 ✅ |
| Weitz symmetry (incidence) | 0.60 ❌ | **2.58 ✅** |
| quantile symmetry | 0.38 ❌ | 0.63 ❌ |
| peak share | 0.75 ❌ | 1.09 ~ |
| duration | 0.79 ❌ | 1.24 ~ |

At N=3,000 Weitz symmetry gives control 1.52 ± 0.68 vs awareness 0.28 ± 0.03.

**C5 — Response gradation.** Final S as δ_c varies over 500×:

| N | 1e-6 | 5e-6 | 2e-5 | 1e-4 | 5e-4 | spread |
|---|---|---|---|---|---|---|
| 1,000 | 0.275 | 0.275 | 0.269 | 0.201 | 0.086 | 0.189 |
| 3,000 | 0.385 | 0.399 | 0.407 | 0.259 | 0.084 | 0.323 |
| 10,000 | 0.698 | 0.629 | 0.352 | 0.265 | 0.085 | 0.612 |
| 30,000 | 0.819 | 0.488 | 0.305 | 0.270 | 0.080 | 0.739 |

At N=1,000 a 20× change across Weitz's operating range produces **no change** (0.275, 0.275,
0.269) — the awareness signal is effectively binary.

**C6 — Event counts at N=1,000.** Whole epidemic: 8.2 deaths across 7.4 days; 721 infections
across 61 days. This is why the signature must be measured on incidence.

**C7 — Averaging window matters more than N for response gradation.** Final S across
δ_c ∈ [1e-6, 3e-4], 12 seeds:

| N | signal window | spread |
|---|---|---|
| 1,000 | 7-day (current) | 0.190 |
| 1,000 | 14-day | 0.332 |
| 1,000 | 28-day | **0.447** |
| 1,000 | 56-day | 0.490 |
| 1,000 | cumulative deaths only | 0.017 (useless — a ratchet, saturates) |
| 3,000 | 7-day | 0.274 |
| 3,000 | 28-day | **0.593** |
| 10,000 | 7-day (reference) | 0.629 |

A 28-day window at **N=1,000** (0.447) outperforms a 7-day window at **N=3,000** (0.274).
Trade-off: a 28-day window means agents respond to month-old information, adds ~14 days of lag
comparable to T_H, and departs from Weitz's sourced 7-day smoothing.

**C8 — Test 1 under the 12-substep scheme.** N=100,000, 10/10 seeds, behaviour off, 900 days:
mean final S = 0.05801 vs ODE target 0.0594 (2.34% relative error); implied R0 = 3.0225
(per-seed mean 3.0226 ± 0.0124). [Speculation, high confidence] SEM ≈ 0.0124/√10 ≈ 0.0039; the
0.0226 gap from R0=3.0000 is ~5.8 SEMs, too large to attribute to sampling noise alone. Likely a
small residual bias from discretisation error compounding across the E→I→H→D chain (three
sequential sub-stepped transitions), distinct from the single-transition check in D1 that gave
3.006. Not yet distinguished from an implementation issue — see E15.

**C9 — Substep convergence, resolved.** N=100,000, 30/30 seeds, behaviour off, 900 days
(ODE reference final S = 0.05952 at R0=3.0000 exactly):

| substeps | mean final S | implied R0 | R0 std | SEM | gap (SEM units) |
|---|---|---|---|---|---|
| 12 | 0.05807 | 3.0216 | 0.0150 | 0.0027 | 7.92 |
| 24 | 0.05858 | 3.0140 | 0.0144 | 0.0026 | 5.30 |
| 48 | 0.05955 | 2.9997 | 0.0183 | 0.0033 | **-0.08** |

Gap shrinks monotonically (7.92 → 5.30 → -0.08) and is statistically indistinguishable from
zero at 48 — confirms genuine discretisation bias shrinking as dt→0, rules out an
implementation bug. In relative-error terms: 12 substeps → 2.44% (fails even the old 2%
tolerance), 24 → 1.58% (fails 1%), 48 → 0.05% (passes 1% comfortably). **A20 revised: 48
sub-steps/day, not Gozzi's default of 12.** Gozzi's own model has one fewer sequential
sub-stepped compartment (no H/death-delay chain), so their published default does not carry
enough precision for this model's extra compartment. Convergence order not identifiable from
3 points (bias drops 35% then far more than either O(dt) or O(dt²) predicts — seed noise
contributes at 48), but not needed for the decision: 48 clears the tolerance with margin.

**C10 — Test 1 closed against `src/model.py`.** Repointed from the `experiments/abm.py` pilot
(G2 resolved) with the tolerance tightened 2% → 1% (G1 resolved). N=100,000, 30/30 seeds,
days=900, behaviour off: mean final S = 0.05926 vs ODE target 0.05952 — **0.431% relative
error**. Pass, with roughly 2.3× margin under the 1% gate.

**C11 — Mean-field recovery re-run at full Test 2 scale (N=100,000, 30/30 seeds, days=900, 48
sub-steps/day; `src/model.py`'s `run_weitz_behaviour` fixed to δ(t)=γ_H·H(t), continuous,
recomputed every sub-step, zero lag — D10's fix, now actually applied in `src/`, not just the
`experiments/verify_meanfield_delta_bug.py` diagnostic). ODE reference final S = 0.52502.
`experiments/meanfield_recovery_fullscale.py`, raw output in
`results/meanfield_recovery_fullscale.json`:

| Variant | seeds used | mean final S | relative error | gap in SEMs |
|---|---|---|---|---|
| a. direct-g (deterministic, no per-agent draws) | 30/30 | 0.50105 | 4.56% | −7.11 |
| b. continuous-q (two-sided, redrawn every sub-step — what `src/model.py` implements) | 30/30 | 0.50331 | 4.13% | −6.62 |
| c. daily-q (two-sided, decided once/day — original spec cadence) | 30/30 | 0.49401 | 5.91% | −8.05 |

All three are 6.6–8.1 SEMs below the ODE — statistically real at this scale, not sampling
noise, and **all three land outside even Test 1's 1% tolerance and outside the 2% tolerance
`tests/test_meanfield_recovery.py` currently states.** See D11 for why this contradicts the
5-seed diagnostic, and E16 for the consequence.

**C12 — δ_c sweep confirms the small-H-count hypothesis (D11).** Isolated to the deterministic
`direct-g` variant only (no per-agent draws, no q, no cadence question — cleanest signal),
N=100,000, 30/30 seeds, days=900, 48 sub-steps/day, `experiments/meanfield_deltac_sweep.py`,
raw output `results/meanfield_deltac_sweep.json`. ODE reference recomputed separately for each
δ_c (not reused from C11):

| δ_c | mean peak H (agents) | ODE final S | ABM mean final S | relative error | gap in SEMs |
|---|---|---|---|---|---|
| 0.5 (baseline, C11) | 23.0 | 0.52502 | 0.50105 | 4.56% | −7.11 |
| 2.0 | 66.5 | 0.29368 | 0.29399 | 0.10% | 0.26 |
| 3.5 | 104.8 | 0.27850 | 0.27810 | 0.14% | −0.36 |
| 7.0 | 172.5 | 0.25146 | 0.25347 | 0.80% | 2.23 |

**The bias collapses as δ_c grows: 4.56% → 0.10% → 0.14% → 0.80%, and only δ_c=0.5's gap is
large in SEM terms (the rest are within ~2 SEMs of zero).** [Fact] This confirms D11's
speculation: at δ_c=0.5 the behavioural throttle is being driven by an H-compartment stock that
peaks around 23 agents out of N=100,000 — small enough that the ABM's discrete, stochastic H(t)
diverges materially from the ODE's continuous H(t) feeding the same nonlinear g(·). At δ_c≥2.0,
where peak H is in the tens-to-hundreds, the discrepancy is gone. Note the measured peak H
values (23, 66.5, 104.8, 172.5) run noticeably higher than D11's naive threshold approximation
H≈δ_c·T_H (7, 28, 49, 98) — the epidemic overshoots the point where δ=δ_c before the throttle
turns it over, roughly by a factor of ~2–3×, so use the measured peak-H figures, not the naive
approximation, going forward. **Not yet done this round (deliberately — one variable isolated at
a time):** re-checking whether the two-sided `q` variants (continuous-q, daily-q) show the same
collapse at larger δ_c; whether Weitz's own N=10,000,000/δ_c=50 regime (peak H order ~10⁴–10⁵)
would ever hit this regime at all, versus it being an artifact specific to rescaling δ_c down for
smaller N; and what, if anything, this implies for Test 2's tolerance or for arm 1/2's actual
operating δ_c (register-sourced, not free to change on this basis alone). Reported, not decided.

**C13 — Arm 1's own trigger constant (CBF's γ_beh, not Weitz's δ_c) checked against N=3,000, the
project's actual settled population — higher priority follow-up to C12.**
`experiments/cbf_gamma_beh_scale_check.py`, raw output `results/cbf_gamma_beh_scale_check.log`.

*Sourced constant, verified directly against Gozzi's code* (`models/compartment_model_age_deaths.py`
and `example.ipynb` cell 10 at `github.com/ngozzi/covid-behavior-models`, the same repo already
used for A20/C9's substep-default verification): CBF's global mechanism is
`prob_S_to_SB = β_B·(1 − exp(−γ_beh·deaths_yesterday))`, i.e. `deaths_yesterday` is a raw,
previous-day death **count** (a flow), not a stock like Weitz's H. The only concrete numeric
values anywhere in the repo — `constants.py` carries none, and per-city ABC posteriors are not
published as one canonical number (E8, unchanged) — are the authors' own demo defaults in
`example.ipynb`, run against Madrid (N=6,779,888): **β_B=0.5, μ_B=0.01, r=0.5, γ_beh=10⁰=1**,
swept illustratively over γ_beh∈{1, 0.1, 0.01, 0.001}. [Fact] This is Gozzi's own code default,
same evidentiary status as the `daily_steps=12` default settled empirically in C9 — not a fitted
value.

*Translating γ_beh into "an equivalent count" the way δ_c was is NOT clean, and is reported
rather than decided, for two independent reasons:* (a) γ_beh is the rate constant of an
**exponential** saturating function, not a power-law threshold like `(δ/δ_c)^k` — there is no
single canonical "count" to read off; the half-saturation count `ln(2)/γ_beh` and the e-folding
count `1/γ_beh` differ by <1.5×, so this ambiguity doesn't change the conclusion below, but it is
a choice, not a fact. (b) Gozzi's γ_beh was demonstrated against a **raw same/previous-day death
count**; this project's own arm-1 design (`Design_Spec_Perception_and_Population.md` §3) drives
CBF from a **smoothed rolling-mean** death signal instead (`deaths_7day_mean` there; A8/C7 later
settled the project-wide window at 28 days) — reusing γ_beh unchanged against a differently-scaled
smoothed input is not well-defined without a re-derivation not attempted here.

*What IS clean — the calculation, both ways:* at Gozzi's own reference scale (Madrid,
N=6,779,888, γ_beh=1), the implied half-saturation count is **0.693 deaths/day** — already
sub-single-digit at the AUTHORS' OWN calibration population, before touching N=3,000 at all. If
γ_beh is rescaled the same proportional-to-N way δ_c was (`γ_beh_project = γ_beh_demo ×
N_demo/N_project`), at N=3,000 that gives γ_beh≈2,260 and an implied half-saturation count of
**0.00031 deaths/day** — saturating on the very first death. Both routes land far below
single-digit, i.e. in the *worse-than-broken* range, not the safe tens-to-hundreds range C12
established.

*What is clean regardless of the translation choice — direct simulation, N=3,000, 30/30 seeds,
600 days, 48 sub-steps/day, behaviour OFF (the upper bound; a working throttle only shrinks
these further):*

| Quantity | mean | std | min | max |
|---|---|---|---|---|
| peak H (stock, agents) | 12.93 | 2.61 | 6 | 19 |
| peak daily deaths (flow, raw count) | 2.53 | 0.56 | 2 | 4 |

**[Fact] At N=3,000, the raw counts ANY count-based behavioural trigger would see — Weitz's H
stock or CBF's daily-death flow, regardless of which specific rule or parameter value drives it
— are already in or below C12's "broken" regime (peak H≈23 there gave 4.56% error; N=3,000's own
disease-only ceiling is peak H≈13, peak daily deaths≈2.5), and this is the *ceiling*, not the
typical case, since a working behavioural throttle only suppresses transmission further and
shrinks these counts more.** This reframes the question: it is not only "did we pick a bad δ_c,"
but potentially "is N=3,000 itself too small for any death/hospitalisation-count-based
behavioural trigger to escape the small-count bias regime" — independent of arm 1's specific
rule. N=3,000 is a hard-settled constraint (A7/D3) chosen for a different reason (response
gradation, C5), so this is **reported, not decided**: whether this is a genuine problem for arm
1/Test 2, and if so whether the fix is a different N, a different trigger formulation, or
something else, is for the planning chat.

**C14 — Ceiling scaling check: is peak-H/peak-deaths growth linear in N?** Follow-up to C13,
`experiments/ceiling_scaling_check.py`, raw output `results/ceiling_scaling_check.log`. Same
disease-only (behaviour OFF), 30/30-seed, 600-day, 48-substep/day setup as C13, now also at
N=10,000 and N=30,000:

| N | peak H mean (std, min–max) | peak daily deaths mean (std, min–max) | N-ratio | peak-H-ratio | peak-deaths-ratio |
|---|---|---|---|---|---|
| 3,000 | 12.93 (2.61, 6–19) | 2.53 (0.56, 2–4) | 1.00× | 1.00× | 1.00× |
| 10,000 | 38.10 (4.27, 30–47) | 5.50 (0.92, 4–7) | 3.33× | 2.95× | 2.17× |
| 30,000 | 111.40 (9.91, 92–132) | 12.03 (1.72, 9–16) | 10.00× | 8.61× | 4.75× |

**[Fact] Growth is sub-linear in N for both quantities, and much more so for peak daily deaths
than peak H** (a 10× increase in N gives 8.61× peak H but only 4.75× peak daily deaths — H is a
~14-day-dwell stock accumulating a flow, so it smooths the same sub-linearity further). By
N=30,000, peak H (111.4) sits inside C12's "safe" range (66.5–172.5, ≤0.80% error there); peak
daily deaths (12.0) is still well below C12's H-based safe range, but C12 never tested a
deaths-flow-based trigger directly, so this is not a direct read-across — reported as raw scaling
data only, no N recommendation implied.

**C15 — State-count check (Design_Spec_Perception_and_Population.md §5) at N=10,000/30,000, a
simple stand-in rule, no arm 1 built.** `experiments/state_count_check.py`, raw output
`results/state_count_check.log`. Fields used: `age_band` (10, quota-drawn), `occupation_flex`
and `response_efficacy` (3 bins each, Design_Spec §3/§4's already-decided provisional
Beta(2,2)/fixed defaults — not invented here), `own_health` (3, Sec 2a's fully-specified
mapping), and three population-wide dynamic fields binned with **hand-picked, explicitly
provisional edges** (Design_Spec §8 item 2 states bins are unsettled) — `deaths_28day_mean`
per-capita (8 bins, [0, 0.001]), `cumulative_deaths` per-capita (6 bins, [0, 0.01]), `social_norm`
(10 bins, [0.5, 1.0]). **Omitted:** `local_deaths_7d` (CBF's local/contact-weighted mechanism) —
no contact-network structure exists in the well-mixed `src/model.py` disease model (A5), so
"local" would trivially equal "global" here; this omission removes a factor of 4 from the
design spec's own combinatorial table and is flagged, not silently absorbed. Decision cadence:
every decision-eligible agent (not in H/D) logged every day (p=1, the upper bound on total
decisions — a lower cadence only shrinks the denominator, so this is the most conservative case
for the ratio). One seed per N (a single full run, as asked):

| N | distinct states | total decisions | ratio | compression if perfectly cached |
|---|---|---|---|---|
| 10,000 | 3,364 | 5,946,724 | 0.000566 | ~1,768× |
| 30,000 | 3,040 | 17,840,400 | 0.000170 | ~5,869× |

**[Fact] Distinct states realized (3,040–3,364) are a small fraction even of this stand-in's own
structurally-reachable ceiling** — only 60 of the 90 (age×occ×eff) static combinations are ever
realized (school-age and retired bands have a FIXED, not free, `occupation_flex` per Design_Spec
§3, so they contribute only 1 occ-bin each, not 3 — verified directly, not a bug), giving a
reachable ceiling of 60×3×8×6×10=86,400, of which ~3.5–3.9% is actually visited. **Distinct
states did not grow with N (3,364 at N=10,000 vs 3,040 at N=30,000) while total decisions grew
~3×** — larger N converges the epidemic trajectory closer to its deterministic (ODE-like) shape
(register C9's convergence story), so the number of distinct day-to-day dynamic-bin combinations
visited does not obviously increase with N. **This is a single seed per N, a stand-in rule (not
CBF), and hand-picked bins — reported as a first empirical read, not a settled caching
conclusion.** No N or caching decision made here.

**C16 — δ_c-sweep methodology repeated with CBF's OWN mechanism (not Weitz's) — does N=30,000
work for the real rule?** `experiments/cbf_deltac_sweep.py` (+ an inline extension to larger T,
`results/cbf_deltac_sweep_ext.log`/`.json`), deterministic direct-g only, no per-agent draws, no
S/S^B compartment split — same isolation principle as C12, but this time using CBF's actual
sourced formula (C13): `g_CBF(D) = 1 − β_B·(1 − exp(−γ_beh·D))`, with **D = deaths[t−1], a raw
one-day-LAGGED death count** (CBF's own published design — recomputed once per day, not every
sub-step; this is not the D10 bug being reintroduced, it is what CBF's formula actually
specifies). β_B held at Gozzi's sourced demo value 0.5 throughout (C13); γ_beh swept via its
characteristic count `T = 1/γ_beh`, at values chosen to extend past C12's progression once the
first four points didn't converge. 30/30 seeds, days=900, 48 sub-steps/day, ODE recomputed per
(N, T):

| N | T | mean peak daily deaths | ODE final S | ABM mean final S | relative error | gap (SEMs) |
|---|---|---|---|---|---|---|
| 30,000 | 0.5 | 8.2 | 0.31148 | 0.27435 | 11.92% | −17.92 |
| 30,000 | 2.0 | 9.5 | 0.23202 | 0.20841 | 10.17% | −16.11 |
| 30,000 | 3.5 | 10.2 | 0.18140 | 0.16703 | 7.92% | −12.58 |
| 30,000 | 7.0 | 10.9 | 0.12896 | 0.12282 | 4.76% | −9.02 |
| 30,000 | 15 | 11.6 | 0.09335 | 0.09126 | 2.24% | −4.56 |
| 30,000 | **30** | **11.8** | 0.07652 | 0.07618 | **0.45%** | −0.96 |
| 30,000 | **60** | **11.9** | 0.06800 | 0.06802 | **0.03%** | 0.06 |
| 30,000 | 120 | 12.0 | 0.06375 | 0.06393 | 0.28% | 0.56 |
| 30,000 | 250 | 12.0 | 0.06155 | 0.06190 | 0.57% | 1.10 |
| 10,000 | 0.5 | 4.7 | 0.25686 | 0.17944 | 30.14% | −26.29 |
| 10,000 | 2.0 | 5.1 | 0.13901 | 0.12183 | 12.36% | −11.56 |
| 10,000 | 3.5 | 5.3 | 0.10727 | 0.09984 | 6.92% | −6.92 |
| 10,000 | 7.0 | 5.4 | 0.08379 | 0.08097 | 3.37% | −3.79 |

**[Fact] At N=30,000, the bias does become small — but not until T≈30–60 (γ_beh≈0.017–0.033),
where it's statistically indistinguishable from zero (≤1 SEM).** Below that (T≤15), the error is
large and highly significant (2.2–17.9 SEMs), far worse at every matched T than Weitz's own
mechanism was in C12 (compare: Weitz needed only T≈2.0 to reach ≤0.3 SEMs; CBF needs T≈30–60, an
order of magnitude higher). **Critically, mean peak daily deaths barely changes across this
entire "safe" transition (11.6→11.8→11.9→12.0), sitting right at C14's disease-only ceiling for
N=30,000 (12.03)** — the bias only vanishes once γ_beh is so small that the behavioural effect is
nearly switched off (at T=60, peak transmission reduction is ~9%; at T=250, ~2%), i.e. the model
is converging to something close to Test 1's already-validated no-behaviour case, not to a
meaningfully-behavioural one. A γ_beh anywhere near Gozzi's own sourced demo value (γ_beh=1,
i.e. T=1, between this sweep's T=0.5 and T=2.0 points) shows 10–12% error at N=30,000 — nowhere
near safe.

**Confound, flagged not resolved:** CBF's one-day lag (a discrete, previous-day count, unlike the
corrected zero-lag continuous Weitz mechanism) is itself a plausible independent contributor to
the residual — D10 showed a bare 1-day lag alone produced ~26% error even with H-based δ at
N=100,000. This sweep does not separate "small flow-count" from "one-day lag" as two effects; it
tests CBF's mechanism exactly as published, which has both. Isolating them (e.g. a zero-lag,
continuous-flow variant of CBF's formula) has not been done and is a natural next step, not taken
here since it wasn't asked for this round.

**Answer to "does N=30,000 work for the real rule, not just Weitz's": only for a weak
behavioural effect (T≳30, close to no-behaviour). For anything resembling Gozzi's own
demonstrated γ_beh, N=30,000 is not safe by this measure.** Reported, not decided — no N,
tolerance, or arm-1 design choice has been made on this basis.

**C17 — CBF exactly as arm 1 is actually specified to run (not Gozzi's literal formula): the
bias resolves at both N=10,000 and N=30,000.** Single test, not a sweep — the one configuration
the project actually intends: `experiments/cbf_28day_mean_test.py`. `g_CBF(D) = 1 −
β_B·(1−exp(−γ_beh·D))`, **β_B=0.5 and γ_beh=1 held exactly at Gozzi's sourced value (C13), not
substituted** — the only change from C16 is that **D is the project's actual settled signal, a
28-day rolling mean of daily deaths (A8/C7, Design_Spec §2/§3), using days strictly before today
(shrinking window for the first 28 days), not Gozzi's literal single-day-lagged raw count.**
Deterministic direct-g only, no per-agent draws. The ODE reference is a genuine delay
differential equation (a trailing 28-day integral, `N·(Dcum(t)−Dcum(t−28))/28`) implemented as a
fixed-step (dt=0.25 d) RK4 integrator with a stored cumulative-death history — sanity-checked
against the known Test 1 ODE target with β_B=0 (behaviour off): reproduced 0.05952 to 5 decimals,
confirming the integrator itself is correct before trusting its behavioural-mode output. 30/30
seeds, days=900, 48 sub-steps/day:

| N | mean peak daily deaths | ODE final S | ABM mean final S | relative error | gap (SEMs) |
|---|---|---|---|---|---|
| 10,000 | 5.3 | 0.13260 | 0.12973 | 2.16% | −1.10 |
| 30,000 | 10.0 | 0.21761 | 0.21428 | 1.53% | −1.76 |

**[Fact] Both gaps are within ~2 SEMs of zero — statistically indistinguishable from no bias,
at Gozzi's own sourced γ_beh, unmodified.** This is a dramatic change from C16, where the same
γ_beh=1 (T=1) against Gozzi's own literal one-day-lag signal showed 10,000: ~21% and 30,000:
~11% error (interpolating C16's T=0.5/T=2.0 points), each 15+ SEMs from zero. **The 28-day
averaging — adopted in A8/C7 for an unrelated reason (response gradation at small N, C5/C7) —
also resolves the small-flow-count bias this session has been chasing since C11.** [Speculation,
medium confidence] This is consistent with the working hypothesis all along (C12/D11/C13): the
problem was never γ_beh specifically, it was feeding a nonlinear saturating function a raw,
high-variance single-sample count; a 28-day mean is a ~28x variance-reduction on exactly that
count, so this is the expected mechanism, not a coincidental fix.

**Not yet answered, and not tested this round (not asked):** whether this also holds at
N=3,000 — the project's actual settled operating population (A7/D3), not the N=10,000/30,000
explored this session. C13 already showed N=3,000's own disease-only ceiling (peak daily
deaths≈2.5) is smaller than N=10,000's here (5.3) — smaller than either point in this clean
result — so this is not a foregone conclusion at N=3,000 and would need its own test. Also not
tested: the two-sided (stochastic, per-agent) version of CBF's S/S^B mechanism — this remains a
deterministic direct-g isolation only, per C12/C16's methodology.

**C18 — CBF's REAL S/S^B mechanism (not `direct-g`) built and tested at N=3,000/10,000/30,000
(D12/E17's requested follow-up).** `src/model.py`'s new `run_cbf_behaviour` implements S and
S^B as separate tracked compartments with genuine sub-step competing-hazards transitions,
verified directly against Gozzi's `compartment_model_age_deaths.py` (fetched and read in full
this round): from S, one joint "leave" draw split by relative hazard between adoption
(`prob_S_to_SB = beta_B*(1-exp(-gamma_beh*D(t)))`) and infection (full force of infection); from
S^B, one joint "leave" draw split between relaxation (`prob_SB_to_S = mu_B*(S+R)/N`) and
infection at the reduced rate `r*foi`. With individual agents rather than Gozzi's age-group
binomial counts, the equivalent is two sequential per-agent Bernoulli draws (leave, then
destination) — distributionally identical by multinomial thinning, not an approximation.
beta_B=0.5, mu_B=0.01, r=0.5, gamma_beh=1 (Gozzi's own sourced demo values, C13, unmodified);
D(t) is the project's actual settled signal — a 28-day rolling mean of daily deaths, shrinking
window, days strictly before today (A8/C7, C17's convention) — not Gozzi's own literal
yesterday-count.

Reference: a genuine 7-state (S, S^B, E, I, H, R, D) delay-differential-equation system,
fixed-step RK4 (dt=0.25d), same delay-history convention as the ABM. Sanity-checked first (as
C17's reference was): with beta_B=0, S^B never receives inflow and the system collapses exactly
to Test 1's validated 6-state system — reproduced 0.05952 to 5 decimals (0.0002% relative
error), confirming the integrator before trusting its behavioural-mode output.

`experiments/cbf_real_mechanism_test.py`, raw output `results/cbf_real_mechanism_test.json`/
`.log`. Real per-agent stochastic S/S^B ABM (not `direct-g`), 30/30 seeds, days=900 (C16/C17's
convergence-testing convention, not the 600-day production run length), 48 sub-steps/day:

| N | mean peak daily deaths | ODE final S | ABM mean final S | relative error | gap (SEMs) |
|---|---|---|---|---|---|
| 3,000 | 2.6 | 0.14643 | 0.13979 | 4.54% | −0.90 |
| 10,000 | 4.8 | 0.22199 | 0.23182 | 4.43% | 1.13 |
| 30,000 | 9.2 | 0.29849 | 0.28169 | 5.63% | −3.12 |

**[Fact] Unlike C16/C17's `direct-g` results (which improved or stayed flat as N grew — C17:
2.16%/1.53% relative error at N=10,000/30,000, both gaps <2 SEMs), the real mechanism's relative
error does NOT shrink monotonically with N (4.54% → 4.43% → 5.63%), and the sign of the gap
flips between N=10,000 (+1.13 SEMs) and N=30,000 (−3.12 SEMs).** All three N show a
similar-magnitude relative error (~4.4-5.6%), roughly double C17's `direct-g` error at the
matching N, and N=30,000's gap is the only one exceeding ~2 SEMs.

**[Fact] This is NOT a small-count artifact of the kind C12/D11 found for Weitz's H-stock.** A
diagnostic run (10 seeds/N, not part of the committed batch) measured mean peak S^B population:
555 (N=3,000), 3,999 (N=10,000), 16,122 (N=30,000) — two to four orders of magnitude above C12's
"broken" threshold (peak H≈23-172, where the bias was shown to collapse). The bias here persists
at S^B counts large by C12's own standard, so C12's explanation does not transfer to this
mechanism.

[Speculation, low confidence] The magnitude (~4-6%) and its failure to shrink with N instead
resembles E16's still-open C11 residual — Weitz's own two-sided `q` mechanism (continuous-q)
showed a statistically real 4.13% gap at N=100,000 (30 seeds, large H counts throughout) that
was never explained by small counts either. If the two are related, the common thread may be an
intrinsic mean-field-approximation gap in how a stochastic compartment split interacts with a
nonlinear saturating adoption function, independent of N — but this is not established, only
noted as a parallel worth checking.

**Not decided here (per CLAUDE.md's working convention):** whether ~4-6% is an acceptable
tolerance for Test-2-style closure of the real CBF mechanism; whether N=3,000 (arm 1's actual
operating population, A7/D3) is "safe" by this measure — its own gap (−0.90 SEMs) is not
significant, but its relative error (4.54%) is comparable to N=30,000's significant one, a case
where the SEM criterion and the relative-error criterion disagree, itself worth flagging; what,
if anything, explains the non-monotonic-in-N pattern; and whether any of this changes arm 1's
viability or design. Reported to the planning chat, not decided.

**C19 — C18 re-run at 90 seeds for N=3,000/10,000 (N=30,000 left alone; already >2 SEMs at 30
seeds) to check whether the ~4.5% gap was noise a 30-seed SEM couldn't rule out.**
`experiments/cbf_real_mechanism_seed_check.py` (imports C18's own `_worker`/`ode_final_S`
unchanged — no model or reference change, seeds 0-29 identical to C18's, 60 more added), same
parameters, days=900, 48 sub-steps/day. Raw output `results/cbf_real_mechanism_seed_check.json`/
`.log`:

| N | seeds | mean final S | ODE final S | relative error | gap (SEMs) |
|---|---|---|---|---|---|
| 3,000 | 30 (C18) | 0.13979 | 0.14643 | 4.54% | −0.90 |
| 3,000 | **90** | 0.13906 | 0.14643 | **5.03%** | **−1.66** |
| 10,000 | 30 (C18) | 0.23182 | 0.22199 | 4.43% | +1.13 |
| 10,000 | **90** | 0.23005 | 0.22199 | **3.63%** | **+1.55** |

**[Fact] Neither point estimate collapsed toward the ODE with 3x the seeds** (N=3,000's relative
error rose slightly, 4.54%→5.03%; N=10,000's fell somewhat, 4.43%→3.63%, but not toward zero).
**Both gaps grew in SEM terms** (0.90→1.66; 1.13→1.55) — roughly consistent with a persistent,
non-shrinking bias viewed through a tightening SEM (√(90/30)=1.73× predicts 1.56 and 1.96
respectively from pure variance-reduction alone; observed growth, 1.66 and 1.55, is in the same
range). **Neither individually crosses the "several SEMs" bar C18/this round's request used as
the marker of a confirmed bias** — so this round does not, by itself, settle the question on
the pre-registered criterion. But the direction is uniform across all three N and both seed
counts now measured: no configuration's relative error has approached 0%, and the trend with
more seeds is toward greater statistical confidence in a nonzero gap, not away from it. [Speculation,
medium confidence] Combined with N=30,000's already-significant −3.12 SEMs (C18, unchanged) and
the seed-count trend here, the evidence leans toward "a real, roughly N-independent bias of a
few percent" over "N=30,000 was a 30-seed outlier" — but this is a read of a trend, not a
result that has itself cleared the bar. **Not decided here:** whether to run further seeds to
settle N=3,000/10,000 individually, what magnitude of bias would be tolerable for Test
2-style closure of the real CBF mechanism, and what (if anything) explains a bias that neither
grows nor shrinks with N. Reported to the planning chat.

**C20 — Final interpretation of C18/C19: the ~4-6% gap is real, N-independent, and not a coding
artifact — accepted as a documented limitation, not chased further.** [Decision, planning chat,
informed by C18/C19] Two separate concerns raised by this investigation are now resolved:

1. **C13's small-count concern is resolved.** C13 warned that N=3,000's own raw death/H counts
   sit in or below C12's "broken" small-count regime, raising doubt about whether ANY
   count-based trigger (Weitz's H-stock or CBF's own mechanism) could work at N=3,000 without a
   Jensen's-gap-style bias. C18's diagnostic measured the actual stock at risk for CBF's real
   two-compartment mechanism — peak S^B population — at 555 (N=3,000), 3,999 (N=10,000), 16,122
   (N=30,000): two to four orders of magnitude above C12's threshold (peak H≈23-172) at every N
   tested, including N=3,000. Combined with C17's finding that the 28-day mean already smooths
   the raw death-count input enough to avoid the same bias on the trigger side, both halves of
   the small-count concern are closed. **This is confirmed NOT what explains the remaining gap.**

2. **The remaining ~4-6% relative-error gap between the real CBF ABM and its DDE mean-field
   reference is real and does not shrink with N.** C18 measured 4.54%/4.43%/5.63% relative error
   at N=3,000/10,000/30,000 (30 seeds); C19's 90-seed re-run of the two smaller N moved the point
   estimates to 5.03%/3.63% and pushed both further from zero in SEM terms (0.90→1.66;
   1.13→1.55), while N=30,000 already stood at −3.12 SEMs. No N tested shows the gap collapsing
   toward zero the way Test 1's disease-only convergence does.

3. **Confirmed not a coding bug**, checked two ways, independent of the N-sweep itself: (a) a
   1,000,000-trial Monte Carlo of the competing-hazards two-sequential-Bernoulli-draw code
   against the theoretical joint-multinomial split, across four representative hazard-rate pairs
   including an edge case (zero adoption rate), matched theory within 3× sampling SEM in every
   case; (b) the 28-day rolling-mean window computation, fed the identical death sequence from
   an actual beta_B>0 ABM run, reproduced the DDE reference's cumulative-difference formula to
   within floating-point precision (max diff = 0.0) at every day of a 200-day run, including the
   shrinking-to-full-window transition at day 28.

**[Decision]** Given (1) and (3) rule out the two most likely mechanical explanations, and (2)
shows the gap is stable in magnitude and persistent (though not monotonic in sign) across three
population sizes and two seed counts, this is recorded as a genuine, modest limitation of
comparing this stochastic two-compartment model against its mean-field DDE reference — similar
in kind (though not confirmed in cause) to E16's separately-open Weitz-mechanism residual.
**Recommendation, adopted: treat the ~4-6% gap as a documented, accepted feature of this
comparison rather than a defect to keep chasing with more seeds, more N, or further mechanism
audits.** This closes E18.

**C21 — Per-agent `response_efficacy` wired into CBF's `r`, replacing the flat r=0.5 used
throughout C13-C20's validation round.** `src/model.py` gains
`cbf_r_from_response_efficacy(response_efficacy) = 1 - response_efficacy`, computed once per
agent (static, not recomputed per day — response_efficacy does not change over an agent's
lifetime) inside `run_cbf_behaviour`, which now REQUIRES a length-N `response_efficacy` array
(normally `Population.response_efficacy` from `src/population.py`) in place of the old scalar
`r_factor` parameter.

**[Decision, unsourced]** The mapping itself — higher response_efficacy (an agent's belief that
precautions work) gives a lower residual transmission rate `r_i` while that agent is in S^B —
is a stated modelling choice, not a sourced formula: no paper specifies how response_efficacy
maps onto CBF's `r`, only that response_efficacy is the PMT construct (β=+0.251) that maps to it
(Sourcing_Pack_v3.md Sec 3a, Design_Spec_Perception_and_Population.md Sec 2). **Same
evidentiary status as occupation_flex's own values (A13/A14 area): sourced construct, unsourced
mapping/values.**

Verified before calling this done (`tests/test_cbf_response_efficacy.py`): (a) `r_i == 1 -
response_efficacy_i` checked directly against a handful of values and against a real built
population; (b) the effective cautious transmission rate `r_i * beta` is confirmed strictly
decreasing as response_efficacy rises from 0 to 1 (101-point sweep); (c) `run_cbf_behaviour` now
rejects a `response_efficacy` array of the wrong length instead of silently misaligning it; (d)
a smoke run with the real quota-drawn population wires through end to end without error.

**Realised population-average `r_i`, measured not assumed** (N=3,000, Beta(2,2), seed=0 — the
same population `tests/test_population.py` exercises): response_efficacy mean 0.4992 (SD
0.2216), so **mean r_i = 0.5008**. This lands close to Gozzi's flat demo default (r=0.5, C13)
because Beta(2,2)'s expectation is exactly 0.5 — but this is the realised finite-N draw, not a
guarantee, and would differ under a different seed or a different swept Beta shape (Design_Spec
Sec 6 Step 3's stated later sweep).

**Not done this round (deliberately, per instruction): the N=3,000/10,000/30,000 validation
battery (C18/C19/C20's own tests) has NOT been re-run with per-agent r.**
`experiments/cbf_real_mechanism_test.py` and `experiments/cbf_real_mechanism_seed_check.py`
still call the old `r_factor=` keyword and will error if run as-is — they need updating (build a
`Population` per N, pass `response_efficacy` through) before they can run again. That update,
and the re-run itself, are a separate step.

**C22 — CBF with per-agent response_efficacy-derived r, validated at N=3,000/10,000/30,000
against the same flat-r=0.5 DDE reference used in C18/C19. [Measured, closed]**

**N=3,000 (operating size for all four arms): clean at every seed count tried (10, 30, 90) and
across 5 independent population draws** — relative error 2.59-8.43%, all within 1 SEM of the
reference. No evidence of a problem at the size actually used by the project.

**N=10,000: real, non-zero gap**, confirmed by 5 independent population draws (10 seeds each,
20.0-23.3%) and by extending one population from 30 to 90 seeds (17.34%→16.48%, gap growing
from 3.49 to 5.48 SEMs — stable magnitude, increasing certainty it's real, not noise).

**N=30,000: real but not yet converged** — extending 30→90 seeds moved the estimate itself
(7.53%→12.29%, 3.47→7.54 SEMs), unlike N=10,000 where the estimate held steady. The true
magnitude at this N is unresolved; that it is non-zero was already established (>3 SEMs at 30
seeds, before the instability was found).

**Ruled out as causes, each independently checked:** a bug in `build_population` (independently
re-derived, exact match); a bug in the array-based per-agent hazard rewrite (bit-exact match to
the old scalar code when every agent is given r=0.5); an unusual specific population draw at
N=10,000 (5 independent draws, same result); response_efficacy=0 being mishandled as "no seed"
(checked the literal source, no such branch exists); the hazard formula misbehaving at extreme
response_efficacy values (isolated test at 0.0001/0.9999, correct direction, no NaN/inf/negative
values); a pile-up of extreme agents at N=30,000 (1 agent above 0.999, 0 below 0.001).

**Working hypothesis, unconfirmed:** the DDE reference assumes one shared r for the whole S^B
compartment and has never been rebuilt for per-agent r; mixing many different r values is not
guaranteed to average to the same dynamics as one shared r. Confirming this would require
building a heterogeneous-r mean-field reference — separate, larger scope, not undertaken here.

**Decision:** since no arm in this project runs above N=3,000, and N=3,000 shows no problem,
this is recorded as a documented, accepted limitation of the N=10,000/30,000 stress test only —
not chased further, same treatment as the earlier flat-r gap (C20). Revisit only if a future
stage requires a validated arm 1 above N=3,000 (not currently planned).

**C23 — "Gozzi as-is" arm-1 baseline (step 1 of the supervisor's one-modification-at-a-time
plan): 28-day mean vs yesterday's-deaths signal, with Gozzi's 70% reporting and age-based IFR.
[Measured facts only; no decision taken.]** Planning-chat inputs (not re-decided): flat r=0.5
for every agent; detection 0.7 and per-agent f_D = IFR_10AGE[age_band] adopted; Weitz disease
parameters and 48 sub-steps kept; Gozzi's 14-day Δ NOT added (H with T_H=14 already supplies
the infection-to-death delay).

*Code.* `src/model.py`: `run()` and `run_cbf_behaviour()` accept `f_D` as a scalar (default
0.01) or a length-N per-agent array; `run_cbf_behaviour()` gains `detection_rate` (default 1.0)
and optional `truncate_by_age_band`. Agents perceive reported deaths; the recorded `deaths`
series is always the realised count. Tests: `tests/test_mortality_and_reporting.py` (defaults
bit-identical to the pre-change HEAD code, loaded via git; per-agent f_D mean 0.009718; signal
= window mean of 0.7 × realised; literal-cast mode; detection never changes realised deaths).

*How Gozzi applies 0.7 — from source.* `models/compartment_model_age_deaths.py` line 152
(default `deaths_delay="fixed"`; repo commit 7ddda64):
`deaths[:, (t-1)+int(Delta)] = (detection_rate * np.random.binomial(new_R_day, ifr)).astype(int)`.
It is a **multiplier on the count, not binomial thinning**, followed by an **integer cast per age
group per day**. (The `"gamma"` delay branch, lines 154–163, applies no detection at all.) At
Gozzi's city scale the cast is negligible; at N=3,000 a single death in a band becomes
floor(0.7)=0. [Decision, Max, this session] Main configs use the plain multiplier (no cast); the
literal cast was added as an extra measured config (2T) rather than assumed away.

*Setup.* `experiments/step1_gozzi_baseline.py`, `results/step1_gozzi_baseline.{json,log}`.
N=3,000 quota population (seed 0), r=0.5 flat, β_B=0.5, μ_B=0.01, γ_beh=1, 48 sub-steps, R0=3,
latent 2 d, infectious 6 d, T_H=14, 10 initial infected, 900 days, seeds 0–29 for every config.
Controls are `run_cbf_behaviour` with β_B=0 (identical to the no-behaviour model in
distribution, and same random-number pattern as the behavioural runs, so seeds pair). DDE
reference: C18's `ode_final_S`, now parameterised by `f_D` and `detection_rate` (detection
scales the signal inside γ_beh·D); age-based configs use f_D = 0.009718. DDE sanity check with
β_B=0 reproduced 0.05952 (0.0002% error); default arguments reproduce C18's 0.14643.

| config | window | detection | f_D | final S | peak I | peak S^B | peak daily deaths |
|---|---|---|---|---|---|---|---|
| 1 | 1 | 0.7 | age | 0.18214 ± 0.00647 | 543.1 ± 14.1 | 918.6 ± 47.3 | 2.47 ± 0.10 |
| 2 | 28 | 0.7 | age | 0.14438 ± 0.00868 | 592.5 ± 16.6 | 567.2 ± 62.1 | 2.50 ± 0.11 |
| 3 | 28 | 1.0 | flat 0.01 | 0.13979 ± 0.00740 | 606.5 ± 13.3 | 534.0 ± 47.1 | 2.60 ± 0.10 |
| 2T | 28 | 0.7, per-band floor | age | 0.06533 ± 0.00178 | 676.5 ± 5.1 | 89.4 ± 13.9 | 2.70 ± 0.13 |
| ctrl A | — | — | age | 0.05850 ± 0.00104 | 679.2 ± 4.9 | — | 2.73 ± 0.14 |
| ctrl B | — | — | flat 0.01 | 0.05850 ± 0.00104 | 679.2 ± 4.9 | — | 2.73 ± 0.17 |

Mean ± SEM, n=30 for every cell. Peak I and peak S^B are agent counts. Controls A and B have
identical S and I trajectories because, with no behaviour, f_D only routes I-leavers to H or R
(both non-infectious), and the random draws are the same; only deaths differ (29.3 vs 28.0
total).

*Pass mark (a)* — paired difference from control (same seed), n=30:

| config | Δ peak I | Δ final S | (a) |
|---|---|---|---|
| 1 | −136.2 ± 12.8 (−10.61 SEM) | +0.1236 ± 0.0063 (+19.57 SEM) | pass |
| 2 | −86.8 ± 15.8 (−5.48 SEM) | +0.0859 ± 0.0086 (+10.00 SEM) | pass |
| 3 | −72.7 ± 13.4 (−5.43 SEM) | +0.0813 ± 0.0074 (+11.02 SEM) | pass |
| 2T | −2.7 ± 1.8 (−1.52 SEM) | +0.0068 ± 0.0019 (+3.68 SEM) | fail (peak I) |

*Pass mark (b)* — ABM mean final S vs the continuous-signal DDE, n=30:

| config | DDE | rel. error | gap | (b) ≤6% |
|---|---|---|---|---|
| 1 | 0.20675 | 11.90% | −3.80 SEM | fail |
| 2 | 0.12763 | 13.12% | +1.93 SEM | fail |
| 3 | 0.14643 | 4.54% | −0.90 SEM | pass |
| 2T | 0.12763 (not like-for-like) | 48.81% | −34.95 SEM | fail |

**[Fact] Config 2's (b) failure is within noise at 30 seeds.** At N=3,000, one SEM of final S
is ~6.8% of the reference — larger than the 6% band itself, so a 30-seed run cannot resolve
it. Supplementary run (`experiments/step1_supplement.py`, `results/step1_supplement.{json,log}`;
seeds 0–29 identical to the main run, extended to 0–89):

| config | n=30 rel. error (gap) | n=90 rel. error (gap) |
|---|---|---|
| 1 | 11.90% (−3.80 SEM) | **17.07% (−9.13 SEM)** |
| 2 | 13.12% (+1.93 SEM) | **1.52% (+0.47 SEM)** |
| 3 | 4.54% (−0.90 SEM) | 5.03% (−1.66 SEM) — identical to C19 |
| det 0.7 only, flat f_D | 3.48% (−0.76 SEM) | 4.25% (−1.56 SEM) |
| age f_D only, det 1.0 | 14.97% (+1.99 SEM) | 1.46% (+0.40 SEM) |

The one-at-a-time split shows the high 30-seed config-2 value came from seeds 0–29 running high
under age-based f_D, not from a reference mismatch: both single changes sit within the C18–C20
band at 90 seeds. **Config 1's gap is real and grows with seeds.**

*Other measured items.*
- Runs with any E or I agent at day 600: 0/30 in every config; at day 900: 0/30 in every config.
- **Config 3 vs C18: bit-identical on 30/30 seeds** (mean 0.13979 both; paired diff 0). At 90
  seeds it also reproduces C19 exactly (0.13906).
- Config 2 − config 3 (effect of 70% reporting + age-based f_D together), paired, n=30: final S
  +0.0046 ± 0.0095 (+0.48 SEM); peak I −14.1 ± 17.6 (−0.80 SEM). Not distinguishable from zero.
- Reported/realised deaths, pooled over 30 runs: 0.7000 (configs 1, 2); **0.0668 for 2T** — the
  literal per-band cast removes ~90% of the signal at N=3,000, and behaviour is nearly switched
  off (peak S^B 89 vs 567).
- Diagnostic DDE holding the signal fixed within each day (the ABM's own convention) instead of
  updating it every RK4 step: config 1 ref 0.20331 (rel. error 10.41%, −3.27 SEM), config 2
  0.12539, config 3 0.14368 (2.71%). The convention difference does not explain config 1's gap.
- Mean-field f_D: using f_D = 0.009718 is exact in expectation here, since with flat r the
  infection hazard does not depend on age. It would not be exact with per-agent r (C21/C22).

*Recorded predictions (planning chat, written before running) vs outcome.* Config 1: "passes
(a), fails (b) with relative error > 10%" — **as predicted** (11.90% at n=30, 17.07% at n=90).
Config 2: "passes both" — **(a) pass; (b) fail at the pre-registered n=30 (13.12%, +1.93 SEM)**,
but 1.52% (+0.47 SEM) at n=90.

**Not decided here:** whether yesterday's-deaths is dropped; whether the literal per-band cast
or the plain multiplier is the "as-is" baseline; whether pass mark (b)'s seed count should be
raised given its 30-seed resolution at N=3,000. No settled value was changed.

**C24 — Modification A: per-agent r vs flat r, on the C23-config-2 foundation. [Measured facts
only; no decision taken.]** `experiments/step2_personal_r.py` (+ `step2_common.py`),
`results/step2_personal_r.{json,log}`. Foundation (F): N=3,000 frozen quota population (seed 0),
real CBF, flat r=0.5, β_B=0.5, μ_B=0.01, γ_beh=1, window 28, detection 0.7 (A25), per-agent f_D
(A26), Weitz disease, 48 sub-steps, 10 initial infected, 900 days. PR changes only r:
r_i = 1 − response_efficacy_i (C21), from the same population (response_efficacy mean 0.4992 →
mean r_i 0.5008). Control A = β_B=0. Seeds 0–89 for every config. F and A are bit-identical to
C23's config 2 / Control A on seeds 0–29 (30/30 each).

| | F (flat r) | PR (per-agent r) | A (no behaviour) |
|---|---|---|---|
| final S | 0.12957 ± 0.00412 | 0.13969 ± 0.00506 | 0.05912 ± 0.00063 |
| peak I | 620.7 ± 7.7 | 618.1 ± 8.1 | 679.8 ± 2.6 |
| peak S^B | 463.6 ± 26.2 | 472.7 ± 26.2 | — |
| peak daily deaths | 2.50 ± 0.07 | 2.54 ± 0.07 | 2.69 ± 0.08 |

n=90 for every cell; runs with E or I agents at day 900: 0/90 in each config.

**Primary — paired difference PR − F (same seed), n=90:** final S **+0.01012 ± 0.00107
(+9.47 SEM)**; peak I **−2.63 ± 0.84 (−3.12 SEM)**; peak S^B +9.08 ± 1.48 (+6.13 SEM); peak daily
deaths +0.044 ± 0.027 (+1.65 SEM). **[Fact] Detectable by the stated criterion** (|diff| > 2 SEM
in both final S and peak I). In relative terms: final S +7.8% of F's value, peak I −0.4%.

**Pass mark (a), n=90:** PR vs A: peak I −61.7 ± 8.0 (−7.76 SEM), final S +0.0806 ± 0.0051
(+15.70 SEM) → pass. F vs A: −59.1 ± 7.5 (−7.90 SEM), +0.0704 ± 0.0042 (+16.78 SEM) → pass.

**Pass mark (b):** not applied to PR (the DDE assumes one shared r, C22). F, for continuity
under A27: n=30 13.12% / +1.93 SEM → INCONCLUSIVE; n=90 1.52% / +0.47 SEM → PASS (as C23).

**Recorded prediction (planning chat, written before running):** "PR has slightly higher final S
than F; whether the difference exceeds 2 SEM at N=3,000 is uncertain." **Outcome:** higher
final S, as predicted, and the difference exceeds 2 SEM (+9.47 SEM).

[Speculation, medium confidence] Mean r_i is essentially 0.5, so the shift comes from the
spread of r, not its mean: agents with low r_i (high response_efficacy) are both better
protected and, being uninfected longer, stay in S/S^B, so infection selectively depletes the
high-r agents — the same kind of heterogeneity effect C22 hypothesised for the N=10,000/30,000
gap. Not tested.

**C25 — Modification B: Gozzi disease parameters vs Weitz. Step 3a convergence check FAILED;
3b not run. [Measured facts only.]** Gozzi disease set, checked against source
(`models/constants.py`: `mu = 1/2.5` → infectious_period_days=2.5; `eps = 1/4` →
latent_period_days=4; `example.ipynb`: R0=2.5); transmission rate R0/infectious = 1.0/day.
T_H=14 and everything else unchanged. `experiments/step2_gozzi_disease.py`,
`results/step2_gozzi_disease.{json,log}`. The DDE reference (`ode_final_S`) now also takes the
disease parameters; defaults still reproduce C18 (0.14643) and C23 config 2 (0.12763).

Step 3a (behaviour off, N=100,000, 30 seeds, 48 sub-steps, 900 days; analytical final size
s = exp(−2.5(1−s)) = 0.10736):
- DDE with β_B=0: 0.10736 (0.0046% relative error) — passes.
- **ABM: mean final S 0.10624 ± 0.00040 (n=30), relative error 1.043%, gap −2.79 SEM — FAILS
  the < 1% tolerance.** Per instruction, 3b was not run.

For comparison, the same check under the Weitz set (C9, 48 sub-steps) gave 0.05% relative
error. [Speculation, medium confidence] The ABM sits below the target (more infection than the
continuous model), the same direction as the sub-step discretisation bias C9 measured. The
Gozzi set's rates are larger per step (infectious rate 0.4/day vs 0.167/day, transmission
1.0/day vs 0.5/day), so 48 sub-steps may no longer be enough for it. Not tested — e.g. a
96-sub-step run of the same check would confirm or rule this out. Not decided here.

**C25 addendum — Gozzi disease set at 96 sub-steps: convergence passes; Step 3b run. [Measured
facts only.]** `python experiments/step2_gozzi_disease.py --substeps 96`,
`results/step2_gozzi_disease_96sub.{json,log}`. Only the Gozzi-set configs (3a check, G, CG) use
96 sub-steps; the Weitz foundation F and its control A stay at 48 (main setup unchanged). The
sub-step counts differ because at 48 the Gozzi set failed the < 1% convergence check (above),
while 48 already converges for the Weitz set (C9).

*3a re-check* (behaviour off, N=100,000, same 30 seeds as C25, 96 sub-steps): ABM mean final S
**0.10701 ± 0.00035 (n=30) vs 0.10736 — relative error 0.329%, gap −1.02 SEM → PASS**
(48 sub-steps: 1.043%, −2.79 SEM). Recorded prediction ("passes, well under 1%"): as predicted.

*3b* (N=3,000, seeds 0–29 = C24's first 30; foundation otherwise unchanged; flat r=0.5):

| n=30 | Weitz F (48 sub-steps) | Weitz control A | Gozzi G (96) | Gozzi control CG (96) |
|---|---|---|---|---|
| final S | 0.1444 ± 0.0087 | 0.0585 ± 0.0010 | 0.1984 ± 0.0098 | 0.1038 ± 0.0019 |
| peak I | 592.5 ± 16.6 | 679.2 ± 4.9 | 253.9 ± 6.2 | 281.0 ± 3.5 |
| peak S^B | 567.2 ± 62.1 | — | 602.1 ± 40.2 | — |
| peak daily deaths | 2.50 ± 0.11 | 2.73 ± 0.14 | 2.47 ± 0.12 | 2.43 ± 0.13 |

Runs with E or I agents at day 900: 0/30 in every config.

Behavioural effect (paired vs own control, n=30):
- final S: Weitz +0.0859 ± 0.0086 (+10.00 SEM); Gozzi +0.0946 ± 0.0096 (+9.89 SEM).
- peak I: Weitz −86.8 ± 15.8 (−5.48 SEM, −12.8% of control); Gozzi −27.1 ± 5.1 (−5.34 SEM,
  −9.7% of control).

**Pass mark (a), G vs CG: PASS** (peak I −5.34 SEM, final S +9.89 SEM). Recorded prediction
("G passes (a)"): as predicted.
**Pass mark (b), G vs Gozzi-parameterised DDE (0.20318): relative error 2.37%, gap −0.49 SEM
(n=30) → PASS** under A27; no 90-seed re-run needed. (F at n=30 reads INCONCLUSIVE, 13.12%; at
n=90 it is PASS, 1.52% — C23/C24.)

Other measured facts: Gozzi peak prevalence is ~0.4× Weitz's (shorter infectious period, 2.5 vs
6 d). The N=3,000 no-behaviour final S sits below the analytical value for both sets (CG 0.1038
vs 0.10736, −3.3%; A 0.0585 vs 0.05952, −1.7%). [Speculation, medium confidence] A finite-N effect, since at
N=100,000 both converge; not separately tested.

**C26 — Gradation sweep over γ_beh at N=1,000 and N=3,000. [Measured facts only; no decision on
N or γ_beh.]** `experiments/step2_gradation.py`, `results/step2_gradation.{json,log}`.
Foundation (flat r=0.5 per A29; detection 0.7; per-agent f_D; Weitz disease; 48 sub-steps; 10
initial infected; 900 days). γ_beh ∈ {0.25, 0.5, 1, 2, 4} × Gozzi's sourced default — a
sensitivity sweep, not a calibration. Seeds 0–29 for every config; one no-behaviour control per N.

*Prerequisite code (committed):* `run_cbf_behaviour` now defaults to flat r=0.5, and the C21
mapping sits behind `experimental_r_from_response_efficacy`. C23 config 2 reproduces
bit-identically (30/30 seeds), as do C24's F and PR (90/90 each). The N=1,000 quota population
uses the Design Spec's largest-remainder method. On Gozzi's raw New York `pop_data_Nk.csv`
counts, the same method reproduces the published N=3,000 table exactly. At N=1,000 it gives
**[110, 112, 63, 80, 157, 126, 125, 111, 74, 42]** (same from the raw CSV or from the spec's
2-decimal shares; no near-ties), realised mean IFR **0.971836%** (N=3,000: 0.971791%).

| N | γ_beh | final S | peak I | peak S^B | adoption rate at peak signal (/day) | (a) | (b) |
|---|---|---|---|---|---|---|---|
| 1,000 | ctrl | 0.0554 ± 0.0020 | 233.7 ± 3.2 | — | — | | |
| 1,000 | 0.25 | 0.0650 ± 0.0032 | 229.8 ± 3.7 | 34.1 ± 5.2 | 0.0231 ± 0.0022 | pass | pass (5.28%) |
| 1,000 | 0.5 | 0.0733 ± 0.0043 | 229.0 ± 4.1 | 57.6 ± 9.8 | 0.0443 ± 0.0041 | **fail** (peak I −1.92 SEM) | pass (4.19%) |
| 1,000 | 1 | 0.0857 ± 0.0061 | 225.1 ± 5.0 | 85.4 ± 15.9 | 0.0837 ± 0.0071 | pass | pass (4.73%) |
| 1,000 | 2 | 0.1030 ± 0.0086 | 219.6 ± 6.3 | 122.3 ± 23.0 | 0.1487 ± 0.0105 | pass | inconcl. → pass at n=90 (2.85%) |
| 1,000 | 4 | 0.1277 ± 0.0105 | 215.0 ± 6.7 | 169.5 ± 28.2 | 0.2479 ± 0.0122 | pass | inconcl. → pass at n=90 (1.22%) |
| 3,000 | ctrl | 0.0585 ± 0.0010 | 679.2 ± 4.9 | — | — | | |
| 3,000 | 0.25 | 0.0888 ± 0.0030 | 655.6 ± 7.3 | 227.5 ± 15.5 | 0.0564 ± 0.0022 | pass | inconcl. → pass at n=90 (0.92%) |
| 3,000 | 0.5 | 0.1078 ± 0.0046 | 634.0 ± 10.4 | 347.6 ± 31.6 | 0.1037 ± 0.0038 | pass | inconcl. → pass at n=90 (0.18%) |
| 3,000 | 1 | 0.1444 ± 0.0087 | 592.5 ± 16.6 | 567.2 ± 62.1 | 0.1761 ± 0.0054 | pass | inconcl. → pass at n=90 (1.52%) |
| 3,000 | 2 | 0.1903 ± 0.0130 | 538.3 ± 24.6 | 893.3 ± 98.9 | 0.2761 ± 0.0091 | pass | **FAIL** (16.36%, +2.06 SEM, n=30) |
| 3,000 | 4 | 0.2277 ± 0.0159 | 478.0 ± 30.1 | 1227.4 ± 126.8 | 0.3817 ± 0.0101 | pass | inconcl. → pass at n=90 (4.56%) |

n=30 per cell (the n=90 re-runs affect only the (b) column). Runs with E or I agents at day 900:
0/30 everywhere. Adoption rate = β_B(1 − exp(−γ_beh·D_max)), with D_max the run's maximum
28-day reported-death signal; β_B cap = 0.5/day.

**Gradation (paired adjacent steps in final S, n=30):**
- N=1,000: +5.08, +4.18, +6.18, +6.76 SEM; monotonic → **GRADED** (4/4 steps significant).
- N=3,000: +9.08, +8.37, +9.36, +9.70 SEM; monotonic → **GRADED** (4/4).
- Peak I steps at N=3,000: −4.37, −5.44, −5.57, −8.15 SEM. At N=1,000: −0.83, −2.70, −2.69,
  −2.17 SEM.

**[Fact] The peak death signal scales with N** (raw counts, C13): D_max ≈ 0.19 at N=1,000 vs
0.39–0.48 at N=3,000. So the same γ_beh gives a weaker response at N=1,000: the S1
final-S effect is +0.030 there vs +0.086 at N=3,000.

**Recorded prediction (planning chat):** "steps below γ_beh=1 significant, steps above 1 small
(adoption already near the β_B cap); GRADED at N=3,000." **Outcome:** GRADED at N=3,000, as
predicted. **But steps above 1 are not small** (+9.36, +9.70 SEM; peak-I steps grow), and
adoption at the peak signal is not near the cap: 0.38 of 0.5 at γ_beh=4, 0.18 at γ_beh=1.

*Diagnostic outside the A27 rule (verdict unchanged):*
`results/step2_fail_diagnostic_90.log`. N=3,000 γ_beh=2 extended to seeds 0–89 gives 0.16460
± 0.00645 vs DDE 0.16355: 0.64%, +0.16 SEM. Of the five distinct N=3,000 behavioural points re-run or
diagnosed at 90 seeds (γ_beh 0.25, 0.5, 1, 2, 4; S1 is the γ_beh=1 point), all five moved
closer to the DDE, and all five 30-seed means sat above their 90-seed means. These are not independent observations: common random numbers make
the configs correlated across seeds.

**C27 — Scenario separation S1/S2/S3 with the real CBF arm 1, N=1,000 and N=3,000 (closes the
measurement asked for in E4). [Measured facts only; no decision on N or scenarios.]**
`experiments/step2_scenarios.py`, `results/step2_scenarios.{json,log}`. Scenario_Spec §3:
S1 R0=3/T_H=14, S2 R0=2/T_H=14, S3 R0=3/T_H=28. Each has behaviour (foundation, γ_beh=1) and
its own no-behaviour control. Seeds 0–29. Run length is 900 days (foundation), not the spec's
600. S1 is the same configuration as C26's γ_beh=1 point, and the numbers match.

| N | scen. | final S beh / ctrl | peak I beh / ctrl | peak day beh / ctrl | peak S^B | effect final S | effect peak I | (a) | (b) |
|---|---|---|---|---|---|---|---|---|---|
| 1,000 | S1 | 0.0857 / 0.0554 | 225.1 / 233.7 | 27.3 / 27.2 | 85.4 | +0.0304 ± 0.0055 (+5.49) | −8.6 ± 3.7 (−2.33) | pass | pass (4.73%) |
| 1,000 | S2 | 0.2720 / 0.1969 | 123.2 / 134.2 | 40.3 / 40.2 | 217.8 | +0.0751 ± 0.0111 (+6.79) | −11.0 ± 3.5 (−3.13) | pass | **FAIL** (9.01%, −2.11 SEM, n=30) |
| 1,000 | S3 | 0.0757 / 0.0554 | 227.6 / 233.7 | 27.2 / 27.2 | 74.2 | +0.0203 ± 0.0059 (+3.47) | −6.2 ± 3.5 (−1.75) | **fail** (peak I) | pass (5.12%) |
| 3,000 | S1 | 0.1444 / 0.0585 | 592.5 / 679.2 | 32.4 / 32.2 | 567.2 | +0.0859 ± 0.0086 (+10.00) | −86.8 ± 15.8 (−5.48) | pass | inconcl. → pass at n=90 (1.52%) |
| 3,000 | S2 | 0.4075 / 0.2045 | 268.8 / 352.0 | 50.7 / 52.6 | 1217.8 | +0.2029 ± 0.0169 (+12.03) | −83.1 ± 13.6 (−6.12) | pass | pass (1.59%) |
| 3,000 | S3 | 0.1094 / 0.0585 | 631.7 / 679.2 | 31.7 / 32.2 | 380.1 | +0.0509 ± 0.0066 (+7.74) | −47.5 ± 11.2 (−4.23) | pass | pass (1.88%) |

n=30 for every statistic. Effects are paired differences from the scenario's own control (in
SEMs). Runs with E or I agents at day 900: 0/30 everywhere.

**Separation (difference of behavioural effects vs S1, per seed, n=30):**
- N=1,000: S2 final S +0.0447 ± 0.0082 (+5.43 SEM), peak I −2.4 ± 2.9 (−0.81); S3 final S
  −0.0100 ± 0.0026 (−3.91 SEM), peak I +2.5 ± 1.3 (+1.87). Both separate on final S → **PASS**.
- N=3,000: S2 final S +0.1171 ± 0.0129 (+9.09 SEM), peak I +3.6 ± 9.8 (+0.37); S3 final S
  −0.0350 ± 0.0060 (−5.82 SEM), peak I +39.3 ± 9.9 (+3.96 SEM). Both separate → **PASS**.

**[Fact] S1 and S3 controls are identical in infections on the same seeds** (final S, peak I,
peak day, total incidence identical on 30/30 seeds at both N). Only deaths move: peak daily
deaths S3 − S1 = −0.20 ± 0.11 (N=1,000), −0.30 ± 0.16 (N=3,000).

**Recorded predictions (planning chat) vs outcome:**
- "S3 has a higher peak I than S1 (later reaction)" — N=3,000: yes (631.7 vs 592.5; the effect
  differs by +39.3, +3.96 SEM). N=1,000: 227.6 vs 225.1, the effect difference not significant
  (+1.87 SEM).
- "S2 has a smaller behavioural effect than S1 (weaker death signal)" — **not as predicted.**
  S2's final-S effect is larger (N=3,000: +0.203 vs +0.086; N=1,000: +0.075 vs +0.030). Its
  absolute peak-I effect is not distinguishable from S1's (−83.1 vs −86.8, +0.37 SEM). As a
  fraction of its own control's peak, the reduction is larger in S2 (−23.6% vs −12.8%).
- "Both separate at N=3,000" — as predicted.

*Diagnostic outside the A27 rule (verdict unchanged):* N=1,000 S2 extended to seeds 0–89 gives
0.28934 ± 0.00735 vs DDE 0.29894: 3.21%, −1.31 SEM (`results/step2_fail_diagnostic_90.log`).

**N=1,000 vs N=3,000 on the four criteria (planning chat's decision rule; not applied here):**

| criterion | N=1,000 | N=3,000 |
|---|---|---|
| (a), all 8 behavioural configs | **2 fail**: γ_beh=0.5 (peak I −1.92 SEM), S3 (peak I −1.75 SEM) | all pass |
| (b), A27 rule | **1 FAIL**: S2 (9.01%, −2.11 SEM); passes at n=90 in the diagnostic | **1 FAIL**: γ_beh=2 (16.36%, +2.06 SEM); passes at n=90 in the diagnostic |
| GRADED | GRADED (4/4) | GRADED (4/4) |
| SEPARATION | PASS (on final S only) | PASS |

Not decided here: N, γ_beh, scenario set, or whether A27 should change given the two
borderline n=30 FAILs.

**C28 — Re-scoring under the revised pass mark (b) (A31), and the day-600 check at N=3,000 (A32).
[Measured facts only.]** `experiments/step2_rescore_day600.py`,
`results/step2_rescore_day600.{json,log}`. Old verdicts are kept visible below. **A31 was
adopted after the C26/C27 pattern was observed** (see A31).

*Re-scoring.* Existing 30-/90-seed results reused. The only new 90-seed run the revised rule
required was C23 config 2T (seeds 30–89 added; seeds 0–29 bit-identical to C23, 30/30). "A27"
is the superseded rule (FAIL if > 6% and > 2 SEM at n=30; INCONCLUSIVE → 90 seeds); "as
recorded" is the verdict in the original entry where that differed (C23 predates A27).

| config | n=30: rel. err, gap | n=90: rel. err, gap | as recorded | A27 | **A31** |
|---|---|---|---|---|---|
| C23 config 1 (window 1) | 11.90%, −3.80 | 17.07%, −9.13 | FAIL | FAIL | **FAIL** |
| C23 config 2 (= C24 F = C26 N3000 γ1 = C27 N3000 S1) | 13.12%, +1.93 | 1.52%, +0.47 | FAIL (C23, pre-A27) | INCONCL. → PASS | **PASS** |
| C23 config 3 (C18 setup) | 4.54%, −0.90 | 5.03%, −1.66 (C19) | PASS | PASS | **PASS** |
| C23 config 2T (literal truncation; DDE not like-for-like) | 48.81%, −34.95 | **47.62%, −45.04** (new) | FAIL | FAIL | **FAIL** |
| C23 suppl. det 0.7 only, flat f_D | 3.48%, −0.76 | 4.25%, −1.56 | — | PASS | **PASS** |
| C23 suppl. age f_D only, det 1.0 | 14.97%, +1.99 | 1.46%, +0.40 | — | INCONCL. → PASS | **PASS** |
| C25 G, Gozzi disease, 48 sub-steps | not run (3a failed) | — | — | — | — |
| C25 add. G, Gozzi disease, 96 sub-steps | 2.37%, −0.49 | — | PASS | PASS | **PASS** |
| C26 N1000 γ0.25 | 5.28%, −1.13 | — | PASS | PASS | **PASS** |
| C26 N1000 γ0.5 | 4.19%, −0.74 | — | PASS | PASS | **PASS** |
| C26 N1000 γ1 (= C27 N1000 S1) | 4.73%, −0.69 | — | PASS | PASS | **PASS** |
| C26 N1000 γ2 | 7.30%, −0.95 | 2.85%, +0.61 | INCONCL. → PASS | INCONCL. → PASS | **PASS** |
| C26 N1000 γ4 | 9.66%, −1.30 | 1.22%, −0.26 | INCONCL. → PASS | INCONCL. → PASS | **PASS** |
| C26 N3000 γ0.25 | 6.20%, +1.72 | 0.92%, +0.53 | INCONCL. → PASS | INCONCL. → PASS | **PASS** |
| C26 N3000 γ0.5 | 6.45%, +1.42 | 0.18%, +0.08 | INCONCL. → PASS | INCONCL. → PASS | **PASS** |
| C26 N3000 γ2 | 16.36%, +2.06 | 0.64%, +0.16 (C26 diagnostic) | FAIL | FAIL | **PASS ← changed** |
| C26 N3000 γ4 | 9.52%, +1.24 | 4.56%, −1.16 | INCONCL. → PASS | INCONCL. → PASS | **PASS** |
| C27 N1000 S2 | 9.01%, −2.11 | 3.21%, −1.31 (C27 diagnostic) | FAIL | FAIL | **PASS ← changed** |
| C27 N1000 S3 | 5.12%, −0.63 | — | PASS | PASS | **PASS** |
| C27 N3000 S2 | 1.59%, +0.37 | — | PASS | PASS | **PASS** |
| C27 N3000 S3 | 1.88%, +0.30 | — | PASS | PASS | **PASS** |

Gaps in SEMs. Not scored: C24 PR ((b) does not apply, C22/C24). C25 addendum's F is C23
config 2.

**Recorded prediction (planning chat):** "only C26 N=3,000 γ_beh=2 and C27 N=1,000 S2 change
(FAIL → PASS); nothing else changes." **Outcome: as predicted** against A27. Against the original
C23 wording, C23 config 2 also reads PASS now, but that change already happened under A27.
**Remaining (b) FAILs under A31: C23 config 1 (one-day signal; rejected in A24) and C23
config 2T (literal truncation; rejected in A25).**

*Day-600 check, N=3,000, seeds 0–29, re-run at days=900* (final S and peak I bit-identical to the
stored C26/C27 runs on 30/30 seeds for every config):

| config | runs with E+I > 0 at day 600 | latest day E+I > 0 (all runs) | median last active day |
|---|---|---|---|
| control (C26; = C27 S1 control) | 0/30 | 126 | 93 |
| γ_beh 0.25 | 0/30 | 126 | 91 |
| γ_beh 0.5 | 0/30 | 126 | 91 |
| γ_beh 1 (= C27 S1) | 0/30 | 131 | 92 |
| γ_beh 2 | 0/30 | 213 | 99 |
| γ_beh 4 | 0/30 | 235 | 109 |
| C27 S2 behaviour | 0/30 | **401** | 132 |
| C27 S2 control | 0/30 | 173 | 136 |
| C27 S3 behaviour | 0/30 | 126 | 91 |
| C27 S3 control | 0/30 | 126 | 93 |

"Day d" = the end-of-day state at index d−1 (C23 convention).

**Recorded prediction:** "0 runs still infected at day 600 everywhere; S3 and γ_beh=0.25 the most
likely exceptions." **Outcome: 0/30 everywhere, as predicted.** The longest tails are not S3 or
γ_beh=0.25 (both 126, the same as the control). They are S2 with behaviour (401) and the strongest
γ_beh points (γ=4: 235; γ=2: 213). The latest activity anywhere is 199 days before day 600.
This check covers E+I only; deaths after day 600 were not counted directly. Agents already in H
can still die after E+I reaches 0, with exponential H exits (mean 14 d; 28 d in S3). Computed
bound, not measured: an agent entering H at the latest active day is still in H at day 600 with
probability exp(−199/14) ≈ 6.7×10⁻⁷ (S2, day 401). For S3 (day 126, T_H=28) it is
exp(−474/28) ≈ 4.4×10⁻⁸.

**C29 — Step 3 Phase 1: candidate shape metrics validated on KNOWN cases only (no arm scored).
[Measured facts only; the final metric is not chosen here.]** `experiments/step3_shape_metrics.py`;
outputs in `results/step3/` (`sim_series.npz`, `stage1.{json,log}`, `stage2.{json,log}`, figures
`K1_ode.png`, `K2_abm_N100000.png`, `K3_abm_N3000.png`). Staged run, as instructed: stage 1 scored
P1–P3 at default settings for every metric; stage 2 ran P4 only for metric/kind pairs passing
P1–P3. A metric failing P1–P3 fails regardless of P4. Criteria P1–P4 were fixed by the planning
chat before running and are unchanged.

*Known cases (600 days; daily incidence, i.e. new infections per day, is the primary series; seeds
0–29 everywhere):*
- **K1, Weitz model B ODE.** Implemented from Weitz's own code (`seirdelay_plat.m`,
  jsweitz/covid19-git-plateaus): β=0.5, latent 2 d, infectious 6 d, T_H=14, f_D=0.01, initial
  E=1/N with N=10⁷. Daily incidence = S(t)−S(t+1). (a) no behaviour; (b) g = 1/(1+(δ/δ_c)^k),
  δ = γ_H·H, Nδ_c = 50, **k = 2**. k is sourced from Weitz's model-B scripts
  `figseir_Hdel_k2.m` and `figseir_Hlong_k2D.m` (`pars.awareness = 2`, `Dcrit = 0.5e-5`),
  not from a PNAS figure number. That repo's model-A script `figseir_baseplat_k2_D.m` sweeps
  k ∈ {1, 2, 4}, and `figseir_phase2.m` uses k = 1.
- **K2, Weitz-rule ABM, N=100,000.** `run_weitz_behaviour` (continuous-q, δ_c = 0.5, k = 2;
  the C11/Test 2 configuration) and its control `run()` on the same seeds.
- **K3, no-behaviour ABM, N=3,000.** `run()` with per-agent f_D (A26), 48 sub-steps.

*Metrics, as sourced or as instructed (plateau direction in brackets):*
- **M1** EpidemicKabu 0.2.7 (pip; Ruiz G. & Ruales B.): number of waves = cut points + 1. The
  library pipeline is called exactly as `waves.run()` minus its CSV/plot output. Kernel 18 is the
  library's only built-in value; `fbi` = 0 (signature default). [more waves — the direction is
  an operationalisation agreed with Max, not sourced]
- **M2** Hoen et al. 2015 (JMIR 17:e169) two-peak metric, Multimedia Appendix eq. S1:
  TP = max over i<j of √((sᵢ−vᵢⱼ)(sⱼ−vᵢⱼ)), vᵢⱼ = min over i≤k≤j of sₖ. Applied to per-capita
  incidence; no tunables. [higher]
- **M3** T10–90 duration. [longer]
- **M4** peak-to-mean ratio over the T10–90 window. [lower]
- **SA** symmetry coefficient as implemented in `experiments/metrics.py` (`sym_pt`: centred
  7-day moving average; cutoff·peak / value at t_P+Δt). Verified identical to `metrics.py` on
  10/10 test runs. [lower]
- **SB** symmetry coefficient per Weitz's R code (`deaths/national_deaths_metric.R`: zero days
  dropped, `loess(log y ~ day)` with R defaults span 0.75 / degree 2, D_l/D_r at the 10%
  cutoff). **An approximation:** R is not installed, so this is a direct tricube local-quadratic
  fit rather than R's default kd-tree interpolation surface, on a 0.1-day grid rather than
  0.01. [lower]
- **M5** averaged curve: runs aligned at the first day cumulative incidence ≥ 1% of N, per-capita
  mean over the common window, then M3/M4/SA/SB on it, with a 1,000-resample bootstrap over runs
  (seed 20261004, 95% percentile interval).

**Stage 1, default settings** (n defined / 30 for every per-run statistic; paired = K2 behaviour −
K2 control, same seed):

| metric | P1: K1 ODE ctrl → beh | P2: K2 per-run (n beh/ctrl; paired diff) | P2: K2 averaged (95% CIs) | P3: K3 per-run mean / averaged | K3 SD ÷ K1 gap | P1–P3 |
|---|---|---|---|---|---|---|
| M1 waves | 1 → 4 ✓ | 30/30; 1.00 → 8.57, +7.57 ± 0.14 (+53.6 SEM) ✓ | — | 1.00 (all 30 runs = 1) ✓ | 0.00 | **pass** |
| M2 TP | 5.6×10⁻¹⁰ → 9.8×10⁻⁴ ✓ | 30/30; +2.1×10⁻⁴ ± 1.3×10⁻⁴ (+1.58 SEM) ✗ | — | 0.0122 — closer to beh ✗ | 2.27 | fail |
| M3 T10–90 | 23 → 461 d ✓ | 30/30; 23.5 → 483.5, +460 ± 4.4 (+103.8 SEM) ✓ | beh 477 [465, 487] vs ctrl 23 [22, 23] ✓ | 23.2 / 23 ✓ | 0.002 | **pass (both)** |
| M4 peak/mean | 1.435 → 3.822 ✗ (wrong direction) | 30/30; +4.22 ± 0.33 (+12.8 SEM, wrong direction) ✗ | beh 4.02 [3.45, 4.70] vs ctrl 1.43 [1.40, 1.44], wrong direction ✗ | 1.551 / 1.437 ✓ | 0.03 | fail |
| SA sym (metrics.py) | 0.841 → 0.432 ✓ | **29**/30 ✗; −0.217 ± 0.088 (−2.47 SEM) | beh undefined (0/1,000 bootstrap curves) ✗ | 0.939 / 0.918 ✓ | 0.67 | fail |
| SB sym (Weitz LOESS) | 1.321 → 0.147 ✓ | **0**/30 behaviour runs defined ✗ | beh and ctrl undefined (0/1,000 each) ✗ | 1.007 ✓ / K3 0.884 (closer to ctrl) but K2-ctrl averaged undefined ✗ | 0.11 | fail |

**Stage 2, P4** (only M1 per-run and M3 per-run / averaged qualified; verdicts at every variant
equal the default's):
- **M1, kernel 9 / 36:** ODE 1 → 4 / 1 → 2; paired +9.87 (+39.1 SEM) / +4.67 (+38.7 SEM);
  K3 mean 1.067 / 1.000. All of P1–P3 hold → **P4 pass**.
- **M3, 5–95 / 20–80, per-run:** ODE 32 → 503 / 15 → 339; paired +501 (+196.7 SEM) /
  +345 (+67.2 SEM); K3 31.2 / 14.2 → **P4 pass**.
- **M3 averaged, 5–95 / 20–80 / alignment 0.5% / 2%:** beh vs ctrl CIs [525, 535] vs [31, 31];
  [339, 364] vs [14, 15]; [472, 491] vs [23, 23]; [446, 468] vs [23, 23]. K3 averaged
  31 / 14 / 24 / 23 → **P4 pass**.

**PASS list: M1 (EpidemicKabu wave count, per-run); M3 (T10–90, per-run); M3 on the averaged
curve (M5).** **FAIL list:** M2 (P2, P3); M4 per-run and averaged (P1, P2 — wrong direction);
SA per-run (P2) and averaged (P2); SB per-run (P2) and averaged (P2, P3).

**Recorded predictions (planning chat) vs outcome:**
- "M3 passes all": as predicted.
- "M4 passes all": **not as predicted.** It fails P1 on the ODE itself: the plateau's
  peak-to-mean ratio is *higher* (3.82 vs 1.44), because the plateau's T10–90 window is long
  and low relative to its early peak.
- "Per-run symmetry fails P2 (< 30/30 or wrong direction)": as predicted, for both versions
  (SA 29/30; SB 0/30).
- "M5 symmetry on the averaged curve may pass": **did not.** The averaged K2 behaviour curve has
  no pre-peak 10% crossing: by the time 1% has been infected, incidence is already at 82% of
  the averaged peak, which comes 5 days later. The same holds at 0.5% and 2% alignment (day 0
  at 50% and 100% of peak). This is structural for this behaviour case, not noise.
- "M1 uncertain": passes.

**Caveats, measured:**
- **The behaviour cases are not finished at day 600.** All 30/30 K2 behaviour runs are still
  infecting at day 600 (mean 48 per day over days 571–600, vs a mean peak of 347). Cumulative
  incidence by day 600 is 0.370 (K2) and 0.339 (K1 ODE). The ODE reaches 0.678 by day 2,000,
  where its T10–90 would be 1,249 d. So on K1(b)/K2, M3 partly measures the 600-day window, not
  the epidemic's full duration. All K2 control and K3 runs have ended (0/30 active in the last
  30 days). (C28: no arm-1 run at N=3,000 was active after day 401.)
- **M1 on K2 behaviour counts 8.6 waves vs the ODE's 4.** The extra waves come from stochastic
  wiggles on a long low plateau at N=100,000. P3 tests only the no-behaviour side for fake
  plateaus; it does not test over-counting on a genuine plateau.
- **SA and SB disagree on the no-behaviour ODE** (0.841 vs 1.321). The symmetry coefficient is
  sensitive to its smoothing method; see D14.
- Simulation wall time was 6.8 min (90 runs).

**C30 — Arm 1 scored on the frozen shape-metric list (A33–A35). [Measured facts only; no
decision on which metric "wins" or what the score means for the project.]**
`experiments/step3_score_arm1.py`; outputs `results/step3/arm1_scores.{json,log}`, figures
`arm1_S1.png`, `arm1_S2.png`, `arm1_S3.png`, `arm1_stretch_summary.png`. Foundation arm 1, N=3,000,
**days=600**, seeds 0–29: (a) S1/S2/S3 with own controls (C27); (b) S1 at γ_beh 0.25–4 sharing
the S1 control (C26). S1 = γ_beh 1 (one configuration, run once). No daily series had been
cached by C26/C27, so all 10 configs were re-run with series kept. **Final S and peak I are
bit-identical to the stored C26/C27 runs on 30/30 seeds for all 10 configs.** M3 = T10–90 on
daily incidence; stretch = arm M3 ÷ own-control M3 (A34). Bootstrap: 1,000 paired resamples of
seeds (seed 20261005).

**Truncation (A35): every config valid.** 0/30 runs with E+I > 0 at day 600, for all 7 arm
configs and all 3 controls.

| config | M3 arm / control (d, mean ± SEM) | paired Δ M3 (d) | stretch, ratio of means [95% CI] | stretch, mean per-seed ratio | averaged-curve M3 arm / ctrl [95% CI] | M1 waves arm / ctrl; paired | peak I reduction | final S increase |
|---|---|---|---|---|---|---|---|---|
| S1 (= γ 1) | 24.93 ± 0.85 / 23.10 ± 0.20 | +1.83 ± 0.83 (+2.21 SEM) | ×1.079 [1.018, 1.158] | ×1.080 ± 0.036 | 26 [24, 27] / 23 [22, 23] | 1.00 / 1.03; −0.03 (−1.00 SEM) | 12.8% (−5.48 SEM) | +0.0859 (+10.00 SEM) |
| S2 | 53.23 ± 9.13 / 42.97 ± 0.63 | +10.27 ± 9.23 (+1.11 SEM) | ×1.239 [0.962, 1.704] | ×1.257 ± 0.230 | 45 [41, 54] / 44 [42, 45] | 1.20 / 1.03; +0.17 (+1.54 SEM) | 23.6% (−6.12 SEM) | +0.2029 (+12.03 SEM) |
| S3 | 23.57 ± 0.45 / 23.10 ± 0.20 | +0.47 ± 0.42 (+1.11 SEM) | ×1.020 [0.987, 1.057] | ×1.021 ± 0.018 | 23 [22, 25] / 23 [22, 23] | 1.00 / 1.03; −0.03 (−1.00 SEM) | 7.0% (−4.23 SEM) | +0.0509 (+7.74 SEM) |
| γ 0.25 | 23.23 ± 0.29 / 23.10 ± 0.20 | +0.13 ± 0.21 (+0.63 SEM) | ×1.006 [0.989, 1.024] | ×1.006 ± 0.009 | 23 [22, 24] / 23 [22, 23] | 1.00 / 1.03; −0.03 (−1.00 SEM) | 3.5% (−5.20 SEM) | +0.0303 (+11.23 SEM) |
| γ 0.5 | 23.67 ± 0.45 / 23.10 ± 0.20 | +0.57 ± 0.42 (+1.34 SEM) | ×1.025 [0.993, 1.063] | ×1.025 ± 0.018 | 23 [23, 25] / 23 [22, 23] | 1.00 / 1.03; −0.03 (−1.00 SEM) | 6.7% (−5.16 SEM) | +0.0493 (+11.05 SEM) |
| γ 1 (= S1) | as S1 | | | | | | | |
| γ 2 | 28.53 ± 1.72 / 23.10 ± 0.20 | +5.43 ± 1.69 (+3.22 SEM) | ×1.235 [1.103, 1.393] | ×1.234 ± 0.072 | 30 [26, 34] / 23 [22, 23] | 1.03 / 1.03; 0.00 | 20.7% (−5.88 SEM) | +0.1318 (+10.25 SEM) |
| γ 4 | 34.17 ± 3.09 / 23.10 ± 0.20 | +11.07 ± 3.05 (+3.63 SEM) | ×1.479 [1.256, 1.753] | ×1.474 ± 0.129 | 38 [29, 50] / 23 [22, 23] | 1.03 / 1.03; 0.00 | 29.6% (−6.77 SEM) | +0.1692 (+10.72 SEM) |

n = 30/30 defined for every statistic (M3, M1, averaged curve: all runs used). Reference
marker (A34): Weitz plateau stretch ≥ ×20 (K1 ODE 461/23 = ×20.0; K2 averaged 477/23 = ×20.7;
both truncated at 600 d, C29). All arm-1 stretch factors are between ×1.006 and ×1.48.

**[Fact] S2's stretch is driven by a few runs, not a shift of the whole distribution.**
- Per-run S2 M3: median 41 d (control median 42 d). Top five: 47, 65, 79, 83, **311** d
  (control maximum 52 d).
- 4/30 runs are stretched > ×1.5. **The median per-seed ratio is ×0.964.**
- M1 counts 2–3 waves on 4/30 S2 runs, including the 311-day run (3 waves).
- The averaged S2 curve is lower but not wider (45 vs 44 d) — see `arm1_S2.png`.
- So S2 is "longer + separate waves" on a few seeds, in A34's terms, while the bulk of runs is
  lower but not longer.
- γ 4 also has a tail: median 26 d, maximum 91 d.

**Agreement M3 vs M1:**
- Spearman across 210 arm runs (7 distinct configs × 30; S1 = γ 1 counted once): **ρ = 0.268**
  (p = 8×10⁻⁵).
- Config order by mean M3: γ0.25 < S3 < γ0.5 < S1 < γ2 < γ4 < S2.
- **Not the same order** by mean M1, but M1's ordering is mostly ties: S1, S3, γ0.25 and γ0.5
  are all 1.00 waves, γ2 and γ4 are both 1.03, and only S2 (1.20) stands apart. So the "order"
  among tied configs is arbitrary. Spearman over the 7 config means: 0.896 (with ties).
- M1 is near-constant: 1 wave on 204/210 arm runs.

**Recorded predictions (planning chat) vs outcome:**
- "S1 stretch clearly > ×1 and far below ×20 (rough guess ×1.5–3, low confidence)": > ×1
  (CI [1.018, 1.158] excludes 1) and far below ×20, as predicted. **Below the guessed range:
  ×1.08.**
- "S2 the largest stretch of S1/S2/S3, S3 the smallest": **point estimates as predicted**
  (×1.24 > ×1.08 > ×1.02). But S2's CI includes ×1 [0.96, 1.70] and overlaps S1's, its median
  per-seed ratio is below 1, and S3's CI also includes ×1.
- "Stretch rises monotonically with γ_beh": **as predicted in point estimates** (×1.006, 1.025,
  1.079, 1.235, 1.479). The adjacent CIs overlap below γ=1, and the CIs at γ 0.25 and 0.5
  include ×1.
- "M1 and M3 strongly correlated (Spearman > 0.7)": **not as predicted** across runs (ρ = 0.268).
  The cause is M1's near-zero variance (1 wave on 204/210 runs).

Not decided here: which metric "wins", or what arm 1's score means for the project.

**C31 — Step 4: shared-world checks (A37–A45). PRE-REGISTRATION, written before any timing or
check run; amended 10 Oct 2026 before running (see "Amendments" below).** Code: `src/shared_world.py` (`run_shared_world`, `CBFArm1`, `AlwaysNormal`,
`ForcedPrecautions`, `ForcedStayHomeFraction`), `experiments/step4_shared_world_checks.py`, output
`results/step4/checks.{json,log}`. Prior evidence, stated so it is not mistaken for a prediction:
`tests/test_shared_world.py` already passed bit-identity on small cases before this entry was
written (AlwaysNormal vs `run()`, N=2,000, 3 seeds × 200 days; CBFArm1 vs `run_cbf_behaviour`,
N=3,000, 2 seeds × 150 days).

*Check 1 — no behaviour.* AlwaysNormal vs `run()`, Test 1's setup (N=100,000, seeds 0–29, 900 d,
R₀=3, f_D=0.01). **Pass** = bit-identical daily S, prevalence, incidence, deaths on 30/30 seeds
(fallback: mean final S within 1 SEM, with an explanation). **Prediction (Max):** identical.

*Check 2 — known-answer physics.* N=100,000, seeds 0–29, 900 d (A32's mean-field convention),
f_D=0.01. ODE = Weitz model B (Test 1's equations) with the ABM's own initial condition,
I(0)=10/N (Test 1's I(0)=10⁻⁶ also reported; it matters only for (c), see D15). **Pass** = mean
final S within 1% relative error of the reference (Test 1's tolerance).
- (a) S1, every never_ill agent in precautions from day 0 → ODE β×0.5: **0.41708**.
- (b) S1, a fixed random 50% of never_ill agents (49,995 of 99,990) stay home all run →
  **reference corrected (D15): ODE with that fraction held non-infectable, 0.70840.** The
  originally stated reference, ODE β×0.5 (0.41708), is also reported; it is predicted to FAIL by
  ~70% because the two are not equivalent in final size (D15).
- (c) S2, as (a) → ODE β×0.5 (R_eff = 1.0, critical): **0.99062**. ~~Pass = final S within 1%~~
  **→ REPORT-ONLY, no pass/fail (amended 10 Oct 2026, BEFORE running; planning chat):** the
  case is critical and its attack rate is ~0.9%, so a 1% relative tolerance on final S is
  meaningless. Final S and attack-rate relative error are reported.
- N=3,000 ceiling, (a) S1 and (c) S2 vs own AlwaysNormal control, 600 d, foundation population
  (per-agent f_D), 30 seeds: stretch (ratio of means [95% CI], median per-seed ratio, share
  > ×1.5, A36), peak reduction, final S, M1 waves, runs finished by day 600 (A35).
- **Predictions (Max):** (a) and (b) pass; (a) at N=3,000 S1: stretch roughly ×2–4, 1 wave, no
  plateau (low confidence); (c): very slow epidemic, possibly not finished by day 600 (duration
  then invalid per A35).
- **Predictions (Claude Code), [Speculation]:** (b) passes against the corrected reference and
  fails against β×0.5 (computed, high confidence). (a) at N=3,000: stretch ×3–4 (growth rate
  0.058/d vs 0.194/d at R₀=3 gives ~×3.4; medium confidence), 1 wave. (c) at N=3,000: a critical
  branching process from 10 seeds — mostly small outbreaks that end well before day 600, with a
  minority (0–4 of 30) still active at day 600, which would flag (c) TRUNCATED (medium
  confidence). (c) at N=100,000 passes the 1% final-S mark.

*Check 3 — arm 1 inside the shared world.* CBFArm1 vs `run_cbf_behaviour`, S1/S2/S3, N=3,000,
seeds 0–29, 600 d, foundation (r=0.5, β_B=0.5, μ_B=0.01, γ_beh=1, window 28, detection 0.7,
per-agent f_D). Controls: β_B=0 in both engines. **Pass** = bit-identical; or, if the random
streams differ, paired difference in mean final S and in mean peak I each within 2 SEM AND
stretch within C30's 95% CI. **Prediction (Max):** pass (bit-identical if the RNG order matches).

*Timing rule:* 2 seeds per config first; if the upper-end projection exceeds 10 min, stop and
report before running.

*Amendments (planning chat, Max, 10 Oct 2026), all made BEFORE any check was run:*
- **Seed counts (option (b)).** N=3,000: Checks 1, 2 and 3 at **30 seeds (0–29)**. N=100,000:
  Checks 1 and 2 at **10 seeds (0–9)**, not 30. Check 1's and Check 2(a)/(b)'s pass marks are
  applied to the N=100,000 runs at 10 seeds.
- Check 2(c) → report-only (above).
- D15 accepted: (b)'s pass mark uses the corrected reference; β×0.5 stays the predicted-fail
  comparison.
- Added by Claude Code to fill option (b), stated here so it is not mistaken for a result:
  Check 1 at N=3,000 = Test 1's setup with N=3,000 (f_D 0.01, 900 d) **plus** the two N=3,000
  600-day foundation controls (S1, S2, per-agent f_D) against `run()`; pass = bit-identical,
  as at N=100,000. Check 2 at N=3,000 = (a), (b), (c) at 600 d, foundation population, compared
  with ODEs at I(0)=10/3,000 and 600 d: (a) 0.41351, (b) 0.70241 (β×0.5: 0.41351), (c) 0.92082
  — **reported, no pass mark**, because the 1% tolerance is Test 1's large-N tolerance and the
  no-behaviour N=3,000 final S already sits 1.7% below the ODE (C25: 0.0585 vs 0.05952, n=30).
  Ceiling numbers are also computed for (b), not only (a) and (c).
- **Prediction added (Claude Code), [Speculation, medium]:** Check 2(a)/(b) at N=3,000 sit
  below their ODE by a few percent in final S, the same direction as the no-behaviour finite-N
  offset in C25.

*Timing, measured (`--timing`, seeds 0–1 of every config, 42 runs on 16 workers, wall 121.7 s;
`results/step4/timing.log`).* Per run, under parallel load: Check 1 `run()` 29.6–30.6 s,
shared world 49.7–51.1 s; Check 2 N=100,000 (a) 95.5–107.9 s, (b) 74.5–83.8 s, (c) 27.9–119.3 s;
every N=3,000 config 0.5–4.2 s. Upper-end projection for 30 seeds (slowest timed run × 30 per
config): 13,003 CPU-s = **13.5 min** on 16 workers before EpidemicKabu; scaling the timing wall
×15 gives 30.4 min. **Both exceed the 10-min limit, so no check was run.** Reported to the
planning chat.

**C31 results. [Measured facts only.]** Run after commit a1932de (code and pre-registration
unchanged since). `python experiments/step4_shared_world_checks.py`; `results/step4/checks.{json,log}`.
680 runs (N=100,000: seeds 0–9; N=3,000: seeds 0–29); simulation wall 6.0 min, total wall
9.3 min including EpidemicKabu and bootstrap, 16 workers.

*Check 1 — PASS everywhere.* Bit-identical daily S, prevalence, incidence and deaths, AlwaysNormal
in `run_shared_world` vs `run()`:

| setup | bit-identical | mean final S (run / world) |
|---|---|---|
| N=100,000, Test 1 setup (f_D 0.01, 900 d) | 10/10 | 0.05905 / 0.05905 |
| N=3,000, Test 1 setup | 30/30 | 0.05866 / 0.05866 |
| N=3,000, S1 foundation control (per-agent f_D, 600 d) | 30/30 | 0.05866 / 0.05866 |
| N=3,000, S2 foundation control | 30/30 | 0.19964 / 0.19964 |

*Check 2 — final S vs ODE.* Reference = I(0)=10/N; relative error, gap in SEMs.

| case | N (seeds) | mean final S ± SEM | ODE | rel. error | gap | verdict |
|---|---|---|---|---|---|---|
| (a) S1, all precautions | 100,000 (10/10) | 0.41496 ± 0.00162 | 0.41708 | 0.507% | −1.31 | **PASS** |
| (b) S1, 50% home | 100,000 (10/10) | 0.70674 ± 0.00143 | 0.70840 | 0.235% | −1.16 | **PASS** |
| (b) vs stated β×0.5 | 100,000 (10/10) | 0.70674 | 0.41708 | 69.45% | +202.08 | FAIL, as predicted (D15) |
| (c) S2, all precautions | 100,000 (10/10) | 0.98999 ± 0.00528 | 0.99062 | 0.064% | −0.12 | report-only |
| (a) | 3,000 (30/30) | 0.40774 ± 0.00603 | 0.41351 | 1.394% | −0.96 | report-only |
| (b) | 3,000 (30/30) | 0.70931 ± 0.01071 | 0.70241 | 0.982% | +0.64 | report-only |
| (b) vs stated β×0.5 | 3,000 (30/30) | 0.70931 | 0.41351 | 71.53% | +27.61 | report-only |
| (c) | 3,000 (30/30) | 0.95254 ± 0.00978 | 0.92082 | 3.445% | +3.25 | report-only |

(c) attack-rate relative error vs the 10/N reference: 6.8% (N=100,000), 40.1% (N=3,000). With
Test 1's I(0)=10⁻⁶ reference the (c) final-S errors are 0.990% (−1.87 SEM) and 4.738%. Runs with
E+I > 0 at the last day: 0 in every Check 2 config; runs with zero incidence: 0 in every config.
Mean peak I: (a) 4,847.4 / 163.3, (b) 2,433.7 / 89.6, (c) 40.5 / 16.2 (N=100,000 / N=3,000).

*Ceiling numbers, N=3,000, 600 d, 30/30 seeds vs own AlwaysNormal control (same seeds).* M3
defined on 30/30 runs in every arm and control.

| | (a) S1 all precautions | (b) S1 50% home | (c) S2 all precautions |
|---|---|---|---|
| M3 arm / control (d) | 76.9 ± 2.2 / 23.2 ± 0.2 | 74.4 ± 2.9 / 23.2 ± 0.2 | 60.4 ± 7.8 / 42.6 ± 0.6 |
| stretch, ratio of means [95% CI] | ×3.32 [3.13, 3.52] | ×3.21 [2.96, 3.49] | ×1.42 [1.06, 1.78] |
| median per-seed ratio | ×3.19 | ×3.20 | ×1.24 |
| share of runs > ×1.5 | 30/30 | 30/30 | 12/30 |
| arm M3 median / max (d) | 74 / 110 | 72 / 105 | 55.5 / 200 |
| peak I arm / control | 163.3 / 681.1 | 89.6 / 681.1 | 16.2 / 358.9 |
| peak I reduction (paired) | 76.0%, −517.8 ± 8.1 | 86.8%, −591.5 ± 7.6 | 95.5%, −342.7 ± 5.9 |
| final S arm / control | 0.4077 / 0.0587 | 0.7093 / 0.0587 | 0.9525 / 0.1996 |
| final S increase (paired) | +0.3491 ± 0.0063 | +0.6507 ± 0.0106 | +0.7529 ± 0.0097 |
| M1 waves arm / control | 1.10 / 1.00 (1 wave 27, 2 waves 3) | 1.17 / 1.00 (25 / 5) | 1.33 / 1.00 (1: 21, 2: 8, 3: 1) |
| runs with E+I > 0 at day 600, arm / control (A35) | 0/30 / 0/30 | 0/30 / 0/30 | 0/30 / 0/30 |
| arm last active day, median / max | 188.5 / 254 | 168 / 237 | 80.5 / 300 |

*Check 3 — PASS.* CBFArm1 in the shared world vs `run_cbf_behaviour`, foundation, 600 d:
bit-identical daily S, prevalence, incidence and deaths on **30/30 seeds in S1, S2 and S3, for
the arm and for the β_B=0 control**. Paired differences in final S and peak I: 0 (n=30) in all
three. Stretch (shared world, ratio of means [95% CI]; median per-seed; share > ×1.5): S1
×1.079 [1.018, 1.158], ×1.000, 2/30; S2 ×1.239 [0.962, 1.704], ×0.964, 4/30; S3 ×1.020
[0.987, 1.057], ×0.980, 0/30 — identical to C30. 0/30 runs active at day 600 in every config.

*Agent-days, arm 1 in the shared world, mean per run (n=30):* never_ill (S+E) vs recovered.
Over 600 d: S1 335,047 vs 1,434,275; S2 823,047 vs 956,174; S3 273,887 vs 1,494,296. Up to the
last day with E+I > 0: S1 117,535 vs 151,345; S2 279,612 vs 152,521; S3 108,436 vs 156,629.

*Predictions vs outcome:*
- Check 1 "identical" (Max): as predicted.
- Check 2 "(a) and (b) pass" (Max): as predicted, (b) against the corrected reference. (b) vs
  β×0.5 "fails by ~70%" (Claude Code): 69.45% at N=100,000.
- "(a) at N=3,000 S1: stretch ×2–4, 1 wave, no plateau" (Max) / "×3–4, 1 wave" (Claude Code):
  ×3.32 [3.13, 3.52]; 1 wave on 27/30 runs, 2 on 3/30. Plateau is not measured by a metric.
- "(c): very slow, possibly not finished by day 600" (Max) / "mostly small outbreaks ending well
  before day 600, 0–4 of 30 still active" (Claude Code): 0/30 active at day 600; median last
  active day 80.5, max 300; (c) is not TRUNCATED under A35.
- "(c) at N=100,000 passes the 1% final-S mark" (Claude Code; mark later made report-only):
  0.064%.
- "(a)/(b) at N=3,000 below their ODE by a few percent" (Claude Code): (a) 1.39% below; **(b)
  0.98% above — not as predicted.**
- Check 3 "pass, bit-identical if the RNG order matches" (Max): bit-identical, as predicted.

**C32 — Arm-2 call count under A38/A42 (only never-ill, alive agents decide), p = 0.3/day.
[Measured facts only.]** `experiments/step4_arm2_call_count.py`, `results/step4/arm2_call_count.{json,log}`.
N=3,000, 600 d, foundation, seeds 0–29, S1/S2/S3; 180/180 runs; wall 25 s. Arm 2's own epidemic
is not known yet, so two reference epidemics are used: the no-behaviour control (AlwaysNormal)
and arm 1 (CBFArm1), both in `run_shared_world`. Deciders on day t = S + E at the start of day t.
Expected calls = 0.3 × deciding agent-days. "With E19" counts day t only while E + I > 0 at the
start of day t. Upper bound if all 3,000 agents decided every day: 540,000 calls per run.

| reference | scenario | calls per run, no E19: mean (SD, min–max) | calls per run, with E19: mean (SD, min–max) | days counted with E19, mean (min–max) |
|---|---|---|---|---|
| control | S1 | 56,510 (3,711; 49,746–64,094) | 29,868 (1,876; 26,476–33,130) | 95.3 (81–134) |
| control | S2 | 142,666 (8,023; 120,932–157,171) | 59,895 (4,903; 51,308–72,912) | 139.3 (113–171) |
| control | S3 | 56,510 (3,711; 49,746–64,094) | 29,868 (1,876; 26,476–33,130) | 95.3 (81–134) |
| arm 1 | S1 | 101,281 (26,630; 60,394–165,146) | 36,157 (6,667; 27,886–53,150) | 96.3 (77–132) |
| arm 1 | S2 | 247,444 (50,683; 183,820–383,873) | 84,781 (41,636; 57,032–277,131) | 149.2 (107–402) |
| arm 1 | S3 | 82,965 (19,882; 54,542–135,085) | 33,428 (4,428; 27,347–42,578) | 95.3 (82–127) |

n = 30 per row. S1 and S3 controls are identical (same infections on the same seeds, as in C27).

Totals:

| reference | S1+S2+S3, one run each (sum of means), no E19 / with E19 | S1+S2+S3, 30 seeds each (90 runs), no E19 / with E19 |
|---|---|---|
| control | 255,685 / 119,632 | 7,670,550 / 3,588,962 |
| arm 1 | 431,690 / 154,366 | 12,950,705 / 4,630,971 |

For comparison, E1's 1.62M (3,000 agents × 600 d × 3 scenarios × 0.3) is the all-agents count
for ONE run per scenario.

**C33 — Arm-2 prompt size and token ESTIMATE per call (draft v1 template). [Measured facts;
token counts are estimates, not tokenizer output.]** `experiments/step4_prompt_tokens.py`,
`results/step4/prompt_tokens.{json,log}`, template `prompts/DRAFT_arm2_arm3.md`. No LLM was
called and no model is chosen, so no model tokenizer was used (none is installed). Rendered
from a real run (arm 1, S1, seed 0) for one agent aged 60–69 at days 0, 5, 20, 45, 100, 300:
1,010–1,032 characters, 196–199 words per prompt (6/6 renders). Estimates: characters / 4 →
252–258 tokens; words × 1.33 → 261–265 tokens. Reply "A=20, B=60, C=20" is 16 characters;
10–15 output tokens is assumed (the two rules of thumb undercount short digit strings).

Totals for 90 runs (S1+S2+S3 × 30 seeds) with E19 (A55), using C32's call counts and a ±25%
tokenizer band around ~260 input tokens (200–330), output 10–15 tokens:

| reference epidemic (C32) | calls | input tokens (200 / 260 / 330 per call) | output tokens (10 / 15 per call) |
|---|---|---|---|
| no-behaviour control | 3,588,962 | 718M / 933M / 1,184M | 35.9M / 53.8M |
| arm 1 | 4,630,971 | 926M / 1,204M / 1,528M | 46.3M / 69.5M |

Not included: retries after invalid replies (A61; each retry repeats a full call), and arm 3
(one instruction of ~3,290 characters / 544 words, ~720–820 input tokens, per rule; 5 rules
plus logged regenerations, A51).

*Addendum (10 Oct 2026, after A63).* Anthropic's Models overview states that on the current
tokenizer (introduced with Claude Opus 4.7) 1M tokens ≈ 2.5M Unicode characters ≈ 555k words,
i.e. ~2.5 characters or ~0.555 words per token. Applied to the 1,010–1,032-character /
196–199-word prompt this gives ~400–410 or ~355–360 input tokens per call — higher than the
~255–265 above. Whether Claude Haiku 5.5 uses that tokenizer is not stated on the pages read.
**The per-call input count is therefore uncertain between ~255 and ~410 tokens** until it is
measured with the token-counting endpoint (an API call, not yet made). Thinking tokens (A63
flag) are not included in any figure. At A63's prices, 90 runs with E19: input $72–$187
(3.59M–4.63M calls × 200–404 tokens × $0.10/M), output $18–$35 (10–15 tokens × $0.50/M),
before thinking and retries.

*Measured (10 Oct 2026, token-counting endpoint `messages.count_tokens`, model
`claude-haiku-5-5`, `thinking: {"type": "disabled"}`; no generation; `results/step4/pilot_token_counts.{json,log}`).*
The 10 C34 pilot prompts (1,013–1,032 characters, 198–202 words): **356–366 input tokens each
(10/10)**; the typical case (rising deaths, aged 70–79) is **361**. The estimates above were
low: characters / 4 and words × 1.33 gave ~255–265; the docs' ~2.5 characters per token gave
~400–410. At 361 tokens and A63's price, input for 90 runs with E19 is $129.6 (control
reference, 3,588,962 calls) to $167.2 (arm-1 reference, 4,630,971 calls); output per call is
measured in C34.

**C34 — Arm-2 prompt pilot (E6; criteria A62; settings A65). PRE-REGISTRATION, written before
any generation call.** `experiments/step4_pilot.py`; situations
`results/step4/pilot_situations.{json,log}`. Template: `prompts/DRAFT_arm2_arm3.md` section 1,
read verbatim by the script and asserted equal to the renderer's.

*Situations (10), all from ONE run:* arm 1 (`CBFArm1`) in `run_shared_world`, S1, seed 0,
foundation (N=3,000, per-agent f_D, window 28, detection 0.7). Death signal values are the run's
`awareness_signal` (28-day mean of reported deaths), `deaths_28day_mean_7d_ago` = the signal 7
days earlier (0 before day 7), `deaths_cumulative` = reported deaths before the day,
`social_norm` = the run's start-of-day value. Day rules (fixed before looking at any reply):
before = day 0; early rising = first day the signal reaches 25% of its peak; peak = first day
of the maximum (signal rounded to 6 decimals); rising/falling = first day on each side of the
peak at the matched level, chosen among levels taken on both sides as the one nearest 50% of
the peak (ties → lower). Peak signal 0.35; matched level 0.15.

| id | day | deaths_28day_mean | …_7d_ago | deaths_cumulative | social_norm | rendered deaths (past 4 wk / up to a week ago / total) | rendered "normally" |
|---|---|---|---|---|---|---|---|
| before | 0 | 0.0000 | 0.0000 | 0.0 | 0.9967 | 0 / 0 / 0 | 100% |
| early_rising | 30 | 0.1000 | 0.0304 | 2.8 | 0.5767 | 3 / 1 / 3 | 58% |
| rising | 34 | 0.1500 | 0.0519 | 4.2 | 0.5817 | 4 / 1 / 4 | 58% |
| peak | 53 | 0.3500 | 0.2250 | 11.2 | 0.8057 | 10 / 6 / 11 | 81% |
| falling | 89 | 0.1500 | 0.2000 | 17.5 | 0.8637 | 4 / 6 / 18 | 86% |

Each row is asked for a **young** agent (age_band 2, 20–24; vulnerability 0.000309 → "about 3 in
10,000") and an **old** agent (age_band 8, 70–79; vulnerability 0.0428 → "about 4 in 100").
Identical in all 10 situations: occupation_flex 0.4101759 (renders 4), response_efficacy
0.7954036 (renders 8) — both are the real values of the first band-2 agent of the frozen
population (index 667); **for the old agent this occupation_flex departs from band 8's fixed
1.0**, because no band-2 agent has occupation_flex ≥ 0.95 and the pair must be identical;
current_action "normal" (kept constant so phases differ only in the death/social fields);
population 3,000. Note, measured: social_norm is LOWER while deaths are rising (58%) than at
the peak or falling (81–86%), because CBF's (S_normal + R)/N excludes the many E and I agents
mid-epidemic.

*Calls:* each situation 3× with thinking OFF (A65) and 1× with thinking ON (`{"type":
"adaptive"}`, comparison only). Reply rule A64; retries A61 (up to 2). Cost guard: stop if
spending passes $2. Projected worst case (every decision retried twice; every reply at
`max_tokens`): $0.29; expected well under $0.01.

*Scoring (fixed before calling).* Caution c = P(stay_home) + P(precautions) = 1 − P(normal), per
valid reply; per situation the mean over its valid thinking-OFF replies (denominator reported;
fallback replies have no probabilities and are excluded). Strict comparisons of means, no
tolerance; "at least as" passes on ties.
- (i) PASS if c(peak) > c(before) for both the young and the old agent.
- (ii) PASS if c(old) ≥ c(young) in all 5 phases.
- (iii) PASS if c(rising) ≥ c(falling) for both agents (same 4-week death total, 4).
- (iv) PASS if all 30 thinking-OFF replies are valid at the first attempt.
Also reported, not scored: P(stay_home) for the same comparisons; the spread (SD) of the 3
repeats; thinking ON vs OFF.

*Predictions (Claude Code), [Speculation]:* (i) PASS, high confidence. (ii) PASS, medium — the
"before" pair may tie or reverse by noise. (iii) uncertain (~60% PASS, low confidence): the
rising situation has the rising trend (4 vs 1) and fewer people "going about normally" (58% vs
86%), but the falling one has more total deaths (18 vs 4). (iv) PASS, high confidence. Thinking
ON: more output tokens per call (tens to hundreds of thinking tokens), similar probabilities.

**C34 results. [Measured facts only.]** Run 10 Oct 2026, `python experiments/step4_pilot.py
--run` then `--score`; `results/step4/pilot_replies.json`, `pilot_scores.{json,log}`,
`pilot_run.log`. Served model `claude-haiku-5-5` on all 40 calls (service tier standard,
inference_geo global). Wall 55 s. **Total cost $0.00278** (thinking OFF $0.00128, ON $0.00150).

*Validity:* 40/40 decisions valid at the first attempt (30/30 OFF, 10/10 ON); 0 retries; 0
fallbacks; every stop_reason `end_turn`; every reply summed to exactly 100.

*Tokens per call:* OFF: input 356–366 (equal to the C33 counts for the same prompt), output 13
(`output_tokens_details.thinking_tokens` = 0), no thinking block. ON: input 358–368 (+2), output
175–286, of which thinking 162–273 (sum 2,140 over 10 calls) and answer 13; one thinking block
per reply. Cost per call: OFF $0.0000427 (mean), ON $0.000150 (mean), 3.5×.

*Replies, thinking OFF (A=stay home, B=precautions, C=normal), three repeats; caution c = 1 −
P(normal):*

| situation | repeat 1 | repeat 2 | repeat 3 | mean c (SD) | mean P(stay home) | thinking ON (1 reply) | ON c |
|---|---|---|---|---|---|---|---|
| before, young | 10/60/30 | 10/50/40 | 10/60/30 | 0.667 (0.058) | 0.100 | 5/30/65 | 0.350 |
| before, old | 20/60/20 | 15/60/25 | 20/55/25 | 0.767 (0.029) | 0.183 | 12/44/44 | 0.560 |
| early rising, young | 10/45/45 | 10/45/45 | 10/45/45 | 0.550 (0.000) | 0.100 | 15/45/40 | 0.600 |
| early rising, old | 15/50/35 | 20/50/30 | 20/50/30 | 0.683 (0.029) | 0.183 | 8/50/42 | 0.580 |
| rising, young | 10/50/40 | 10/45/45 | 10/45/45 | 0.567 (0.029) | 0.100 | 5/30/65 | 0.350 |
| rising, old | 18/52/30 | 12/48/40 | 18/52/30 | 0.667 (0.058) | 0.160 | 12/38/50 | 0.500 |
| peak, young | 10/60/30 | 10/55/35 | 12/50/38 | 0.657 (0.040) | 0.107 | 12/38/50 | 0.500 |
| peak, old | 20/55/25 | 20/55/25 | 20/55/25 | 0.750 (0.000) | 0.200 | 8/44/48 | 0.520 |
| falling, young | 10/50/40 | 10/50/40 | 10/50/40 | 0.600 (0.000) | 0.100 | 10/45/45 | 0.550 |
| falling, old | 25/50/25 | 25/50/25 | 20/55/25 | 0.750 (0.000) | 0.233 | 10/35/55 | 0.450 |

n = 3/3 valid OFF replies per situation; n = 1/1 ON.

*Criteria (thinking OFF, pre-registered scoring):*
- **(i) FAIL.** c(peak) < c(before) for both agents: young 0.657 vs 0.667; old 0.750 vs 0.767.
- **(ii) PASS.** c(old) > c(young) in 5/5 phases (differences +0.100, +0.133, +0.100, +0.093,
  +0.150). P(stay home) old ≥ young in 5/5 as well.
- **(iii) FAIL.** c(rising) < c(falling) for both agents: young 0.567 vs 0.600; old 0.667 vs
  0.750.
- **(iv) PASS.** 30/30 OFF replies valid at the first attempt.

Range of mean c over the 10 OFF situations: 0.550–0.767; the young agent's is 0.550–0.667, the
old agent's 0.667–0.767. Repeat-to-repeat SD of c: 0.000–0.058.

*Thinking ON vs OFF (information only, 1 ON reply per situation):* ON c is lower than OFF mean
c in 9/10 situations (early rising, young: 0.600 vs 0.550 is the exception); mean ON − OFF
difference −0.170. Applying the same criteria to the single ON replies: (i) peak > before for
the young agent (0.500 vs 0.350), not for the old (0.520 vs 0.560); (ii) old ≥ young in 3/5
phases; (iii) rising ≥ falling for the old agent (0.500 vs 0.450), not the young (0.350 vs 0.550).

*Predictions vs outcome:* (i) "PASS, high confidence" — **FAIL**. (ii) "PASS, medium" — PASS.
(iii) "uncertain, ~60% PASS" — FAIL. (iv) "PASS, high confidence" — PASS. Thinking ON "more
output tokens (tens to hundreds), similar probabilities" — 162–273 thinking tokens; caution
lower by 0.170 on average.

*Cost at measured per-call figures (computed):* arm 2 with thinking OFF at $0.0000427 per call
× C32's E19 call counts → $153 (control reference) to $198 (arm-1 reference) for 90 runs,
before retries. The prompt wording was NOT changed.

**C35 — Arm-2 prompt pilot v2: controlled situations, one field changed at a time.
PRE-REGISTRATION, written before any generation call.** [Design: planning chat (Max), 10 Oct
2026.] `experiments/step4_pilot_v2.py`; situations `results/step4/pilot_v2_situations.{json,log}`.
Settings A65 with thinking OFF only; template `prompts/DRAFT_arm2_arm3.md` unchanged (asserted
equal to the renderer's); reply rule A64, retries A61. 3 repeats per situation. Cost guard: stop
if spending passes $2; projected worst case (every decision retried twice, every reply at
`max_tokens` 1024) $0.15; expected about $0.004 (C34's $0.0000427 per call × 90).

*Base situation (constructed, not from a run):* day 60; social_norm 0.85 (renders "85%"); flat
deaths: deaths_28day_mean_7d_ago = deaths_28day_mean (both = 4-week total / 28, so both
rendered 4-week totals are equal); deaths_cumulative = 4-week total + 5; current_action normal;
population 3,000. Agents as in C34: young = age_band 2, vulnerability 0.000309 ("about 3 in
10,000"); old = age_band 8, vulnerability 0.0428 ("about 4 in 100"); both occupation_flex
0.4101759 (renders 4) and response_efficacy 0.7954036 (renders 8).

*Situations (each × young and × old = 30 situations, 90 decisions). Rendered death lines: past
four weeks / four weeks up to a week ago / total; rendered "normally" %:*

| test | id | 4-week total | 4 weeks up to a week ago | total so far | normally |
|---|---|---|---|---|---|
| D | D0, D1, D3, D6, D12, D25, D50, D100 | 0, 1, 3, 6, 12, 25, 50, 100 | same as 4-week total | 5, 6, 8, 11, 17, 30, 55, 105 | 85% |
| T | T4, T12, T25 | 12 | 4, 12, 25 | 17 | 85% |
| N | N50, N70, N90 | 12 | 12 | 17 | 50%, 70%, 90% |
| supplementary | T25c | 12 | 25 | **30** | 85% |

Notes, fixed before calling: (1) T12 is the identical prompt to D12 and is called separately
(so that prompt gets 6 calls); N's base value (85%) is D12. (2) **T25 is an impossible
combination**: 25 deaths in the four weeks up to a week ago but only 17 in total. It is run as
specified. T25c is added (not part of Test T, changes two fields relative to T12) with the
total raised to 25 + 5 = 30, so the falling-trend comparison can be read without the
contradiction. (3) The renderer prints "1 people" for D1 (template unchanged).

*Reported per situation:* caution c = 1 − P(normal) and P(stay home), mean and SD over the
valid replies (denominator reported). No pass/fail criteria were set for v2.

*Predictions (Claude Code), [Speculation]:*
- D: c(D100) > c(D0) by at least 0.10 for both agents (medium confidence). c strictly increasing
  over all 8 levels: unlikely for either agent (low confidence; C34's repeat SD was up to 0.058
  and its range only 0.55–0.77). P(stay home) at D100 > at D0 for both (medium).
- D, low end: c(D0) is not below about 0.5 for either agent — the model is cautious even with
  no deaths, as C34's day-0 situation was (0.67/0.77) (medium).
- T: c(T4) > c(T25) for both agents (low confidence, ~55%; C34 showed the opposite direction for
  rising vs falling, but those situations also differed in total and norm).
- N: c(N50) > c(N90) for both agents, i.e. fewer people "going about normally" → more caution
  (low confidence, ~60%).
- Age: c(old) > c(young) in at least 13/15 matched pairs (medium-high).
- Validity: 90/90 valid at the first attempt (high).

**C35 results. [Measured facts only.]** Run 10 Oct 2026, `python experiments/step4_pilot_v2.py
--run` then `--score`; `results/step4/pilot_v2_replies.json`, `pilot_v2_scores.{json,log}`,
`pilot_v2_run.log`. Model `claude-haiku-5-5`, thinking OFF. Wall 99 s. **Total cost $0.00383.**
90/90 decisions valid at the first attempt; 0 retries; 0 fallbacks. Input 358–363 tokens, output
13 tokens on every call. Prompt wording unchanged.

*Per situation (A/B/C = stay home / precautions / normal; n = 3/3 valid for every situation;
mean (SD) over the 3 replies):*

| id | young replies | young c | young P(stay) | old replies | old c | old P(stay) |
|---|---|---|---|---|---|---|
| D0 | 10/55/35 10/60/30 10/60/30 | 0.683 (0.029) | 0.100 (0.000) | 20/55/25 15/60/25 20/50/30 | 0.733 (0.029) | 0.183 (0.029) |
| D1 | 10/55/35 10/60/30 10/50/40 | 0.650 (0.050) | 0.100 (0.000) | 20/50/30 20/55/25 20/50/30 | 0.717 (0.029) | 0.200 (0.000) |
| D3 | 10/60/30 10/50/40 10/60/30 | 0.667 (0.058) | 0.100 (0.000) | 25/55/20 25/50/25 25/50/25 | 0.767 (0.029) | 0.250 (0.000) |
| D6 | 10/50/40 10/45/45 10/45/45 | 0.567 (0.029) | 0.100 (0.000) | 20/55/25 25/50/25 20/55/25 | 0.750 (0.000) | 0.217 (0.029) |
| D12 | 10/50/40 10/55/35 10/50/40 | 0.617 (0.029) | 0.100 (0.000) | 20/55/25 25/55/20 20/50/30 | 0.750 (0.050) | 0.217 (0.029) |
| D25 | 10/60/30 10/50/40 10/55/35 | 0.650 (0.050) | 0.100 (0.000) | 20/55/25 15/55/30 20/50/30 | 0.717 (0.029) | 0.183 (0.029) |
| D50 | 10/60/30 10/60/30 10/60/30 | 0.700 (0.000) | 0.100 (0.000) | 20/60/20 25/50/25 20/55/25 | 0.767 (0.029) | 0.217 (0.029) |
| D100 | 10/60/30 10/60/30 15/50/35 | 0.683 (0.029) | 0.117 (0.029) | 25/55/20 20/55/25 25/45/30 | 0.750 (0.050) | 0.233 (0.029) |
| T4 | 10/60/30 10/45/45 15/45/40 | 0.617 (0.076) | 0.117 (0.029) | 25/55/20 20/60/20 25/55/20 | 0.800 (0.000) | 0.233 (0.029) |
| T12 | 10/50/40 10/45/45 10/55/35 | 0.600 (0.050) | 0.100 (0.000) | 20/55/25 20/50/30 20/55/25 | 0.733 (0.029) | 0.200 (0.000) |
| T25 | 10/50/40 10/45/45 12/58/30 | 0.617 (0.076) | 0.107 (0.012) | 30/50/20 25/50/25 25/50/25 | 0.767 (0.029) | 0.267 (0.029) |
| N50 | 10/45/45 10/55/35 12/48/40 | 0.600 (0.050) | 0.107 (0.012) | 20/55/25 20/55/25 25/50/25 | 0.750 (0.000) | 0.217 (0.029) |
| N70 | 10/50/40 10/55/35 10/60/30 | 0.650 (0.050) | 0.100 (0.000) | 20/55/25 20/50/30 25/50/25 | 0.733 (0.029) | 0.217 (0.029) |
| N90 | 15/60/25 15/50/35 15/50/35 | 0.683 (0.058) | 0.150 (0.000) | 25/50/25 25/50/25 25/55/20 | 0.767 (0.029) | 0.250 (0.000) |
| T25c | 10/45/45 15/50/35 15/55/30 | 0.633 (0.076) | 0.133 (0.029) | 30/50/20 25/50/25 30/50/20 | 0.783 (0.029) | 0.283 (0.029) |

*Summaries (computed from the table):*
- D (8 levels, 0 → 100 deaths in four weeks): young c 0.567–0.700, old c 0.717–0.767. c(D100) −
  c(D0): young 0.000, old +0.017. Spearman rank correlation of mean c with the death level:
  young 0.18, old 0.32 (n = 8 levels each). P(stay home): young 0.100 at every level except D100
  (0.117); old 0.183–0.250.
- T (week-ago total 4 / 12 / 25 at a 4-week total of 12): young c 0.617 / 0.600 / 0.617; old
  0.800 / 0.733 / 0.767. T25c (total 30): young 0.633, old 0.783.
- N (50% / 70% / 90% "normally"; 85% is D12): young c 0.600 / 0.650 / 0.683 (D12 0.617); old
  0.750 / 0.733 / 0.767 (D12 0.750). P(stay home) young 0.107 / 0.100 / 0.150; old 0.217 /
  0.217 / 0.250.
- D12 and T12 are the same prompt: young 0.617 and 0.600, old 0.750 and 0.733.
- Age: c(old) > c(young) in 15/15 matched situations; difference +0.050 to +0.183, mean +0.111.
- Repeat SD of c: 0.000–0.076 (young), 0.000–0.050 (old).

*Predictions vs outcome:* c(D100) − c(D0) ≥ 0.10 for both — **wrong** (0.000, +0.017). c not
strictly increasing over D — correct (neither agent). P(stay home) D100 > D0 for both — correct
(0.117 vs 0.100; 0.233 vs 0.183). c(D0) ≥ about 0.5 — correct (0.683, 0.733). c(T4) > c(T25) for
both — **wrong** for the young agent (0.617 = 0.617), right for the old (0.800 vs 0.767). c(N50) >
c(N90) for both — **wrong** for both (young 0.600 vs 0.683, old 0.750 vs 0.767). Old > young in
≥ 13/15 — correct (15/15). 90/90 valid first — correct.

**C36 — Arm-2 prompt pilot v3: format and model DIAGNOSTIC. PRE-REGISTRATION, written before
any generation call.** [Design: planning chat (Max), 10 Oct 2026.] Diagnostic only: the frozen
template (`prompts/DRAFT_arm2_arm3.md`), the model decision (A63) and A65 are NOT changed.
`experiments/step4_pilot_v3.py`; situations `results/step4/pilot_v3_situations.{json,log}`.

*Situations (10):* C35's base situation (day 60; social_norm 0.85; flat deaths; deaths_cumulative
= 4-week total + 5; current_action normal; population 3,000) at Test D levels **0, 3, 12, 50,
100** deaths in four weeks (C35's D0, D3, D12, D50, D100), each for the young (band 2) and old
(band 8) agent of C34/C35 (occupation_flex 0.4101759, response_efficacy 0.7954036). The
percentage prompts are byte-identical to C35's.

*Versions:*
| version | model | answer format | calls per situation | decisions |
|---|---|---|---|---|
| V1 | `claude-haiku-5-5` | one letter | 10 | 100 |
| V2 | `claude-sonnet-5-5` | percentages (frozen template) | 3 | 30 |
| V3 | `claude-sonnet-5-5` | one letter | 10 | 100 |

*Letter prompt — exact wording:* the rendered percentage prompt with only its last two lines
("Give the probability, in percent, that you choose each option. Use whole numbers that add up
to 100. Reply in exactly this form and nothing else:" / "A=<number>, B=<number>, C=<number>")
replaced by the single line **"Answer with a single letter: A, B or C."** Everything above it is
unchanged. Letter reply rule (fixed before calling): valid if the reply, stripped, is one of A,
B, C, optionally followed by "." or ")" (regex `^\s*([ABC])\s*[.)]?\s*$`); otherwise invalid
and retried as A61 (up to 2). Percentage replies: A64 as before.

*Model check (10 Oct 2026, official docs, platform.claude.com "Models overview", "Claude Sonnet
5.5", "Pricing", "What's new in Claude Sonnet 5.5"):* Claude Sonnet 5.5, Claude API ID and alias
`claude-sonnet-5-5` (pinned snapshot; released 28 Sep 2026; retirement not sooner than 28 Sep
2027). Price $2 / M input, $10 / M output tokens (Batch 50% off). Default effort `high` (Haiku
5.5: `medium`). Non-default temperature / top_p / top_k return 400. **On Claude Sonnet 5.5
`thinking: {"type": "disabled"}` returns 400; its thinking-off setting is `thinking: {"type":
"between_tools"}`** ("the lowest thinking setting on this model"; accepted at low/medium/high
effort; "If your requests don't use tools, the response contains only text, as with `disabled`
on Claude Sonnet 5").

*Request settings:* Haiku as A65 (`thinking: {"type": "disabled"}`). Sonnet: `thinking:
{"type": "between_tools"}`. Both: effort, temperature, top_p, top_k NOT sent (API defaults, as
A65), so **the two models also differ in default effort (Haiku medium, Sonnet high)** — a
recorded confound of this diagnostic. max_tokens 1024. No system prompt.

*Tokens (count_tokens endpoint, no generation; `results/step4/pilot_v3_token_counts.log`):*
percentage prompts 358–363, letter prompts 309–314, identical on both models.
*Cost:* projected about $0.09 (V1 ~$0.003, V2 ~$0.026, V3 ~$0.065). Guard: stop if spending
passes $2.

*Reported:* per version and situation, caution = share of replies not choosing C (letter) or
mean 1 − P(normal) (percentages), and stay-home share (letter: share choosing A; percentages:
mean P(stay home)); counts of A/B/C; SD for percentages; validity, retries, tokens, cost. No
pass/fail criteria.

*Predictions (Claude Code), [Speculation]:*
- V1 (Haiku, letter): B is the most frequent letter in every situation; C (normal) is chosen in
  ≤ 10% of the 100 replies, so letter caution is ≥ 0.9 nearly everywhere and shows no death
  trend (medium). A is chosen more by the old agent than the young (medium-low).
- V2 (Sonnet, percentages): more sensitive to deaths than Haiku: c(D100) − c(D0) ≥ 0.10 for both
  agents (low confidence, ~55%). Young agent's c at D0 lower than Haiku's 0.683 (low).
- V3 (Sonnet, letter): the young agent picks C in at least half of the D0 replies (low, ~50%);
  the old agent picks C in fewer than 3/10 at every level (medium).
- Validity: V1 100/100 valid first (medium-high); V2 30/30 (high); V3 ≥ 95/100 (medium).

**C36 results. [Measured facts only.]** Run 10 Oct 2026, `python experiments/step4_pilot_v3.py
--run` then `--score`; `results/step4/pilot_v3_replies.json`, `pilot_v3_scores.{json,log}`,
`pilot_v3_run.log`. 230/230 decisions completed; wall 255 s. Served models as requested on every
call; every stop_reason `end_turn`; 0 thinking blocks in any reply. **Cost: V1 $0.00327, V2
$0.02913, V3 $0.06982; total $0.10221.**

*V1 — Haiku, one letter (10 per situation):* **B in 100/100 replies** (all 10 situations
A/B/C = 0/10/0). Caution share 1.000 and stay-home share 0.000 in every situation. 100/100 valid
first; 0 retries; output 3 tokens per call; input 309–314.

*V3 — Sonnet, one letter (10 per situation):* **B in 100/100 final replies** (all 10
situations 0/10/0). Caution share 1.000, stay-home share 0.000 everywhere. 98/100 valid at the
first attempt; 2 retries (both D100_young; both invalid replies were a paragraph of reasoning
ending in "B" — one says "the data are somewhat inconsistent (100 deaths in the past four weeks
but 105 total…)"); 0 fallbacks. Output 3 tokens on valid replies, up to 165 on the invalid ones.

*V2 — Sonnet, percentages (3 per situation; A/B/C; n = 3/3 valid final replies each):*

| level | young replies | young c (SD) | young P(stay) | old replies | old c (SD) | old P(stay) |
|---|---|---|---|---|---|---|
| D0 | 5/40/55 5/40/55 5/35/60 | 0.433 (0.029) | 0.050 | 10/55/35 ×3 | 0.650 (0.000) | 0.100 |
| D3 | 5/40/55 5/35/60 5/35/60 | 0.417 (0.029) | 0.050 | 12/58/30 10/60/30 15/60/25 | 0.717 (0.029) | 0.123 |
| D12 | 10/45/45 10/40/50 10/40/50 | 0.517 (0.029) | 0.100 | 20/55/25 15/55/30 20/55/25 | 0.733 (0.029) | 0.183 |
| D50 | 10/45/45 10/40/50 10/45/45 | 0.533 (0.029) | 0.100 | 15/60/25 20/60/20 20/60/20 | 0.783 (0.029) | 0.183 |
| D100 | 10/40/50 10/45/45 10/35/55 | 0.500 (0.050) | 0.100 | 25/50/25 20/55/25 20/50/30 | 0.733 (0.029) | 0.217 |

29/30 valid at the first attempt; 1 retry (D50_old: a paragraph of reasoning, which says the
death figures "are inconsistent", ending in "A=20, B=65, C=15"; the retry was valid); 0
fallbacks. Output 13 tokens on valid replies (288 on the invalid one); input 358–363.
c(D100) − c(D0): young +0.067, old +0.083. Range of c: young 0.417–0.533, old 0.650–0.783.
P(stay home) does not decrease from one level to the next for either agent (young 0.050 →
0.100; old 0.100 → 0.217).

*Same prompts on Haiku (C35, percentages, 3 repeats), for comparison:* young c 0.683 / 0.667 /
0.617 / 0.700 / 0.683 at D0 / D3 / D12 / D50 / D100; old 0.733 / 0.767 / 0.750 / 0.767 / 0.750.
c(D100) − c(D0): young 0.000, old +0.017.

*Predictions vs outcome:* V1 B most frequent everywhere — correct (100/100). V1 C ≤ 10% —
correct (0/100). V1 A more for old than young — **wrong** (0 and 0). V2 c(D100) − c(D0) ≥ 0.10
for both — **wrong** (+0.067, +0.083). V2 young D0 c below Haiku's 0.683 — correct (0.433). V3
young picks C in ≥ half of D0 replies — **wrong** (0/10). V3 old picks C < 3/10 at every level —
correct (0/10 each). Validity: V1 100/100 — correct; V2 30/30 — **wrong** (29/30); V3 ≥ 95/100 —
correct (98/100).

**C37 — Arm-2 prompt pilot v4: three wordings on internally consistent situations; last prompt
round before the supervisor meeting. PRE-REGISTRATION, written before any generation call.**
[Design: planning chat (Max), 10 Oct 2026.] `experiments/step4_pilot_v4.py`; situations
`results/step4/pilot_v4_situations.{json,log}`. Model `claude-haiku-5-5`, settings A65 (thinking
`{"type": "disabled"}`; effort, temperature, top_p, top_k not sent; max_tokens 1024). 3 repeats per
situation and wording. Retries A61. The frozen template is NOT edited: W2 and W3 are built by
modifying the rendered W1 prompt at fixed anchors (asserted in code).

*Death-history construction rule (Claude Code's implementation of "internally consistent"):* day
60; deaths occur only in days 25–60 (none before day 25), in three segments with a constant
daily rate inside each: a = days 25–31, b = days 32–52, c = days 53–59. Then 4-week total now =
b + c, 4-week total up to a week ago = a + b, cumulative = a + b + c, so cumulative ≥ both
totals by construction.
- D (flat): constant rate X/28 per day from day 25 → a = c = X/4, b = 3X/4, cumulative 1.25X.
- T rising: a/b/c = 1/3/9 (daily rate 0.14, 0.14, 1.29; non-decreasing).
- T falling: a/b/c = 15/10/2 (daily rate 2.14, 0.48, 0.29; decreasing).

| id | a/b/c | 4 weeks now | 4 weeks up to a week ago | cumulative (rendered) |
|---|---|---|---|---|
| D0 | 0/0/0 | 0 | 0 | 0 |
| D3 | 0.75/2.25/0.75 | 3 | 3 | 3.75 (4) |
| D12 | 3/9/3 | 12 | 12 | 15 |
| D50 | 12.5/37.5/12.5 | 50 | 50 | 62.5 (63) |
| D100 | 25/75/25 | 100 | 100 | 125 |
| Trise | 1/3/9 | 12 | 4 | 13 |
| Tfall | 15/10/2 | 12 | 25 | 27 |

Each × young (band 2, "about 3 in 10,000") and old (band 8, "about 4 in 100"); both
occupation_flex 0.4101759 (renders 4), response_efficacy 0.7954036 (renders 8); social_norm 0.85;
current_action normal; population 3,000. 14 situations × 3 wordings × 3 = 126 decisions. Note:
Trise and Tfall necessarily differ in cumulative deaths (13 vs 27) as well as trend; D0 now says
0 deaths in total (C35's D0 said 5).

*Wordings (exact):*
- **W1:** the frozen template, unchanged.
- **W2:** W1 plus, on its own new line directly after the deaths paragraph (i.e. after "In total,
  … so far."), **"That is about 1 in every {k} people in your town in the past four weeks."**, k =
  3,000 / 4-week total rounded half-up, formatted with a thousands comma (D3 1,000; D12 / Trise /
  Tfall 250; D50 60; D100 30). Omitted when the 4-week total is 0 (D0 is then identical to W1).
  Placement is Claude Code's reading of "one line after the 4-week totals".
- **W3:** W1 with its last two lines (the answer instructions) replaced by **"On how many of the
  next 10 days will you A) stay at home, B) go out but take precautions, C) go out as normal? Give
  three whole numbers that add up to 10."** The option list above it is unchanged. Probabilities
  = numbers / 10. W3 reply rule (fixed before calling): three whole numbers, each optionally
  preceded by its letter and "=", ":" or ")", separated by commas, semicolons, slashes or spaces,
  nothing else (regex in `W3_RE`), summing to exactly 10; otherwise invalid and retried (A61).

*Tokens (count_tokens, no generation; `results/step4/pilot_v4_token_counts.log`):* W1 358–363,
W2 358–389, W3 346–351. Expected cost about $0.006; guard: stop if spending passes $2.

*Criteria — A62 (i)–(iii) as operationalised on these series (Claude Code; scoring as C34:
caution c = 1 − P(normal), mean over valid replies, strict comparison of means, "at least" passes
on ties):*
- (i) more caution at peak deaths than before: c(D100) > c(D0) for both agents.
- (ii) old at least as cautious as young: c(old) ≥ c(young) in all 7 D and T situations.
- (iii) rising at least as cautious as falling at the same 4-week total: c(Trise) ≥ c(Tfall) for
  both agents.
Validity (iv) is reported, not used in selection.

*Selection rule (Max, recorded before calling):* the wording passing the most of (i)–(iii) on the
D and T series wins; ties go to W1, then W2. **If no wording passes (i), report and STOP; no
further wordings are tried.**

*Predictions (Claude Code), [Speculation]:*
- W1: (i) FAIL (~60%; C35 gave young 0.683 vs 0.683), (ii) PASS (high), (iii) uncertain (~50%).
- W2: (i) PASS (~55%; the "1 in every 30 people" line makes the high-death level salient), (ii)
  PASS (high), (iii) ~50%.
- W3: (i) ~50%, (ii) PASS (medium-high), (iii) ~50%. Validity lower than W1/W2 because W3 does not
  say "and nothing else": at least one invalid first attempt in 42 (medium).
- W1 and W2: 42/42 valid at the first attempt (high).
- Winner: W2 (low confidence). Probability that no wording passes (i): ~35%.

**C37 results. [Measured facts only.]** Run 10 Oct 2026, `python experiments/step4_pilot_v4.py
--run` then `--score`; `results/step4/pilot_v4_replies.json`, `pilot_v4_scores.{json,log}`,
`pilot_v4_run.log`. Model `claude-haiku-5-5` on every call; wall 384 s. **Cost: W1 $0.00179, W2
$0.00187, W3 $0.02067; total $0.02433.**

*Per situation (A/B/C replies; caution c = 1 − P(normal) and P(stay home), mean (SD) over the
valid replies; n = 3/3 valid for every W1 and W2 situation):*

| id | W1 replies | W1 c | W1 P(stay) | W2 replies | W2 c | W2 P(stay) |
|---|---|---|---|---|---|---|
| D0 young | 10/60/30 10/60/30 10/50/40 | 0.667 (0.058) | 0.100 | 10/60/30 10/60/30 10/55/35 | 0.683 (0.029) | 0.100 |
| D3 young | 10/55/35 10/60/30 10/50/40 | 0.650 (0.050) | 0.100 | 12/58/30 10/60/30 10/60/30 | 0.700 (0.000) | 0.107 |
| D12 young | 10/60/30 10/50/40 10/60/30 | 0.667 (0.058) | 0.100 | 10/60/30 ×3 | 0.700 (0.000) | 0.100 |
| D50 young | 15/55/30 15/50/35 15/50/35 | 0.667 (0.029) | 0.150 | 10/60/30 ×3 | 0.700 (0.000) | 0.100 |
| D100 young | 15/55/30 15/60/25 10/60/30 | 0.717 (0.029) | 0.133 | 15/60/25 15/60/25 15/55/30 | 0.733 (0.029) | 0.150 |
| Trise young | 10/45/45 ×3 | 0.550 (0.000) | 0.100 | 10/55/35 10/60/30 10/55/35 | 0.667 (0.029) | 0.100 |
| Tfall young | 10/55/35 10/45/45 10/45/45 | 0.583 (0.058) | 0.100 | 15/50/35 15/55/30 10/60/30 | 0.683 (0.029) | 0.133 |
| D0 old | 20/60/20 20/55/25 20/55/25 | 0.767 (0.029) | 0.200 | 20/55/25 20/50/30 15/60/25 | 0.733 (0.029) | 0.183 |
| D3 old | 20/55/25 ×3 | 0.750 (0.000) | 0.200 | 25/50/25 25/55/20 20/55/25 | 0.767 (0.029) | 0.233 |
| D12 old | 25/50/25 20/55/25 20/55/25 | 0.750 (0.000) | 0.217 | 25/55/20 ×3 | 0.800 (0.000) | 0.250 |
| D50 old | 25/50/25 30/50/20 25/55/20 | 0.783 (0.029) | 0.267 | 25/55/20 ×3 | 0.800 (0.000) | 0.250 |
| D100 old | 35/45/20 30/50/20 25/55/20 | 0.800 (0.000) | 0.300 | 25/55/20 25/60/15 25/55/20 | 0.817 (0.029) | 0.250 |
| Trise old | 20/55/25 20/55/25 20/60/20 | 0.767 (0.029) | 0.200 | 30/50/20 25/55/20 25/50/25 | 0.783 (0.029) | 0.267 |
| Tfall old | 25/45/30 25/45/30 25/50/25 | 0.717 (0.029) | 0.250 | 35/45/20 25/55/20 25/50/25 | 0.783 (0.029) | 0.283 |

*Validity:* W1 42/42 valid at the first attempt, 0 retries, output 13 tokens; W2 42/42, 0
retries, output 13 tokens. **W3 0/42 valid at the first attempt and 0/126 attempts valid under
the pre-registered W3 rule: all 42 decisions are fallbacks** (2 retries each). Every W3 reply was
prose (109–402 output tokens) — reasoning plus the three numbers, e.g. "A) Stay at home: 2 /
B) Go out, but take precautions: 6 / C) Go out and carry on as normal: 2" with explanation.
W3 therefore has no caution values under the rule.

*Criteria (pre-registered operationalisation):*
| wording | (i) c(D100) > c(D0), both | (ii) old ≥ young, 7/7 | (iii) c(Trise) ≥ c(Tfall), both | passes |
|---|---|---|---|---|
| W1 | **PASS** (young 0.717 vs 0.667; old 0.800 vs 0.767) | **PASS** (7/7) | FAIL (young 0.550 vs 0.583; old 0.767 vs 0.717 passes) | 2/3 |
| W2 | **PASS** (young 0.733 vs 0.683; old 0.817 vs 0.733) | **PASS** (7/7) | FAIL (young 0.667 vs 0.683; old 0.783 = 0.783 passes) | 2/3 |
| W3 | FAIL (no valid replies) | FAIL | FAIL | 0/3 |

**Selection rule outcome: W1 and W2 tie at 2/3; the tie goes to W1. Winner: W1** (the frozen
template, unchanged). At least one wording passed (i), so the stop condition did not trigger.

*Supplementary, NOT pre-registered and NOT used in selection:* a post-hoc extraction of the last
number after "A)", "B)", "C)" in each W3 reply (`results/step4/pilot_v4_w3_posthoc.log`), counting
only extractions summing to 10, recovers 119 of 126 attempts. Caution: young 0.767–0.789, old
0.800–0.844; c(D100) − c(D0) = −0.011 for both agents; c(Trise) − c(Tfall) young −0.021, old
+0.011; old ≥ young 7/7.

*Predictions vs outcome:* W1 (i) FAIL — **wrong** (PASS); W1 (ii) PASS — correct; W2 (i) PASS —
correct; W2 (ii) PASS — correct; W3 at least one invalid first attempt — correct (42/42 invalid);
W3 (ii) PASS — **wrong** (no valid replies); W1 and W2 42/42 valid — correct; winner W2 — **wrong**
(W1, by the tie rule). (iii) and W3 (i) were given as ~50% and are not scored.

*Note, measured:* the (i) margins are small relative to the repeat SD (0.000–0.058): W1 young
+0.050, old +0.033; W2 young +0.050, old +0.083. In C35, whose histories had cumulative = 4-week total + 5 (D0: 5, D100: 105; here 0 and 125),
W1's young agent gave c(D100) = c(D0) = 0.683.

**C38 — Arm 3, step 1: generation and mechanical checks of K = 5 rules. PRE-REGISTRATION,
written before any generation call.** [Design: planning chat (Max), 10 Oct 2026.]
`experiments/step5_arm3_generate.py`. No epidemic simulation is run.

*Generation:* the frozen arm-3 instruction v1 (A66; the script asserts its SHA-256) as the single
user message; model `claude-haiku-5-5`; A65 settings (thinking `{"type": "disabled"}`; effort,
temperature, top_p, top_k not sent; no system prompt). `max_tokens` 8192 (implementation cap,
A65 left arm 3's cap open; a reply stopping at the cap fails check 1). Each rule is an
independent fresh call. Code = the first fenced code block in the reply if there is one,
otherwise the whole reply. Regeneration only on a mechanical failure (A51), every attempt
logged; implementation safety stop: 5 attempts for one rule → stop and report. Cost guard $1
(expected about $0.005).

*A53 checks as implemented* (static check first, so code is executed only if it passes):
(3, static) parses; only `math` imported; none of open, exec, eval, compile, `__import__`, input,
print, globals, locals, vars, getattr, setattr, delattr, breakpoint, help, exit, quit, memoryview,
id, hash, dir, type, object, random, time, os, sys; no dunder attributes; one top-level
`decide(p)` with one parameter; every attribute read on `p` is one of the 11 Perception fields.
(1) runs: executed with a restricted builtins set (imports limited to `math`); every grid call
returns without error. (2) valid probabilities: a dict with exactly the keys stay_home /
precautions / normal; values real, finite, ≥ 0, summing to 1 within 1e-9. (3, dynamic) `p` is a
proxy that raises on any non-field attribute. (4) deterministic: a second fresh execution over
the grid in reverse order, and two back-to-back repeat calls per point, give identical outputs.
*Grid:* 82,208 inputs — 62,208 structured (population 3,000; day 0/7/60/600; deaths_28day_mean
and …_7d_ago 0/0.1/3.6/100 each; cumulative 0/10/3,000; social_norm 0/0.85/1; age band
0/2/8/9 with its own vulnerability; occupation_flex 0/0.41/1; response_efficacy 0/0.8/1; all
three current actions; consistent and inconsistent combinations alike) plus 20,000 random
points (seed 20261010) over wide ranges (deaths per day to 10,000, cumulative to 10^6, day to
10,000, population 1/3,000/100,000, vulnerability and the other fractions uniform on 0–1).
Self-test before use (synthetic rules): a valid rule passes; `import random`, a non-field
attribute, `open`, probabilities summing to 1.5, a division by zero at day 0, negative
probabilities, and a rule with hidden call-count state each fail. (The first version of check 4
let the hidden-state rule pass by coincidence of call parity; fixed before any generation.)

*Freeze (A54):* each passing rule is written once to `src/arm3_rules/v1/rule_k.py` (exact
extracted code; never rewritten — the script refuses to overwrite), with the full reply
`rule_k_reply.txt` and `manifest.json` (prompt file and SHA-256, model requested and served,
settings, UTC time, request id, tokens, cost, code and reply SHA-256, and the log of every
attempt including failures). Rejected replies go to `results/step5/`.

*Caution curve (E24 b):* each rule evaluated on C37's situations (D0/D3/D12/D50/D100, also
Trise/Tfall; young and old pilot agents; social_norm 0.85; current_action normal), caution =
1 − P(normal), shown next to arm 2's C37 W1 answers.

*Predictions (planning chat, Max), [Speculation], recorded before generation and before any
simulation:* (1) arm-3 rules react to deaths more strongly than arm 2's pilot answers (medium
confidence). (2) The rules differ substantially from each other (medium confidence).
Operationalisation not specified; the facts reported against (1) are each rule's c(D100) −
c(D0) per agent next to arm 2 W1's (young +0.050, old +0.033, C37).

**C38 results. [Measured facts only.]** Run 10 Oct 2026 (07:46–07:47 UTC), `python
experiments/step5_arm3_generate.py --run` then `--curves`; `results/step5/arm3_generate.log`,
`arm3_curves.{json,log}`, `arm3_field_use.log`. Frozen rules: `src/arm3_rules/v1/rule_1.py` …
`rule_5.py`, replies `rule_k_reply.txt`, `manifest.json`.

*Generation:* 5 calls for 5 rules; **every rule passed all A53 checks on its first attempt; 0
regenerations; 0 rejected replies.** Served model `claude-haiku-5-5`; stop_reason `end_turn`;
input 1,257 tokens per call; output 845–972 tokens; **total cost $0.00291.** Every reply was a
single fenced code block (extracted as the code). Grid: 82,208 inputs per rule.

| rule | code SHA-256 |
|---|---|
| 1 | `cbcce5bf187e7909cb05d85968721e811ad5c9419fe5a5fbb95c07e0455d01f5` |
| 2 | `879e8f3cdbf06f97a181d88c31ba1954831428a620e357cec98b7d60089f7fb7` |
| 3 | `90a90bb858c09a9ac90ebba7a7772c3ed5e3fa2bcd68e22794827f3dd4223747` |
| 4 | `a15335f89fb0ddad736f15e6d915d9994e74821a89ee799f2073f457f487d69e` |
| 5 | `7bbcaff266d008f95444037c8536df7eccff781a61faf8e563e5947499eecbed` |

*Structure (read from the code):* all five compute utility scores for the three options and
apply a softmax; all five add a bonus for the current action; all five read deaths, social_norm,
occupation_flex and response_efficacy. Several compute quantities they never use (rules 2, 3, 4
compute rounded 4-week totals that do not enter the output; rule 1 has terms multiplied by 0.0).
*Fields that do NOT change the output* (each field varied over 3 values at 3,000 grid points;
`arm3_field_use.log`): rule 1 none; rule 2 `day`; rule 3 `age_band`, `day`; rule 4
`deaths_cumulative`, `age_band`, `day`; rule 5 `age_band`, `day`. (Rules 3–5 use age only through
`vulnerability`.)

*Caution curve on C37's situations (c = 1 − P(normal) [P(stay home)]; social_norm 0.85,
current_action normal; arm 2 = C37 W1 mean of 3 replies):*

| agent | rule | D0 | D3 | D12 | D50 | D100 | Trise | Tfall |
|---|---|---|---|---|---|---|---|---|
| young | arm 2 W1 | 0.667 [0.10] | 0.650 [0.10] | 0.667 [0.10] | 0.667 [0.15] | 0.717 [0.13] | 0.550 [0.10] | 0.583 [0.10] |
| young | rule 1 | 0.171 [0.06] | 0.372 [0.17] | 0.512 [0.27] | 0.628 [0.36] | 0.654 [0.38] | 0.567 [0.31] | 0.538 [0.29] |
| young | rule 2 | 0.694 [0.31] | 0.992 [0.74] | 1.000 [0.87] | 1.000 [0.94] | 1.000 [0.96] | 1.000 [0.87] | 1.000 [0.88] |
| young | rule 3 | 0.158 [0.04] | 0.286 [0.09] | 0.376 [0.13] | 0.378 [0.13] | 0.378 [0.13] | 0.377 [0.13] | 0.377 [0.13] |
| young | rule 4 | 0.057 [0.01] | 0.061 [0.01] | 0.076 [0.02] | 0.162 [0.05] | 0.273 [0.09] | 0.101 [0.03] | 0.076 [0.02] |
| young | rule 5 | 0.100 [0.04] | 0.104 [0.04] | 0.115 [0.04] | 0.157 [0.06] | 0.195 [0.08] | 0.115 [0.04] | 0.124 [0.05] |
| old | arm 2 W1 | 0.767 [0.20] | 0.750 [0.20] | 0.750 [0.22] | 0.783 [0.27] | 0.800 [0.30] | 0.767 [0.20] | 0.717 [0.25] |
| old | rule 1 | 0.171 [0.06] | 0.511 [0.27] | 0.702 [0.42] | 0.812 [0.53] | 0.829 [0.55] | 0.760 [0.47] | 0.731 [0.45] |
| old | rule 2 | 0.754 [0.35] | 0.995 [0.76] | 1.000 [0.88] | 1.000 [0.95] | 1.000 [0.97] | 1.000 [0.88] | 1.000 [0.89] |
| old | rule 3 | 0.336 [0.11] | 0.530 [0.23] | 0.635 [0.30] | 0.637 [0.30] | 0.637 [0.30] | 0.636 [0.30] | 0.636 [0.30] |
| old | rule 4 | 0.112 [0.03] | 0.120 [0.03] | 0.147 [0.04] | 0.293 [0.10] | 0.448 [0.18] | 0.193 [0.06] | 0.147 [0.04] |
| old | rule 5 | 0.128 [0.05] | 0.133 [0.05] | 0.147 [0.06] | 0.198 [0.08] | 0.243 [0.10] | 0.147 [0.06] | 0.158 [0.06] |

(Values rounded to 3 decimals; 1.000 means P(normal) < 0.0005.)

*Summaries (computed):*
- c(D100) − c(D0): young — rules 1–5: +0.483, +0.306, +0.219, +0.216, +0.095; old — +0.658,
  +0.246, +0.301, +0.336, +0.115. Arm 2 W1 (C37): young +0.050, old +0.033. Every rule's
  difference exceeds arm 2's for both agents (5/5, 5/5).
- Caution non-decreasing over D0 → D100 for every rule and both agents (10/10).
- Spread across the five rules at the same situation: young c at D0 0.057–0.694, at D12
  0.076–1.000, at D100 0.195–1.000; old at D0 0.112–0.754, at D100 0.243–1.000.
- c(old) ≥ c(young) in 7/7 situations for every rule (rule 1 ties at D0, 0.171 both).
- c(Trise) − c(Tfall): rule 1 +0.029 (both agents); rule 2 −0.0001 (both); rule 3 +0.0006
  (both); rule 4 young +0.026, old +0.046; rule 5 young −0.009, old −0.011.

**C39 — Arm 3, step 2: epidemic runs of the 5 frozen rules. PRE-REGISTRATION, written before
any arm-3 epidemic run.** [Design: planning chat (Max), 10 Oct 2026.] No API calls. Rules,
prompt and settings unchanged (rule files are hash-checked at load).

*Setup:* shared world (`src/shared_world.py`), N = 3,000 frozen population, 600 days, 10
initial infected, per-agent f_D, window 28, detection 0.7, 48 sub-steps. Only never-ill agents
(S or E) decide (A38, A42); re-ask probability p = 0.3 per agent per day (A41, provisional and
UNSOURCED); no agent is re-asked on a day starting with E + I = 0 (A55, new opt-in flag
`stop_deciding_when_no_infection`). Each of rules 1–5 × S1 (R0 3, T_H 14), S2 (R0 2), S3 (T_H
28) × seeds 0–29 = 450 runs. Control: `AlwaysNormal` in the same (discrete-mode) world, same
seeds — one control per scenario and seed, shared by the five rules (90 runs). (Arm 1's C30
controls are run_cbf_behaviour with β_B = 0, a different draw order; each arm is compared with
its own control.)

*Arm-3 decision function (`src/arm3.py`, `Arm3Rule`):* Perception built from world data only —
deaths_28day_mean = the world's awareness signal at the start of the day; …_7d_ago = the same
signal 7 days earlier (0 before day 7); deaths_cumulative = reported deaths on all earlier days;
current_action; social_norm = the world's value at the start of the day; the agent's frozen
age_band, vulnerability, occupation_flex, response_efficacy; population 3,000; day. Action drawn
from the decision stream (A52): one uniform u per re-asked agent in index order; stay_home if
u < P(stay_home), precautions if u < P(stay_home) + P(precautions), else normal. Day-0 actions
all normal (as CBF's S^B starts empty); rules act through re-asking from day 0.
`tests/test_arm3.py` (7 tests, pass): every rule loads; an edited rule is refused; the
Perception equals the world's series (signal, signal 7 days earlier, cumulative, norm); no
re-asking on days starting with E + I = 0; sampled shares match the probabilities; the
supplementary norm definition; E-by-action counts. The 61 earlier fast tests still pass (the
additions leave every default run bit-identical).

*Metrics, as C30:* M3 = T10–90 on daily incidence; **stretch** = arm M3 ÷ own-control M3:
ratio of means [95% CI, 1,000 paired bootstrap resamples of seeds, seed 20261005], median
per-seed ratio, share of seeds with per-seed ratio > ×1.5; **peak-I reduction** (% of control
mean, paired SEM); **final S** (arm, and paired increase); **M1 wave count** (EpidemicKabu,
kernel 18); **runs finished by day 600** (E + I = 0 at day 600; A35 truncation rule);
**death responsiveness** (E24 as filled: per-run Spearman, reported as mean and median over
runs, with n defined). **Arm 3 as a whole:** per scenario, the mean and the min–max over the
5 rules of each statistic, next to arm 1 (C30). Arm 1's death responsiveness: arm 1 re-run
through `run_shared_world` (`CBFArm1`, bit-identical to run_cbf_behaviour, C31) for S1/S2/S3 ×
30 seeds; final S and peak I checked against the stored C27 runs.

*Supplementary (does not replace the main result):* S1 × 5 rules × 30 seeds rerun with
social_norm = agents acting normal / agents in S, E, I or R not staying home
(`social_norm_def="alive_not_home_not_H"`); same seeds and control; reported as the difference
from the main S1 result.

*Predictions (planning chat, Max), [Speculation], recorded before running:*
- Rule 2: strong suppression from early on (large peak reduction; may resemble the
  constant-caution ceiling case); low confidence on the stretch.
- Rules 4 and 5: mild effects, similar to arm 1 (stretch below ×1.5).
- The 5 rules spread widely in stretch and peak reduction.
- Death responsiveness: positive for every rule.

*Time gate (instruction: stop if the upper-end projection exceeds 10 minutes) — measured
before any main run (timing runs: S2, rules 1–5, seeds 0–15, 16 workers):* simulation 0.23
s/run effective (per-run maximum 7.6 s, median 2.8 s); EpidemicKabu 0.58 s/run effective (48
calls; C30: 0.50). Work: 780 simulations (450 arm 3 + 90 control + 90 arm 1 + 150
supplementary) and 690 wave counts (arm 3, control, supplementary; arm 1's are in C30).
Projection: 3.0 + 6.7 = **9.7 min at measured rates; 6.2 + 6.7 = 12.9 min at the upper end**
(every simulation as slow as the slowest). **Upper end exceeds 10 minutes → stopped before any
main run; reported to the planning chat.**
*Approved by Max (10 Oct 2026): run the full batch, including the supplementary and its wave
counts.*

**C39 results. [Measured facts only.]** Run 10 Oct 2026, `python experiments/step5_arm3_runs.py
--sim` then `--score`; `results/step5/arm3_runs.npz`, `arm3_runs_sim.log`, `arm3_scores.{json,log}`.
**Wall time 8.0 min** (780 simulations 2.3 min, per run 0.6–11.3 s; 690 wave counts 5.7 min).
**Arm-1 shared-world rerun = stored C27 runs: final S and peak I identical on 30/30 seeds in each
of S1, S2, S3.** Every run (arm 3, control, arm 1, supplementary) had E + I = 0 by day 600
(30/30 everywhere), so A35 truncation does not apply. M3 defined on 30/30 for every arm-3 config
and control. Controls: S1 final S 0.0587, peak I 681.1; S3 identical to S1 (T_H changes only the
infection-to-death delay, and the no-behaviour control's infection draws do not depend on it);
S2 final S 0.1996, peak I 358.9. Control M3: S1/S3 23.2 d, S2 42.6 d. n = 30 seeds for every
statistic unless stated.

*Per rule and scenario.* Stretch = ratio of mean M3s [95% bootstrap CI]; median = median
per-seed ratio; > ×1.5 = seeds with per-seed ratio > 1.5; peak red = peak-I reduction vs control
(paired SEMs); final S (paired increase); M1 = mean wave count arm / control, runs with > 1 wave;
DR = death responsiveness, mean / median of per-run Spearman (n defined); caution = mean realised
cautious share of deciding agents over active days.

| scen | rule | stretch [95% CI] | median | > ×1.5 | peak red | final S (+ vs ctrl) | M1 arm/ctrl; > 1 wave | DR mean / median (n) | caution |
|---|---|---|---|---|---|---|---|---|---|
| S1 | 1 | ×1.475 [1.347, 1.631] | ×1.383 | 11/30 | 39.6% (−18.7 SEM) | 0.298 (+0.239) | 1.03/1.00; 1/30 | +0.922 / +0.935 (30) | 0.483 |
| S1 | 2 | ×0.986 [0.778, 1.228] | ×0.869 | 3/30 | 97.7% (−113.7 SEM) | 0.983 (+0.924) | 1.03/1.00; 1/30 | +0.691 / +0.716 (8) | 0.860 |
| S1 | 3 | ×1.699 [1.600, 1.830] | ×1.614 | 18/30 | 47.5% (−34.1 SEM) | 0.292 (+0.233) | 1.07/1.00; 1/30 | +0.928 / +0.931 (30) | 0.476 |
| S1 | 4 | ×1.085 [1.074, 1.094] | ×1.087 | 0/30 | 6.3% (−19.5 SEM) | 0.075 (+0.017) | 1.10/1.00; 2/30 | +0.262 / +0.280 (30) | 0.054 |
| S1 | 5 | ×1.180 [1.165, 1.195] | ×1.174 | 0/30 | 15.1% (−25.6 SEM) | 0.092 (+0.033) | 1.03/1.00; 1/30 | +0.171 / +0.140 (30) | 0.126 |
| S2 | 1 | ×1.888 [1.604, 2.208] | ×1.620 | 18/30 | 59.6% (−21.6 SEM) | 0.578 (+0.378) | 1.43/1.00; 8/30 | +0.866 / +0.869 (30) | 0.418 |
| S2 | 2 | ×0.414 [0.347, 0.479] | ×0.372 | 0/30 | 97.0% (−59.1 SEM) | 0.991 (+0.792) | 1.00/1.00; 0/30 | +0.711 / +0.720 (3) | 0.835 |
| S2 | 3 | ×1.942 [1.827, 2.054] | ×1.932 | 27/30 | 62.2% (−33.9 SEM) | 0.522 (+0.322) | 1.20/1.00; 6/30 | +0.901 / +0.906 (30) | 0.380 |
| S2 | 4 | ×1.046 [1.038, 1.054] | ×1.047 | 0/30 | 5.3% (−8.4 SEM) | 0.216 (+0.017) | 1.00/1.00; 0/30 | +0.481 / +0.489 (30) | 0.032 |
| S2 | 5 | ×1.200 [1.179, 1.223] | ×1.191 | 0/30 | 19.5% (−18.8 SEM) | 0.254 (+0.055) | 1.00/1.00; 0/30 | +0.380 / +0.367 (30) | 0.115 |
| S3 | 1 | ×1.364 [1.291, 1.448] | ×1.298 | 7/30 | 32.8% (−18.5 SEM) | 0.243 (+0.185) | 1.07/1.00; 1/30 | +0.915 / +0.932 (30) | 0.463 |
| S3 | 2 | ×1.003 [0.810, 1.256] | ×0.896 | 3/30 | 97.7% (−113.7 SEM) | 0.982 (+0.924) | 1.03/1.00; 1/30 | +0.621 / +0.679 (5) | 0.858 |
| S3 | 3 | ×1.574 [1.525, 1.640] | ×1.544 | 19/30 | 44.2% (−33.9 SEM) | 0.263 (+0.204) | 1.03/1.00; 1/30 | +0.933 / +0.942 (30) | 0.471 |
| S3 | 4 | ×1.075 [1.065, 1.084] | ×1.083 | 0/30 | 6.2% (−20.5 SEM) | 0.074 (+0.015) | 1.03/1.00; 1/30 | −0.005 / +0.008 (30) | 0.051 |
| S3 | 5 | ×1.180 [1.165, 1.195] | ×1.174 | 0/30 | 14.9% (−23.7 SEM) | 0.090 (+0.031) | 1.00/1.00; 0/30 | −0.053 / −0.094 (30) | 0.125 |

All final-S increases exceed +13 SEM. Rule 2's DR is undefined on most runs because the death
signal never changes while E + I > 0 (no reported deaths before the epidemic ends) on 22/30
(S1), 27/30 (S2), 25/30 (S3) runs; its epidemics are small (total infections, median / max: S1
37 / 112, S2 15 / 50, S3 37 / 112; last active day median 44, 32.5, 44).

*Arm 3 as a whole (mean [min, max] over the 5 rules) next to arm 1 (C30; DR and caution from the
shared-world rerun):*

| scen | | stretch | median per-seed | peak red | final S | M1 | DR mean | caution |
|---|---|---|---|---|---|---|---|---|
| S1 | arm 3 | ×1.285 [0.986, 1.699] | ×1.225 [0.869, 1.614] | 41.2% [6.3, 97.7] | 0.348 [0.075, 0.983] | 1.05 [1.03, 1.10] | +0.595 [+0.171, +0.928] | |
| S1 | arm 1 | ×1.079 [1.018, 1.158] | ×1.080 (mean) | 12.8% | 0.144 (+0.086) | 1.00 | +0.792 / median +0.799 (30) | 0.580 |
| S2 | arm 3 | ×1.298 [0.414, 1.942] | ×1.232 [0.372, 1.932] | 48.7% [5.3, 97.0] | 0.512 [0.216, 0.991] | 1.13 [1.00, 1.43] | +0.668 [+0.380, +0.901] | |
| S2 | arm 1 | ×1.239 [0.962, 1.704] | ×0.964 | 23.6% | 0.408 (+0.203) | 1.20 | +0.647 / +0.659 (30) | 0.554 |
| S3 | arm 3 | ×1.239 [1.003, 1.574] | ×1.199 [0.896, 1.544] | 39.2% [6.2, 97.7] | 0.331 [0.074, 0.982] | 1.03 [1.00, 1.07] | +0.482 [−0.053, +0.933] | |
| S3 | arm 1 | ×1.020 [0.987, 1.057] | ×1.021 (mean) | 7.0% | 0.109 (+0.051) | 1.00 | +0.864 / +0.893 (30) | 0.512 |

(Arm 1's "caution" is the S^B share of S + E, E24; arm 3's counts E agents by realised action.)

*Predictions (Max) vs outcome:*
- Rule 2 strong suppression from early on, large peak reduction — peak I −97.0 to −97.7%, final
  S 0.98–0.99, epidemics end by a median day 32.5–44. Stretch (low confidence): ×0.986 (S1),
  ×0.414 (S2), ×1.003 (S3). Resemblance to the constant-caution ceiling case not computed.
- Rules 4 and 5 mild, stretch below ×1.5 — **as predicted** (×1.046–1.200 in all 6 cases;
  0/30 runs > ×1.5 in each). Peak reduction 5.3–19.5% (arm 1: 7.0–23.6%).
- The 5 rules spread widely — stretch ×0.986–1.699 (S1), ×0.414–1.942 (S2), ×1.003–1.574 (S3);
  peak reduction 5.3–97.7%.
- Death responsiveness positive for every rule — **not in S3**: rule 4 −0.005, rule 5 −0.053
  (mean). Positive for every rule in S1 and S2.

*Caveat on rule 2's stretch (planning chat, 10 Oct 2026; an interpretation, not a measurement):* rule 2's M3 is computed on very small epidemics (median 15–37 infections), so its stretch reflects suppression, not flattening, and is a poor guide to stretch in either the main or the supplementary run.

**C39 addendum — averaged-curve M3 (A33), added 10 Oct 2026. [Measured facts only.]** C39 as
first reported computed T10–90 per run only. Now also on the 1%-aligned averaged curve (A33,
`step3_shape_metrics.align_average`'s method; checked equal on the S1 control: 23.0 d), **per rule
and scenario only, never across rules**; 1,000 paired bootstrap resamples of seeds (seed
20261005); runs that never reach 1% cumulative incidence (30 infections) are left out (n used).
`python experiments/step5_arm3_runs.py --aligned`; `results/step5/arm3_aligned.{json,log}`.
Aligned M3 is a whole number of days; control S1/S3 23 [22, 24] d, S2 42 [41, 44] d (30/30).

| config | aligned M3 arm [95% CI] (n used) | aligned stretch [95% CI] | per-run stretch (C39) |
|---|---|---|---|
| rule 1 S1 | 33 [31, 36] (30) | ×1.435 [1.333, 1.566] | ×1.475 |
| rule 2 S1 | 47 [17, 77] (**23/30**) | ×2.043 [0.739, 3.348] | ×0.986 |
| rule 3 S1 | 39 [37, 42] (30) | ×1.696 [1.583, 1.826] | ×1.699 |
| rule 4 S1 | 25 [24, 25] (30) | ×1.087 [1.042, 1.091] | ×1.085 |
| rule 5 S1 | 28 [26, 28] (30) | ×1.217 [1.125, 1.227] | ×1.180 |
| rule 1 S2 | 76 [65, 93] (30) | ×1.810 [1.537, 2.186] | ×1.888 |
| rule 2 S2 | 19 [0, 19] (**2/30**) | ×0.452 [0.000, 0.463] | ×0.414 |
| rule 3 S2 | 83 [78, 89] (30) | ×1.976 [1.833, 2.095] | ×1.942 |
| rule 4 S2 | 45 [43, 46] (30) | ×1.071 [1.023, 1.073] | ×1.046 |
| rule 5 S2 | 51 [50, 53] (30) | ×1.214 [1.163, 1.244] | ×1.200 |
| rule 1 S3 | 31 [29, 33] (30) | ×1.348 [1.250, 1.435] | ×1.364 |
| rule 2 S3 | 47 [19, 76] (**23/30**) | ×2.043 [0.792, 3.305] | ×1.003 |
| rule 3 S3 | 37 [35, 39] (30) | ×1.609 [1.500, 1.696] | ×1.574 |
| rule 4 S3 | 25 [24, 25] (30) | ×1.087 [1.000, 1.091] | ×1.075 |
| rule 5 S3 | 28 [26, 28] (30) | ×1.217 [1.125, 1.227] | ×1.180 |
| supp. rule 1 S1 | 31 [29, 33] (30) | ×1.348 [1.250, 1.435] | ×1.357 |
| supp. rule 2 S1 | 42 [31, 53] (28/30) | ×1.826 [1.363, 2.304] | ×1.514 |
| supp. rule 3 S1 | 33 [32, 35] (30) | ×1.435 [1.375, 1.545] | ×1.433 |
| supp. rule 4 S1 | 23 [23, 24] (30) | ×1.000 [0.958, 1.045] | ×1.012 |
| supp. rule 5 S1 | 26 [25, 26] (30) | ×1.130 [1.083, 1.182] | ×1.111 |

For rules 1, 3, 4, 5 the aligned and per-run stretch differ by at most 0.08. For rule 2 they
differ widely, and the aligned value rests on 23/30 (S1, S3) or 2/30 (S2) runs.

**C40 — Supplementary to C39 (does not replace it): S1 with social_norm = agents acting normal
/ agents in S, E, I or R not staying home. [Measured facts only.]** Same run as C39 (same seeds,
same control). Difference from the main S1 result (supplementary − main):

| rule | stretch (main → supp) | median | > ×1.5 | peak red | final S | M1 | DR mean | caution |
|---|---|---|---|---|---|---|---|---|
| 1 | ×1.475 → ×1.357 [1.283, 1.438] (−0.118) | ×1.326 | 4/30 | 39.6 → 34.7% (−4.9) | 0.298 → 0.261 (−0.037) | 1.03 → 1.03 | +0.922 → +0.921 | 0.483 → 0.457 |
| 2 | ×0.986 → ×1.514 [1.249, 1.838] (+0.528) | ×1.311 | 11/30 | 97.7 → 97.5% (−0.2) | 0.983 → 0.976 (−0.006) | 1.03 → 1.03 | +0.691 → +0.705 | 0.860 → 0.845 |
| 3 | ×1.699 → ×1.433 [1.381, 1.494] (−0.266) | ×1.369 | 8/30 | 47.5 → 36.8% (−10.7) | 0.292 → 0.224 (−0.068) | 1.07 → 1.07 | +0.928 → +0.903 | 0.476 → 0.435 |
| 4 | ×1.085 → ×1.012 [1.003, 1.019] (−0.073) | ×1.000 | 0/30 | 6.3 → 1.2% (−5.1) | 0.075 → 0.061 (−0.014) | 1.10 → 1.00 | +0.262 → +0.340 | 0.054 → 0.022 |
| 5 | ×1.180 → ×1.111 [1.095, 1.126] (−0.069) | ×1.108 | 0/30 | 15.1 → 10.1% (−5.0) | 0.092 → 0.079 (−0.013) | 1.03 → 1.03 | +0.171 → +0.293 | 0.126 → 0.103 |

Finished by day 600: 30/30 for every rule. With the supplementary definition, rules 1, 3, 4, 5
have lower stretch, peak reduction, final S and caution than in the main run; rule 2's stretch
rises (×0.986 → ×1.514) with peak reduction and final S nearly unchanged.

**C41 — Arm 3 side tests T1–T3 (S1 only). PRE-REGISTRATION, written before any side-test run
(timing runs only).** [Design: planning chat (Max), 10 Oct 2026.] No API calls; no rule or
prompt changed. `experiments/step5_arm3_side.py`. Rules 1–5 × seeds 0–29, S1, everything else as
C39 (Perception, sampling, A55 stop, N 3,000, 600 days). Baseline = C39 S1 (p = 0.3). Control =
C39's S1 `AlwaysNormal` runs (no decisions are made in a control, so it is the same for every
test; reused from `results/step5/arm3_runs.npz`).

- **T1 — re-decide rate (E2):** p = 0.1 and p = 1.0 per agent per day.
- **T2 — "variant A-physical" (E21):** currently-ill agents (I) keep deciding with the SAME rule,
  which cannot see illness (`run_shared_world(ill_decide=True)`). Choices (Max): staying home now
  also stops an ill agent spreading (an I agent at home leaves the force of infection);
  precautions do NOT reduce an ill agent's infectiousness (consistent with A39/A57); a newly ill
  agent keeps its last action until re-asked. Implementation choice (Claude Code, following A42):
  agents leaving I (to R or H) are reset to normal. The LLM-judgement version (new instruction
  with own_health) is deferred until after the supervisor meeting.
- **T3 — no stay-home button:** P(stay_home) is added to P(precautions) (intention kept, option
  removed). **A choice, UNSOURCED** (`Arm3Rule(merge_stay_home=True)`).

*Reported per rule and test, next to the C39 S1 baseline:* stretch (ratio of mean M3s [95% CI],
median per-seed ratio, share > ×1.5) and the aligned averaged-curve stretch (A33, per rule);
peak-I reduction; final S; **attack size = 1 − final S** (fraction of the population ever
infected, including the 10 initial cases); M1 wave count; death responsiveness (E24 as filled:
caution among S + E — in T2 too, although I agents also decide there); runs finished by day 600.

*Code and tests:* `run_shared_world(ill_decide=...)` and `Arm3Rule(merge_stay_home=...)`, both
off by default. `tests/test_arm3.py` adds 4 tests (merge never draws stay_home; default
unchanged; with everyone home and p = 1.0 the ill-decide world stops the epidemic at ≤ 12
infections; recovered agents act normal). 72 fast tests pass.

*Predictions (planning chat, Max), [Speculation]:*
- T1: p = 0.1 gives milder effects (slower reactions); p = 1.0 gives somewhat stronger effects;
  low confidence.
- T2: stronger suppression for every rule, largest for rules 1–3.
- T3: milder effects; rule 2's suppression weakens most.

*Time gate (stop if the upper-end projection exceeds 15 minutes):* timing runs (each test × each
rule × seeds 0–1, 40 runs, 16 workers): 0.26 s/run effective; per-run maximum 6.5 s (T1 p = 1.0).
Work: 600 simulations + 600 wave counts (0.58 s/run effective, C39). Projection: 2.6 + 5.8 =
**8.4 min at measured rates; 7.1 + 5.8 = 12.9 min at the upper end** (every simulation as slow
as C39's slowest single run, 11.3 s). Under 15 minutes → run.

**C41 results. [Measured facts only.]** Run 10 Oct 2026, `python experiments/step5_arm3_side.py
--sim` then `--score`; `results/step5/arm3_side_runs.npz`, `arm3_side_sim.log`,
`arm3_side_scores.{json,log}`. **Wall 6.6 min** (600 simulations 1.7 min, per run 0.5–7.1 s; 600
wave counts 4.9 min). Every run finished by day 600 (30/30 in every test). M3 defined on 30/30
everywhere. The C39 baseline rows below are recomputed from the C39 runs and equal C39 and its
addendum. Control M1 1.00. n = 30 seeds.

| rule | test | stretch [95% CI] | median | > ×1.5 | aligned stretch (n used) | peak red (SEM) | final S (paired +) | attack size | M1; > 1 wave | DR mean / median (n) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | C39 p 0.3 | ×1.475 [1.347, 1.631] | ×1.383 | 11/30 | ×1.435 (30) | 39.6% (−18.7) | 0.298 (+0.239) | 0.702 | 1.03; 1/30 | +0.922 / +0.935 (30) |
| 1 | T1 p 0.1 | ×1.196 [1.159, 1.236] | ×1.191 | 1/30 | ×1.217 (30) | 29.8% (−23.6) | 0.263 (+0.205) | 0.737 | 1.07; 2/30 | +0.887 / +0.902 (30) |
| 1 | T1 p 1.0 | ×1.646 [1.542, 1.770] | ×1.609 | 21/30 | ×1.696 (30) | 47.9% (−22.8) | 0.321 (+0.263) | 0.679 | 1.17; 5/30 | +0.912 / +0.924 (30) |
| 1 | T2 ill decide | ×1.712 [1.513, 1.916] | ×1.544 | 17/30 | ×1.565 (30) | 53.9% (−21.7) | 0.456 (+0.397) | 0.544 | 1.17; 4/30 | +0.907 / +0.914 (30) |
| 1 | T3 no home | ×1.289 [1.250, 1.335] | ×1.255 | 1/30 | ×1.304 (30) | 25.1% (−20.2) | 0.153 (+0.094) | 0.847 | 1.07; 1/30 | +0.913 / +0.927 (30) |
| 2 | C39 p 0.3 | ×0.986 [0.778, 1.228] | ×0.869 | 3/30 | ×2.043 (23) | 97.7% (−113.7) | 0.983 (+0.924) | 0.018 | 1.03; 1/30 | +0.691 / +0.716 (8) |
| 2 | T1 p 0.1 | ×1.263 [1.176, 1.356] | ×1.182 | 6/30 | ×1.174 (30) | 93.3% (−91.1) | 0.929 (+0.870) | 0.071 | 1.00; 0/30 | +0.420 / +0.438 (23) |
| 2 | T1 p 1.0 | ×0.863 [0.678, 1.069] | ×0.842 | 1/30 | ×0.783 (4) | 98.5% (−116.0) | 0.992 (+0.933) | 0.008 | 1.03; 1/30 | +0.772 / +0.772 (1) |
| 2 | T2 ill decide | ×0.443 [0.354, 0.556] | ×0.383 | 1/30 | ×0.391 (3) | 98.2% (−114.3) | 0.991 (+0.932) | 0.009 | 1.00; 0/30 | +0.777 / +0.787 (3) |
| 2 | T3 no home | **×2.849 [2.740, 2.967]** | ×2.828 | **30/30** | ×2.826 (30) | 71.4% (−56.2) | 0.383 (+0.324) | 0.617 | 1.03; 1/30 | +0.801 / +0.824 (30) |
| 3 | C39 p 0.3 | ×1.699 [1.600, 1.830] | ×1.614 | 18/30 | ×1.696 (30) | 47.5% (−34.1) | 0.292 (+0.233) | 0.708 | 1.07; 1/30 | +0.928 / +0.931 (30) |
| 3 | T1 p 0.1 | ×1.367 [1.329, 1.408] | ×1.326 | 4/30 | ×1.348 (30) | 37.8% (−36.7) | 0.271 (+0.212) | 0.729 | 1.03; 1/30 | +0.891 / +0.904 (30) |
| 3 | T1 p 1.0 | ×1.781 [1.677, 1.897] | ×1.689 | 24/30 | ×1.783 (30) | 48.5% (−30.0) | 0.274 (+0.216) | 0.726 | 1.07; 2/30 | +0.952 / +0.954 (30) |
| 3 | T2 ill decide | ×1.958 [1.815, 2.108] | ×1.833 | 26/30 | ×1.957 (30) | 57.4% (−36.6) | 0.368 (+0.310) | 0.632 | 1.10; 3/30 | +0.923 / +0.934 (30) |
| 3 | T3 no home | ×1.364 [1.330, 1.398] | ×1.375 | 2/30 | ×1.348 (30) | 28.3% (−27.8) | 0.150 (+0.091) | 0.850 | 1.00; 0/30 | +0.892 / +0.896 (30) |
| 4 | C39 p 0.3 | ×1.085 [1.074, 1.094] | ×1.087 | 0/30 | ×1.087 (30) | 6.3% (−19.5) | 0.075 (+0.017) | 0.925 | 1.10; 2/30 | +0.262 / +0.280 (30) |
| 4 | T1 p 0.1 | ×1.043 [1.031, 1.054] | ×1.043 | 0/30 | ×1.043 (30) | 4.3% (−18.1) | 0.076 (+0.018) | 0.924 | 1.00; 0/30 | +0.627 / +0.653 (30) |
| 4 | T1 p 1.0 | ×1.095 [1.083, 1.106] | ×1.087 | 0/30 | ×1.087 (30) | 8.0% (−22.1) | 0.074 (+0.015) | 0.926 | 1.03; 1/30 | +0.110 / +0.094 (30) |
| 4 | T2 ill decide | ×1.102 [1.090, 1.114] | ×1.091 | 0/30 | ×1.087 (30) | 8.1% (−20.3) | 0.081 (+0.022) | 0.919 | 1.03; 1/30 | +0.252 / +0.228 (30) |
| 4 | T3 no home | ×1.053 [1.044, 1.061] | ×1.043 | 0/30 | ×1.043 (30) | 4.6% (−19.9) | 0.071 (+0.012) | 0.929 | 1.00; 0/30 | +0.243 / +0.251 (30) |
| 5 | C39 p 0.3 | ×1.180 [1.165, 1.195] | ×1.174 | 0/30 | ×1.217 (30) | 15.1% (−25.6) | 0.092 (+0.033) | 0.908 | 1.03; 1/30 | +0.171 / +0.140 (30) |
| 5 | T1 p 0.1 | ×1.151 [1.136, 1.166] | ×1.136 | 0/30 | ×1.174 (30) | 13.2% (−29.8) | 0.099 (+0.040) | 0.901 | 1.00; 0/30 | +0.680 / +0.732 (30) |
| 5 | T1 p 1.0 | ×1.167 [1.152, 1.181] | ×1.174 | 0/30 | ×1.174 (30) | 14.4% (−19.9) | 0.086 (+0.028) | 0.914 | 1.00; 0/30 | −0.033 / −0.040 (30) |
| 5 | T2 ill decide | ×1.252 [1.234, 1.269] | ×1.250 | 0/30 | ×1.261 (30) | 20.4% (−26.0) | 0.108 (+0.049) | 0.893 | 1.03; 1/30 | +0.225 / +0.252 (30) |
| 5 | T3 no home | ×1.108 [1.096, 1.120] | ×1.108 | 0/30 | ×1.130 (30) | 9.6% (−19.9) | 0.077 (+0.019) | 0.923 | 1.00; 0/30 | +0.091 / +0.091 (30) |

*Predictions (Max) vs outcome (facts against each; no verdict beyond the stated direction):*
- T1 p = 0.1 milder: peak reduction lower than baseline for 5/5 rules; final S lower for rules
  1–3, slightly higher for rules 4 (0.076 vs 0.075) and 5 (0.099 vs 0.092); stretch lower for
  rules 1, 3, 4, 5, higher for rule 2 (×1.263 vs ×0.986, larger epidemics: attack 0.071 vs 0.018).
- T1 p = 1.0 somewhat stronger: peak reduction higher for rules 1–4, lower for rule 5 (14.4 vs
  15.1%); final S higher for rules 1–2, lower for rules 3–5; stretch higher for rules 1, 3, 4,
  lower for rules 2 and 5.
- T2 stronger suppression for every rule: **peak reduction and final S higher for 5/5 rules.**
  Gain in final S: rule 1 +0.158, rule 3 +0.077, rule 5 +0.016, rule 2 +0.009, rule 4 +0.006;
  gain in peak reduction (points): 1 +14.3, 3 +9.9, 5 +5.3, 4 +1.8, 2 +0.5 (rule 2 starts at
  97.7%). So the largest gains are rules 1 and 3, not rule 2.
- T3 milder: **peak reduction and final S lower for 5/5 rules.** Rule 2 changes most (peak
  reduction 97.7 → 71.4%, final S 0.983 → 0.383), and its stretch becomes the largest measured
  in this project (×2.849, 30/30 runs > ×1.5).
- Death responsiveness (not predicted): at p = 0.1, rules 4 and 5 rise to +0.627 / +0.680 (from
  +0.262 / +0.171); at p = 1.0 they fall to +0.110 / −0.033.

**C42 — E23 plateau-reachability check. A CAPABILITY TEST, NOT AN ARM. PRE-REGISTRATION,
written before any step is run.** [Design: planning chat (Max), 10 Oct 2026.] No API calls; no
arm, rule or prompt changed. `experiments/step6_plateau_check.py`; outputs `results/step6/`.
Purpose: whether a Weitz-style plateau can occur in the shared world (A37–A39) when healthy
agents stay home in response to deaths.

*Test rule (test case only):* Weitz's g = 1/(1 + (δ/δ_c)^k), k = 2 (figseir_Hlong_k2D.m). Stay
home is one-sided (A39) and ill agents do not decide (A38), so each never-ill agent (S or E)
stays home with probability q = 1 − g; precautions unused. δ and δ_c in deaths per day in the
whole town (Weitz's N·δ_c; `model.run_weitz_behaviour`'s convention). **δ_c is CHOSEN to obtain
a plateau — allowed here because this is a reachability test, not a model of behaviour.**

*Choice rule for δ_c (fixed before Step A):* first candidate = Weitz's own per-capita value
Dcrit = 0.5×10⁻⁵ per day (figseir_Hdel_k2.m; K1/K2, C29) scaled to N = 3,000: **N·δ_c = 0.015
deaths/day**. It is used if Step A shows a plateau with it (A's criterion below). Otherwise the
largest value on the grid {0.005, 0.015, 0.05, 0.15, 0.5, 1.5, 5} that does. The whole grid is
reported for context. The same δ_c is used in B, C and C2.

- **A (equations):** Weitz model B ODE with this g; N = 3,000; S1 (R0 3, latent 2 d, infectious
  6 d, T_H 14); f_D = the frozen population's mean IFR 0.009718 (B–C2 use per-agent f_D, whose
  population mean this is; Weitz's 0.01 would differ from the ABM); I(0) = 10/N, as the ABM;
  δ = γ_H·N·H. Control: the same ODE without behaviour. **A's plateau criterion:** T10–90 stretch
  ≥ ×10 against the no-behaviour ODE, or E + I ≥ 1 person at day 600 ("still active").
- **B (ideal):** shared world, N = 3,000, S1, seeds 0–29; δ = n_H/T_H (Weitz's own, zero lag);
  q recomputed and every never-ill agent's action redrawn each sub-step (new test-only mode
  `"substep"` in `run_shared_world`; never used by an arm; all 72 fast tests still pass).
- **C (arms' real constraints):** same δ_c; δ = the perceived signal, the 28-day mean of 70%-
  reported deaths (A24/A25); decisions once per day at the start of the day, p = 1.0 (everyone);
  A55 stop.
- **C2:** as C with p = 0.3.
Controls for B, C, C2: `AlwaysNormal` in the same world, same seeds (= C39's S1 control).

*Reported for A, B, C, C2:* δ_c; stretch (ratio of mean T10–90 [95% CI, 1,000 paired bootstrap
resamples, seed 20261005], median per-seed ratio, share > ×1.5); peak-I reduction; final S;
attack size (1 − final S); M1 wave count (EpidemicKabu, kernel 18); runs still active at day 600
(E + I > 0). For runs still active, T10–90 is computed on cumulative incidence up to day 600 and
is a lower bound (A35: truncated). One example curve per step against its control: **seed 0**
(fixed here, not chosen after looking), daily incidence on a log-type axis.

*Pass mark for "plateau reachable" (Max):* Step B stretch ≥ ×10, OR a majority of runs (> 15/30)
still active at day 600 with peak reduction ≥ 80%.

*Predictions (planning chat, Max), [Speculation]:* B reproduces a plateau close to A (low-medium
confidence; small-count noise may break it at N = 3,000). C is much weaker than B because of the
delayed signal (medium confidence).

*Time gate:* stop if the upper-end projection exceeds 10 minutes (timing recorded below before
the main run).
*Step A done before timing (it decides δ_c; `results/step6/plateau_ode.{json,log}`):* N·δ_c =
0.015 meets A's criterion (see results), so **δ_c = 0.015 deaths/day** for B, C, C2. *Timing*
(each step × 4 runs, 16 workers, `plateau_timing.log`): per run control 1.0–1.1 s, B 1.6–1.9 s,
C 1.0–1.1 s, C2 0.9–1.1 s. Work: 120 simulations + 122 wave counts (0.58 s/run effective, C39).
Upper end (every simulation at twice the slowest, 3.8 s): 0.5 + 1.2 = **1.7 min** → run.

**C42 results. [Measured facts only.]** Run 10 Oct 2026, `python experiments/step6_plateau_check.py
--ode`, `--sim`, `--score`, `--plot`; `results/step6/plateau_ode.{json,log}`, `plateau_runs.npz`,
`plateau_sim.log`, `plateau_scores.{json,log}`, `plateau_examples.png`. Wall: simulations 0.2
min, wave counts 1.0 min. δ_c = **0.015 deaths/day** (N·δ_c; Weitz's per-capita Dcrit at N =
3,000), chosen by the pre-registered rule: it meets Step A's criterion.

*Step A grid (ODE, N = 3,000, S1; control T10–90 23 d, final S 0.0593, peak I 668.2):*

| N·δ_c | T10–90 (d) | stretch | peak-I red | final S | E + I at day 600 (persons) |
|---|---|---|---|---|---|
| 0.005 | 496 | ×21.57 | 97.6% | 0.855 | 5.14 (active) |
| **0.015** | **502** | **×21.83** | **94.7%** | **0.626** | **11.50 (active)** |
| 0.05 | 387 | ×16.83 | 84.8% | 0.307 | 3.27 (active) |
| 0.15 | 142 | ×6.17 | 62.1% | 0.266 | 0.00 |
| 0.5 | 33 | ×1.43 | 23.8% | 0.203 | 0.00 |
| 1.5 | 24 | ×1.04 | 4.2% | 0.084 | 0.00 |
| 5 | 23 | ×1.00 | 0.4% | 0.062 | 0.00 |

(Stretch for active rows is truncated at day 600, A35: a lower bound.)

*Results at δ_c = 0.015 (B, C, C2: n = 30 seeds; control = shared-world AlwaysNormal, T10–90
23.2 d, peak I 681.1, final S 0.0587, 0/30 active at 600, waves 1.00):*

| step | stretch [95% CI] | median | > ×1.5 | ≥ ×10 | peak-I red | final S | attack | waves (> 1) | active at 600 |
|---|---|---|---|---|---|---|---|---|---|
| A (ODE) | ×21.83 (truncated) | — | — | — | 94.7% | 0.626 | 0.374 | 4 (control 1) | yes (11.5 persons) |
| B | ×1.827 [1.198, 2.510] | ×0.764 | 11/30 | 0/30 | 71.8% (−26.2 SEM) | 0.767 ± 0.031 | 0.233 | 1.63 (12/30) | **0/30** |
| C | ×1.370 [0.760, 2.194] | ×0.652 | 5/30 | 0/30 | 53.6% (−13.3 SEM) | 0.662 ± 0.033 | 0.338 | 1.27 (5/30) | 0/30 |
| C2 | ×0.827 [0.664, 1.127] | ×0.659 | 1/30 | 0/30 | 48.3% (−12.0 SEM) | 0.630 ± 0.031 | 0.370 | 1.03 (1/30) | 0/30 |

Last day with E + I > 0, median (max): B 75.5 (220), C 69 (245), C2 67 (166); control 92.
Mean stay-home share of S while E + I > 0: B 0.616, C 0.623, C2 0.629.

**Pass mark: NOT MET.** B stretch ×1.83 < ×10, and 0/30 runs are active at day 600 (peak
reduction 71.8% < 80%).

*Arithmetic of the signal at N = 3,000 (computed):* in B one hospitalised agent gives δ = 1/14 =
0.071 deaths/day = 4.8 δ_c, so q = 0.958 (two agents: 0.989); with none, q = 0. In C one reported
death in the 28-day window gives a signal of 0.7/28 = 0.025, q = 0.735. The ODE plateau runs at
about 1.5–2 new infections per day (Step A curve), i.e. under one hospitalisation at a time.
The seed-0 example curves (`plateau_examples.png`) show B alternating between bursts and zero
incidence and ending by about day 85; C and C2 end by about day 70.

*Predictions (Max) vs outcome:* "B reproduces a plateau close to A" — **not as predicted** (A
×21.8 and active at 600; B ×1.83, 0/30 active). "C much weaker than B" — C is weaker than B on
every measure (stretch ×1.37 vs ×1.83, peak reduction 53.6 vs 71.8%, final S 0.662 vs 0.767);
C2 weaker again.

## D. Reversals and corrections

**D1 — Discretisation bug.** Setting the daily transition probability to `1 − exp(−rate)` at a
one-day step gives a mean infectious period of 6.51 d instead of 6 and **R₀ = 3.257 instead of
3.000**. Invisible in any single run; caught only by the ODE-convergence test. Gozzi's fix —
12 sub-steps per day — measured at R₀ = 3.006.

**D2 — Shape metric, reversed twice.** First reported as failing in the ABM (control 0.65,
awareness 0.97, wrong direction). Cause: it was being computed on the **death** series, which
has 8 events at N=1,000. Recomputed on incidence it works, and needs N ≥ 3,000.

**D3 — N revised 1,000 → 3,000.** N=1,000 was recommended on control-versus-behaviour
separation alone. That test establishes only that behaviour *matters*, not that it is *graded*.
C5 shows the response is a switch at N=1,000, so all four arms would face a binary input in the
one channel the referent runs through, and could not differ.

**D4 — Caching estimate withdrawn.** A "~4× saving" was quoted without calculation. The
combinatorial state space (~4.6×10⁵) is comparable to the decision count, so caching may save
little. The realised state space must be measured from arm 1's logs.

**D5 — IFR table.** Sourcing pack v3 lists the 9-band `IFR`; the 10-band `IFR_10age` is the one
that pairs with `pop_data_Nk.csv`. Values unaffected, band boundaries differ.

**D7 — The C4 shape-metric result is WITHDRAWN.** "Weitz symmetry reliable at N=3,000,
Cohen's d = 2.58" was computed on 11/30 control runs and **2/30 awareness runs**; the summary
silently dropped undefined values. The tight `0.28 ± 0.03` was two numbers. What looked like
separation was a selection effect over the runs where the metric happened to be computable.

**D8 — Root cause, and it is structural.** Two contributing factors, one fixable and one not:
- *Fixable:* the ABM seeded 1% infected at t=0 (30 agents at N=3,000), leaving no exponential
  growth phase and hence no pre-peak 10% crossing. Reducing the seed to 10 agents (0.33%) takes
  control-run definability from 12/40 to **40/40**. Adopt this regardless — the large seed was
  an unrealistic initial condition anyway.
- *Not fixable:* even with the smaller seed, the metric is defined on only ~50% of awareness
  runs (19–22/40) and has >100% relative variance where defined (26.6 ± 30.3). **The symmetry
  coefficient is referenced to a peak, and the awareness regime is defined by the absence of a
  peak.** A smooth deterministic plateau still has a well-defined maximum with monotone flanks;
  a stochastic plateau does not. Weitz could use this metric because their output is an ODE.

*Consequence:* peak-referenced shape metrics are the wrong family for this problem. Candidates
that avoid a peak landmark — final susceptible fraction, peak-to-mean ratio, time above a
threshold fraction, area concentration — are the direction to search.

**D6 — Oscillation dropped as a scenario target.** Weitz's ODE reproduces waves rising with T_H
(2, 2, 3, 3 at T_H = 7, 14, 21, 28) *under one specific prominence threshold*. The ABM does not
reproduce this under any threshold tested. ⚠️ **This claim is now known to be threshold-fragile
even at the ODE level — see D9.** The integration scheme (D1/E11) has been ruled out as the
cause (E12, disconfirmed). Root cause remains unknown.

**D9 — The wave-count metric is unsourced and threshold-fragile, even on the ODE.** Unlike
Weitz's symmetry coefficient (extracted from their Fig 1C), "count peaks with
`scipy.signal.find_peaks`" is not a method described in either source paper — it was introduced
in this project as an analytical convenience. [Fact] On the *same deterministic ODE curve*,
three reasonable, independently-chosen prominence thresholds give three different qualitative
answers: 5% of the global peak → rising 2,2,3,3 (this register's original citation); 10% of the
global peak → flat 2,2,2,2; 10% of each local peak's own height → rising 2,3,3,4. Consequence:
**no sourced, robust, quantitative definition of "number of oscillations" currently exists in
this project**, at either the ABM or the ODE level. Peak height and final susceptible fraction
remain the only metrics that have been robust throughout, and they carry no shape information.

**D10 — Test 2's δ(t) specification was wrong; corrected.** Originally specified as "raw death
count from the running simulation" — a tally of realized D-transitions (tried both lagged,
δ(t)=deaths(t−1), and same-day via a two-pass split). Measured at ~26% relative error (lagged)
and ~48% (same-day two-pass — worse, not better) against the ODE at N=100,000, 30 seeds, far
outside Test 2's 2% tolerance. Confirmed NOT a two-sided/Bernoulli artifact: a deterministic
`direct-g` version (no `q`, no per-agent draws, transmission multiplied by g(δ) directly, same
lagged δ) gave essentially the same wrong answer (0.392 vs the q-based 0.388, 5 seeds).
**Root cause:** Weitz's own model defines δ(t) = γ_H·H(t) — a continuous instantaneous rate from
the *current* H-compartment stock — not a discrete count of deaths that already happened.
Recomputing δ this way (from the running H count each sub-step, no lag) drops the deterministic
`direct-g` version's error to ~1.6% (5 seeds) — confirms the diagnosis. **Not yet closed:** even
with this fix, the actual two-sided `q` mechanism still shows a residual gap against the ODE —
see E16. Diagnostic script: `experiments/verify_meanfield_delta_bug.py`.

**D11 — D10's 5-seed `direct-g` number (~1.6%) does not hold at full scale; withdrawn.** Re-run
at N=100,000, 30/30 seeds, days=900 (C11): `direct-g` measures **4.56%**, not ~1.6%, a
statistically real gap (−7.11 SEMs), not sampling noise. [Fact] Since `direct-g` has no
per-agent stay-home draws at all — the only mechanism is `transmission_rate × g(δ) × I/N` with δ
computed exactly as the ODE defines it — this rules out the two-sided `q`/Bernoulli mechanism
*and* decision cadence as the sole cause of the residual gap (E16), because the deterministic,
mechanism-free variant fails by nearly as much as the two `q`-based variants (4.13%/5.91%).
[Speculation, low confidence — CONFIRMED, see C12] One candidate: δ_c=0.5 corresponds to a small
H-compartment stock (measured peak ~23 agents, C12), so early in an epidemic `g(δ)` is being
evaluated on small integer H counts where the ABM's discreteness diverges most from the ODE's
continuous H(t) — a Jensen's-gap-style effect (E[g(H)] ≠ g(E[H]) for nonlinear g under
population-level stochastic fluctuation in H, distinct from the sub-step time-discretisation
bias C9 already ruled out as the cause here). **C12's δ_c sweep (direct-g only, N=100,000, 30
seeds) confirms this directly: 4.56% error at δ_c=0.5 (peak H≈23) collapses to 0.10-0.80% at
δ_c=2.0/3.5/7.0 (peak H≈66-172), tracking the H-count scale, not δ_c per se.** Root cause of the
C11 residual is no longer open for `direct-g`. **Still undecided (per CLAUDE.md's working
conventions, reported not decided):** whether the two-sided `q` variants show the same collapse
at larger δ_c (not tested this round — C12 deliberately isolated `direct-g` alone), and what this
implies for Test 2's δ_c=0.5 baseline, its tolerance, or arm 1/2's operating δ_c — see E16.

**D12 — C16/C17's `direct-g` simplification is confirmed NOT a valid stand-in for CBF's real
mechanism.** [Fact, verified directly against `models/compartment_model_age_deaths.py` lines
74–147, the same repo already used for A20/C9/C13.] CBF is explicitly a **5-compartment** model
(S, S^B, E, I, R) — S^B is a genuine tracked stock, not a derived instantaneous quantity. Each of
the `daily_steps` sub-steps runs a proper **competing-hazards** split: from S, agents race between
"→E" (force of infection, full rate) and "→S^B" (adoption, `prob_S_to_SB`), drawn as one joint
binomial then split by relative hazard (source lines 114–118); from S^B, agents race between "→S"
(relaxation, `prob_SB_to_S = μ_B·(S+R)/N`) and "→E" (force of infection at the *reduced* rate
`r·β`) (lines 120–126). **Relaxation is driven by μ_B alone, essentially independent of the death
signal.** With Gozzi's own sourced μ_B=0.01/day (C13), the relaxation half-life is
`ln(2)/0.01≈69 days` — far slower than the disease's own timescale (latent+infectious≈8 days,
T_H=14 days). Cautious agents stay cautious long after deaths subside: genuine memory/hysteresis
that an instantaneous, memoryless multiplier `g(D)` structurally cannot reproduce. `direct-g` was
a fair match for **Weitz's** mechanism (whose own published ODE literally *is* a direct
multiplicative modulation, no separate compartment) — that does not carry over to CBF, which has
a real two-compartment structure Weitz's does not.

**What the correct version needs (not built):** an explicit S^B stock evolved sub-step-by-sub-step
alongside S/E/I/H/R/D, with `prob_S_to_SB(t) = β_B·(1−exp(−γ_beh·D(t)))` (adoption, driven by
whatever death signal — 28-day mean per C17, or otherwise) and `prob_SB_to_S(t) = μ_B·(S(t)+R(t))/N`
(relaxation, driven by a roughly constant rate, *not* the death signal), with competing-hazards
transitions at each sub-step exactly as Gozzi's code implements them.

**Consequence for C16/C17: those results remain valid AS TESTS OF THE SIMPLIFIED `direct-g`
FORMULA (methodologically consistent with C12's isolation approach), but they do NOT establish
whether the REAL two-compartment CBF mechanism is safe at N=10,000/30,000 (let alone N=3,000).**
S^B is itself a new stock subject to its own small-N discreteness questions (C12's own finding
applied to a different compartment), and the adoption/relaxation timescale mismatch could produce
dynamics (e.g. hysteresis across epidemic waves) a memoryless multiplier cannot exhibit in either
direction — untested, either way. **The requested C17-style test at N=3,000 was deliberately NOT
run this round**, since it would have rested on the same unconfirmed premise. Reported, not
fixed — building the real S/S^B mechanism is a modelling/implementation decision for the planning
chat, not made here.

**D13 — N=3,000 reaffirmed; C13's motivating concern for possibly needing a larger N is
resolved.** C13 raised the possibility that N=3,000 might be structurally too small for arm 1's
own count-based trigger to escape a small-count bias regime, independent of the specific rule or
parameter — potentially requiring a larger operating N to make arm 1 viable at all. C18-C20
answer this: the real CBF mechanism's ~4-6% gap against its mean-field reference is present at
N=3,000, 10,000, AND 30,000 alike (C18/C19) and does not shrink with N, so a larger N would not
have removed it — the effect C13 worried about (small S^B/H-type counts) is confirmed absent at
every N tested (C20), and the gap that does exist is N-independent. **A7 (N=3,000) is
reaffirmed, not revised** — there is no reason to trade N=3,000's original justification (C5's
response-gradation requirement, D3) for a larger, more expensive population; doing so buys
nothing against the one concern that motivated considering it.

**D14 — Data-correctness note: the symmetry-coefficient ODE values 0.48 (control) / 0.10
(awareness) are unverified; do not cite them.** These values, quoted in `Sourcing_Pack_v3.md`
(Referent metric section), `Scenario_Spec.md` §6 and earlier in this register, **could not be
reproduced by any code in this repo or by Weitz's own method** (C29). Fresh K1 values (Weitz
model B, k=2, Nδ_c=50, T_H=14, 600 days; C29) replace them:

| symmetry coefficient | incidence ctrl / beh | deaths ctrl / beh |
|---|---|---|
| `experiments/metrics.py` `sym_pt` (SA) | 0.841 / 0.432 | 0.264 / 0.171 |
| Weitz R-LOESS method, Python approximation (SB) | 1.321 / 0.147 | 1.443 / 0.170 |

SB approximates Weitz's R `loess` (R is not installed): a direct tricube local-quadratic fit, not
R's default interpolation surface, on a 0.1-day grid instead of 0.01. **Correction to a statement
made while planning C29:** "Weitz-LOESS is undefined on control incidence" was measured on
`metrics.py`'s own ODE (initial I=10⁻⁶, instantaneous rate rather than daily-integrated
incidence). On K1 as specified it is defined (1.321). That is itself evidence of how sensitive
this metric is to inputs that should be immaterial.

**D15 — Check 2(b)'s stated reference was not equivalent; corrected before running (C31).
ACCEPTED (planning chat, Max, 10 Oct 2026).** The
check as first specified said "a fixed 50% of susceptibles forced to stay home = ODE with β×0.5".
[Fact, computed from the ODE] Both start with the same growth rate (R_eff = 1.5), but they are
different systems: with β×0.5 every susceptible is exposed at half the rate; with 50% held home,
the exposed half meets the full rate and is depleted twice as fast per infection. Final S: β×0.5
0.41708; 50% home 0.70840. The final-size equation for the exposed half is the same as for β×0.5
(s = exp(−1.5(1 − s))), so the exposed half ends at 0.417 of its size and total S = 0.5 + 0.5 ×
0.417. Fourth instance of the CLAUDE.md "simplified stand-in" pattern, caught here before a run.
Also: in (c) R_eff = 1.0 exactly, so the ODE final S depends on the initial condition (0.99989 at
I(0)=10⁻⁶, 0.99062 at I(0)=10/N); the ABM's I(0)=10/N is used.

**D16 — Data correction: the combinatorial state-space figure is ~5.2 × 10⁵, not ~4.6 × 10⁵.**
Design_Spec §5's product of its own bin counts is 10 × 3 × 3 × 3 × 8 × 6 × 10 × 4 = 518,400
(computed). The "about 4.6 × 10⁵" printed there, and quoted in D4, was wrong. Corrected in
Design_Spec §5. Nothing depended on it: D4's conclusion (the space is comparable to the
~5.4 × 10⁵ decision count, so caching may save little) holds either way, and the realised
state count is measured separately (C15, E3).

## E. Open items

| # | Item | Blocks |
|---|---|---|
| E1 | Arm-2 budget at N=3,000 — 1.62M calls at p=0.3, 810k weekly, 540k weekly with 2 scenarios. ⚠️ These counts assume all 3,000 agents decide every day; since A38/A42 only never-ill agents decide (and with E19 none after E+I = 0), they are upper bounds and need recounting | arm 2 |
| E2 | Re-decision cadence sweep, p ∈ {0.1, 0.3, 1}/day. **Updated by A41:** run with **arm 3** once built, NOT in arm 1 and NOT with a stand-in rule (arm 1 keeps CBF's continuous rates and has no cadence) | E1 |
| E3 | Realised state count from arm 1 logs. **First read with a stand-in rule (C15, not real CBF): 3,040-3,364 distinct states out of millions of decisions (ratio ~0.0002-0.0006, ~1,768-5,869x compression) at N=10,000/30,000** — one seed, hand-picked bins, not yet with the real CBF rule or at N=3,000. **The option to build caching exists and looks promising on this first read, but whether to build it is Max's call, not a Claude Code decision — noted here, not acted on** | caching decision (Max's) |
| E4 | Re-measure C3 scenario separation with CBF at N=3,000 | scenario spec |
| E5 | **ANSWERED — yes.** See C7. N=3,000 + 28-day window adopted | closed |
| E11 | `experiments/abm.py` uses a single daily step with raw-rate transitions, contradicting A20 | correctness of the delay kernel |
| E12 | **DISCONFIRMED** — see D9/G3. Switching to 12 sub-steps did not change the T_H → wave-count direction under either definition | closed as a candidate cause; D6 itself remains open |
| E13 | **RESOLVED → A47** (`deaths_28day_mean_7d_ago`, 7-day horizon, unsourced) | closed |
| E14 | Find a sourced, robust way to quantify "number of oscillations" — or drop oscillation as a target signature entirely and rely solely on peak-height reduction / final-S shift from control (both robust throughout) | shape metric, stated project contribution |
| E15 | **RESOLVED — see C9/A20-rev.** Bias confirmed (not a bug); 48 substeps adopted | closed |
| E16 | **Root cause of the C11 residual identified for `direct-g` (C12): small H-compartment stock at δ_c=0.5 (peak H≈23 agents) produces a Jensen's-gap-style bias that vanishes at larger δ_c (0.10-0.80% error at δ_c=2.0/3.5/7.0, vs 4.56% at 0.5).** Not yet resolved for the actual `q`-based variants: continuous-q (4.13%) and daily-q (5.91%) at δ_c=0.5 have NOT been re-swept across δ_c (C12 deliberately isolated `direct-g` only, one variable at a time) — it is not yet confirmed the same collapse happens once per-agent stochastic draws are added back in. Open questions for the planning chat: (a) does the `q`-mechanism residual also collapse at larger δ_c, or does the Bernoulli draw add its own scale-dependent bias on top; (b) Test 2's actual δ_c=0.5 comes from rescaling Weitz's N·δ_c=50 down to N=100,000 — if small-N/small-δ_c is intrinsically biased, does that indict the rescaling approach itself, or only this validation test's choice of N; (c) what cadence to adopt for arm 1 given neither has been shown to close the gap at the production δ_c; (d) whether Test 2's stated 2% tolerance is still the right gate; (e) **C13's higher-priority finding: at N=3,000 (arm 1's actual population, not Test 2's N=100,000), the raw counts behind EITHER Weitz's H-stock or CBF's own γ_beh/daily-deaths trigger are already at or below the "broken" scale even with behaviour off — this may not be a δ_c/γ_beh tuning problem at all, but an N=3,000 problem that affects arm 1 directly, not just this validation test** | Test 2 closure; E2; arm 1 cadence choice; **arm 1 viability at N=3,000 (C13); N=30,000 tested for the real CBF mechanism and found NOT safe except at weak-behaviour settings when using Gozzi's literal yesterday-count signal (C16) — but IS statistically clean at both N=10,000 and N=30,000 (gap <2 SEMs) once the project's own actual 28-day-mean signal is used instead, at Gozzi's own unmodified γ_beh (C17). N=3,000 itself still untested under C17's configuration. **D12: C16/C17 both used a `direct-g` simplification now confirmed NOT a valid stand-in for CBF's real 5-compartment, memory-laden mechanism — their results stand only as tests of that simplified formula, not of arm 1's actual planned dynamics; the N=3,000 test was withheld pending this** |
| E6 | **CLOSED → A66** (pilot C34–C37; template frozen as v1). Prompt wording and anchoring scheme; pilot before full arm-2 run. **Pilot plan (planning chat, Oct 2026):** about 10 sample situations — before the epidemic, rising, peak, falling; young and old — run BEFORE the prompt is frozen. **Pass criteria — APPROVED (A62):** (i) more caution at peak deaths than before the epidemic; (ii) older or more vulnerable agents are at least as cautious, all else equal; (iii) at the same death level, rising deaths give at least as much caution as falling; (iv) valid output every time. **The pilot is never judged on epidemic outcomes** (flattening, stretch). Draft template: `prompts/DRAFT_arm2_arm3.md` (not frozen) | arm 2; arm 3 (A49) |
| E7 | Persona layer — may be redundant given the sourced population construction | diversity metric |
| E8 | Gozzi SI prior ranges for β_B, μ_B, γ_beh (per-city posteriors, no canonical value) — confirmed directly against source (C13): no calibrated value exists anywhere in the repo, only the authors' own uncalibrated demo default (β_B=0.5, μ_B=0.01, r=0.5, γ_beh=1). C13 additionally finds this demo value implies a sub-single-digit death-count trigger even at the authors' own Madrid scale, before any rescaling | arm 1 calibration; Test 2 (E16) |
| E9 | Whether the ABM/ODE oscillation discrepancy (D6) indicates a simulator defect | milestone 2 |
| E10 | Contamination experiment: named vs unnamed disease, decision-level agreement | arm 2 writeup |
| E17 | **BUILT, TESTED, AND CLOSED — see C18/C19/C20.** `src/model.py`'s `run_cbf_behaviour` implements the real S/S^B two-compartment mechanism (adoption + relaxation, competing hazards). The ~4-6% relative-error gap against a sanity-checked DDE reference (N=3,000/10,000/30,000, 30 then 90 seeds) is confirmed real, N-independent, not a small-S^B-count artifact, and not a coding bug — adopted as a documented, accepted limitation (C20) rather than pursued further | closed |
| E19 | **ADOPTED → A55** (arm 2 stops LLM calls once E + I = 0) | closed |
| E20 | **RESOLVED → A42** (recovered agents do not decide; act normal). Consequence A43 (own_health dropped from the main-design vector) | closed |
| E21 | **Planned measured extension (A45), a reported result, not a side note:** once arm 3 exists, run it with and without ill agents deciding. **Variant A:** ill agents may decide; if an ill agent stays home, it neither catches nor SPREADS (two-sided, as A23), so staying home then stops transmission from that agent. Report the difference (variant A − main design, paired seeds) in stretch factor, peak reduction and final S. Needs own_health back in the vector (A43). Code-change estimate in C31's report. Open for variant A, to decide before building it: whether a newly ill agent keeps its last action or starts normal until re-asked (at p = 0.3/day that is ~3.3 days of a 6-day infectious period), and whether precautions reduce an ill agent's infectiousness | arm 3; the stated contribution |
| E22 | **RESOLVED → A48** (CBF's exact value; wording "About X% of people in your town are going about their lives normally."; undercounts) | closed |
| E23 | **Open: plateau reachability under stay home is shown by arithmetic only, not yet by a run.** With stay home ×0 on own susceptibility, effective R = R₀ × (share of susceptibles not at home) when the rest act normal, so at R₀ = 3 holding R ≤ 1 needs a stay-home share > 2/3 (A37's reason). No run has yet shown an epidemic plateau produced this way. C31 Check 2(b) tested a FIXED 50% at home (below 2/3), not a plateau | the Weitz signature being reachable at all in S1/S3 |
| E24 | **PROPOSED, report-only measure, for supervisor approval: "death responsiveness".** (a) Per run: the correlation over time between the population's mean caution among deciding agents and `deaths_28day_mean`, over the days while E + I > 0. (b) For any rule (arm 1, each arm-3 rule, arm 2 via its pilot answers): its caution curve across 4-week deaths 0 / 3 / 12 / 50 / 100 for the young (band 2) and old (band 8) pilot agents, on C37's situations. Caution = 1 − P(normal). **Open points filled (Max, 10 Oct 2026, before any arm-3 run):** Spearman rank correlation; caution = the REALISED share of deciding agents (never-ill and alive: S or E) whose action is stay_home or precautions; lag 0; days while E + I > 0; for arm 1, the share in S^B among the same agents (S^B / (S + E); CBF has no cautious E state, so arm 1's E agents never count as cautious, whereas arm 3's E agents count by their realised action — recorded asymmetry). *Implementation (C39):* per run, day t pairs `deaths_28day_mean` at the start of day t (the world's awareness signal) with the caution share at the end of day t, over the days t whose end-of-day E + I > 0; undefined if either series is constant on those days (count reported). Not a pass mark; not used to select or discard anything | [Proposal, planning chat (Max), 10 Oct 2026] Motivation: C35–C37 |
| E18 | **CLOSED — see C20.** The ~4-6% gap between the real CBF mechanism and its mean-field DDE reference is accepted as a documented, N-independent limitation of the ABM-vs-mean-field comparison, not chased further with more seeds, more N, or mechanism audits. (Whether it is mechanistically the same phenomenon as E16's separate Weitz-mechanism residual remains an open curiosity, not pursued — E16 itself stays open, it concerns Test 2/Weitz's own rule, not arm 1's CBF) | closed |

## F. Known limitations of everything measured above

- All ABM results are **well-mixed**; no clustered network has been tested.
- Seed counts are 8–30 depending on the run; none are large.
- C3 used the Weitz reference rule, not CBF.
- The 7-day awareness window was not re-tested under the real CBF mechanism. N=3,000 was
  originally justified with it (C5/C7); A30 re-checks N only with the 28-day window.
- E9 remains unresolved: the ABM does not reproduce the ODE's T_H → oscillation relationship,
  and it is not yet known whether this is a metric problem or a simulator defect.
- **Ill agents' isolation is omitted from the main design (A38/A45).** It is probably the most
  important real-world protective behaviour, so the main design likely UNDERSTATES how much
  behaviour can flatten an epidemic. The two source models omit it too: Gozzi's CBF acts on
  healthy (susceptible) agents only, and Weitz's model is population-level with no individuals.
  E21 measures the size of the omission for arm 3.

---

## G. Build-phase state

Repo `fyp-abm` (GitHub). Layout: `docs/` · `src/` · `tests/` · `experiments/` · `results/` ·
`CLAUDE.md` · `requirements.txt` · `.gitignore`.

| Item | State |
|---|---|
| Verification Test 1 — ODE convergence | ✅ **CLOSED.** `tests/test_ode_convergence.py`, repointed to `src/model.py` (G2 resolved), 30/30 seeds, N=100,000, behaviour off, 1% relative tolerance (G1 resolved). Measured: mean final S=0.05926 vs ODE 0.05952, 0.431% relative error. See C10 |
| Verification Test 2 — mean-field recovery | ❌ **BLOCKED, not passing.** δ fix (D10) now applied in `src/model.py`'s `run_weitz_behaviour` (continuous, per-sub-step, zero-lag) and re-tested at full N=100,000/30 seeds (C11): 4.13% relative error for the actual (continuous-q) implementation, still outside the file's stated 2% tolerance. The deterministic sanity variant also fails at this scale (4.56%, D11) — the residual is not fully explained by cadence or the two-sided mechanism. Root cause of the remaining ~4-6% gap is open (E16) |
| Verification Test 3 — renderer totality | ❌ cannot exist — no `Perception` dataclass or renderer yet |
| `src/` | `model.py` — SEIR+H disease dynamics, behaviour off (`run`, Test 1); Weitz's own behaviour rule for simulator validation (`run_weitz_behaviour`, Test 2, A4/A19/A23); and arm 1's real CBF mechanism (`run_cbf_behaviour`, S/S^B compartments with competing hazards, C18/E17), now with per-agent heterogeneity in `r` via `cbf_r_from_response_efficacy` (C21). `perception.py` — the `Perception` dataclass (shape only, no renderer/computation yet). `population.py` — quota-drawn `Population` construction at N=3,000, `build_population` (age_band/vulnerability sourced and derived; occupation_flex/response_efficacy configurable free Beta draws) |
| `experiments/abm.py` | validated pilot; **contradicts A20** — single daily step with raw-rate transitions rather than 12 sub-steps. Untouched throughout the `src/model.py` build |
| `experiments/metrics.py` | shape-metric exploration; computes the symmetry coefficient, which D7/D8 show is unreliable. Do not build on it |
| `experiments/verify_substep_bias.py`, `verify_substep_scheme.py`, `verify_meanfield_delta_bug.py` | diagnostic scripts kept alongside the pilot, not part of `src/` — back C9, D9/G3, and D10 respectively |

**G1 — Tolerance note. RESOLVED.** Test 1 used 2% relative tolerance against CLAUDE.md's stated
"three decimals" while it guarded the pilot. Tightened to 1% when repointed to `src/model.py`
(C10) — measured at 0.431% relative error, comfortably inside it.

**G2 — Test 1 currently guards a pilot script, not the model. RESOLVED.** Repointed to
`src/model.py` (C10); the suite now validates the code that is actually run.

**G3 — [DISCONFIRMED, measured].** Switching to 12 sub-steps/day (A20's mandated scheme) did
not change the T_H → wave-count direction under either counting convention tested (prominence
relative to the run's global peak, or to each local peak's own height). Wave counts stayed
flat/noisy (~1.0–2.2) across T_H ∈ {7,14,21,28} under both the old and new integration schemes,
20/20 seeds, N=3,000. The wrong dwell-time distribution (D1/E11) is ruled out as the explanation
for D6. A20 still stands on its own merits — it matches Gozzi's published implementation and
gives the correct dwell-time distribution shape — independent of whether it explains D6. See D9
for why D6's own ODE reference is now in question too.

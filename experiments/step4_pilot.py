"""
Pilot of the arm-2/arm-3 prompt (register E6, criteria A62, settings A65). First LLM use.

Modes (run in this order; each step is recorded in the register before the next):
  --situations  build the 10 pilot situations from ONE arm-1 run (S1, seed 0, shared world) and
                print them; no API call.
  --count       token-counting endpoint on the rendered prompts (no generation).
  --run         3 calls per situation with thinking OFF (A65) + 1 with thinking ON (comparison).
  --score       score criteria (i)-(iv) on the thinking-OFF replies.

Template: read verbatim from prompts/DRAFT_arm2_arm3.md (first code block) and checked equal to
the renderer's TEMPLATE in experiments/step4_prompt_tokens.py. The API key is read by the SDK
from the environment and is never printed or logged.
"""
import json
import math
import os
import re
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))
sys.path.insert(0, HERE)
from perception import Perception  # noqa: E402
from population import build_population  # noqa: E402
from shared_world import CBFArm1, run_shared_world  # noqa: E402
import step4_prompt_tokens as rt  # noqa: E402

OUT = os.path.join(HERE, "..", "results", "step4")
SIT_FILE = os.path.join(OUT, "pilot_situations.json")
REPLY_FILE = os.path.join(OUT, "pilot_replies.json")
MODEL = "claude-haiku-5-5"                     # A63
PRICE_IN, PRICE_OUT = 0.10e-6, 0.50e-6         # $ per token, standard API, prompts <= 100k (A63)
COST_CAP = 2.00                                # $ for this task
N_OFF, N_ON = 3, 1
MAX_TOKENS_OFF, MAX_TOKENS_ON = 1024, 16000    # A65
REPLY_RE = re.compile(r"^\s*A\s*=\s*(\d+)\s*,\s*B\s*=\s*(\d+)\s*,\s*C\s*=\s*(\d+)\s*$")
YOUNG_BAND, OLD_BAND = 2, 8


def template_from_md():
    s = open(os.path.join(HERE, "..", "prompts", "DRAFT_arm2_arm3.md"), encoding="utf-8").read()
    block = re.findall(r"```\n(.*?)\n```", s, re.S)[0]
    assert block == rt.TEMPLATE, "renderer TEMPLATE differs from prompts/DRAFT_arm2_arm3.md"
    return block


def build_situations():
    pop = build_population(N=3000, seed=0)
    out = run_shared_world(N=3000, seed=0, decision=CBFArm1(), days=600, R0=3.0, T_H=14.0,
                           f_D=pop.vulnerability, window=28, detection_rate=0.7)
    sig, rep = out["awareness_signal"], out["reported_deaths"]
    s6 = np.round(sig, 6)                     # signal moves in steps of 0.7/28 = 0.025
    peak = int(np.argmax(s6))                 # first day the maximum is reached
    smax = float(s6[peak])
    rising_25 = int(np.flatnonzero(s6[:peak] >= 0.25 * smax)[0])
    # Matched level for criterion (iii): among levels taken both before and after the peak, the
    # one nearest 50% of the peak (ties -> the lower level); first day at it on each side.
    both = sorted(set(s6[1:peak]) & set(s6[peak + 1:]) - {0.0})
    level = min(both, key=lambda v: (abs(v - 0.5 * smax), v))
    rising = int(np.flatnonzero(s6[:peak] == level)[0])
    falling = peak + int(np.flatnonzero(s6[peak:] == level)[0])
    days = {"before": 0, "early_rising": rising_25, "rising": rising, "peak": peak,
            "falling": falling}

    # The first young agent (band 2) of the frozen population; its occupation_flex and
    # response_efficacy are used for BOTH members of every pair, so each pair differs only in
    # age band and vulnerability. (No band-2 agent has occupation_flex >= 0.95, so the old
    # member's occupation_flex departs from its band's fixed 1.0.)
    young = int(np.flatnonzero(pop.age_band == YOUNG_BAND)[0])
    occ, eff = float(pop.occupation_flex[young]), float(pop.response_efficacy[young])
    sits = []
    for phase, d in days.items():
        for who, band in (("young", YOUNG_BAND), ("old", OLD_BAND)):
            fields = dict(
                deaths_28day_mean=float(sig[d]),
                deaths_cumulative=float(rep[:d].sum()),
                deaths_28day_mean_7d_ago=float(sig[d - 7]) if d >= 7 else 0.0,   # A58
                current_action="normal",
                social_norm=float(out["social_norm"][d]),
                age_band=band,
                vulnerability=float(pop.vulnerability[pop.age_band == band][0]),
                occupation_flex=occ, response_efficacy=eff,
                population=3000, day=int(d))
            p = Perception(**fields)
            sits.append(dict(id=f"{phase}_{who}", phase=phase, who=who, fields=fields,
                             prompt=rt.render(p)))
    meta = dict(run="arm 1 (CBFArm1), S1, seed 0, shared world, foundation", days=days,
                peak_signal=smax, rising_level=level, young_agent_index=young,
                occupation_flex=occ, response_efficacy=eff)
    return meta, sits


def parse(text):
    m = REPLY_RE.match(text or "")
    if not m:
        return None
    a, b, c = (int(x) for x in m.groups())
    tot = a + b + c
    if not 98 <= tot <= 102 or tot == 0:                                 # A64
        return None
    return dict(stay_home=a / tot, precautions=b / tot, normal=c / tot, raw=[a, b, c], sum=tot)


def call(client, prompt, thinking_on):
    kw = dict(model=MODEL, messages=[{"role": "user", "content": prompt}])
    if thinking_on:
        kw.update(max_tokens=MAX_TOKENS_ON, thinking={"type": "adaptive"})
    else:
        kw.update(max_tokens=MAX_TOKENS_OFF, thinking={"type": "disabled"})
    r = client.messages.create(**kw)
    text = "".join(b.text for b in r.content if b.type == "text")
    n_thinking_blocks = sum(1 for b in r.content if b.type == "thinking")
    usage = r.usage.to_dict() if hasattr(r.usage, "to_dict") else dict(r.usage)
    return dict(text=text, stop_reason=r.stop_reason, n_thinking_blocks=n_thinking_blocks,
                usage=usage, model=r.model, request_id=getattr(r, "_request_id", None))


def ask(client, prompt, thinking_on, spent):
    """One decision: up to 1 + 2 retries (A61). Returns the record and the cost."""
    attempts = []
    for k in range(3):
        a = call(client, prompt, thinking_on)
        a["parsed"] = parse(a["text"])
        a["cost"] = a["usage"]["input_tokens"] * PRICE_IN + a["usage"]["output_tokens"] * PRICE_OUT
        attempts.append(a)
        spent += a["cost"]
        if spent > COST_CAP:
            raise RuntimeError(f"cost cap ${COST_CAP} exceeded (${spent:.4f})")
        if a["parsed"] is not None:
            break
    final = attempts[-1]["parsed"]
    return dict(attempts=attempts, valid_first=attempts[0]["parsed"] is not None,
                retries=len(attempts) - 1, final=final, fallback=final is None,
                cost=sum(a["cost"] for a in attempts)), spent


def main():
    os.makedirs(OUT, exist_ok=True)
    template_from_md()
    if "--score" in sys.argv:
        score()
        return
    if "--situations" in sys.argv:
        meta, sits = build_situations()
        json.dump(dict(meta=meta, situations=sits), open(SIT_FILE, "w"), indent=2)
        print(json.dumps(meta, indent=2))
        for s in sits:
            f = s["fields"]
            print(f"{s['id']:20s} day {f['day']:3d} d28 {f['deaths_28day_mean']:.4f} "
                  f"d28_7ago {f['deaths_28day_mean_7d_ago']:.4f} cum {f['deaths_cumulative']:.1f} "
                  f"norm {f['social_norm']:.4f} band {f['age_band']} vul {f['vulnerability']} "
                  f"occ {f['occupation_flex']:.4f} eff {f['response_efficacy']:.4f} "
                  f"action {f['current_action']}")
        print("\n--- rendered:", sits[5]["id"], "\n" + sits[5]["prompt"])
        return

    import anthropic
    client = anthropic.Anthropic()
    sits = json.load(open(SIT_FILE))["situations"]

    if "--count" in sys.argv:
        counts = {}
        for s in sits:
            r = client.messages.count_tokens(
                model=MODEL, messages=[{"role": "user", "content": s["prompt"]}],
                thinking={"type": "disabled"})
            counts[s["id"]] = dict(input_tokens=r.input_tokens, chars=len(s["prompt"]),
                                   words=len(s["prompt"].split()))
            print(f"{s['id']:20s} {r.input_tokens} input tokens ({len(s['prompt'])} chars, "
                  f"{len(s['prompt'].split())} words)")
        json.dump(counts, open(os.path.join(OUT, "pilot_token_counts.json"), "w"), indent=2)
        return

    if "--run" in sys.argv:
        spent, t0 = 0.0, time.time()
        res = {}
        for s in sits:
            res[s["id"]] = dict(off=[], on=[])
            for _ in range(N_OFF):
                rec, spent = ask(client, s["prompt"], False, spent)
                res[s["id"]]["off"].append(rec)
            for _ in range(N_ON):
                rec, spent = ask(client, s["prompt"], True, spent)
                res[s["id"]]["on"].append(rec)
            print(f"{s['id']:20s} done; spent so far ${spent:.5f}", flush=True)
        json.dump(dict(model=MODEL, spent=spent, wall_s=time.time() - t0, replies=res),
                  open(REPLY_FILE, "w"), indent=2)
        print(f"total spent ${spent:.5f} in {time.time() - t0:.0f}s")
        return


def score():
    """C34's pre-registered scoring. Caution c = 1 - P(normal), mean over valid OFF replies."""
    d = json.load(open(REPLY_FILE))
    rep, order = d["replies"], [s["id"] for s in json.load(open(SIT_FILE))["situations"]]
    print("Every reply (attempt-level): id | mode | k | text | valid | stop | in/out tokens | cost")
    for sid in order:
        for mode in ("off", "on"):
            for k, rec in enumerate(rep[sid][mode]):
                for j, a in enumerate(rec["attempts"]):
                    u = a["usage"]
                    print(f"  {sid:20s} {mode:3s} {k}.{j} {a['text']!r:28s} "
                          f"{'valid' if a['parsed'] else 'INVALID'} {a['stop_reason']} "
                          f"{u['input_tokens']}/{u['output_tokens']} ${a['cost']:.6f} "
                          f"thinking_blocks={a['n_thinking_blocks']}")
    stats = {}
    for sid in order:
        for mode in ("off", "on"):
            ps = [r["final"] for r in rep[sid][mode] if r["final"]]
            c = [1 - p["normal"] for p in ps]
            sh = [p["stay_home"] for p in ps]
            stats[(sid, mode)] = dict(c=float(np.mean(c)) if c else np.nan,
                                      c_sd=float(np.std(c, ddof=1)) if len(c) > 1 else np.nan,
                                      stay=float(np.mean(sh)) if sh else np.nan,
                                      n=len(ps), N=len(rep[sid][mode]))
    print("\nPer situation, thinking OFF (mean over valid replies) | thinking ON:")
    for sid in order:
        o, n = stats[(sid, "off")], stats[(sid, "on")]
        print(f"  {sid:20s} OFF c={o['c']:.3f} (sd {o['c_sd']:.3f}) P(stay)={o['stay']:.3f} "
              f"n={o['n']}/{o['N']} | ON c={n['c']:.3f} P(stay)={n['stay']:.3f} n={n['n']}/{n['N']}")
    c = {sid: stats[(sid, "off")]["c"] for sid in order}
    res = {}
    res["i"] = all(c[f"peak_{w}"] > c[f"before_{w}"] for w in ("young", "old"))
    res["ii"] = all(c[f"{ph}_old"] >= c[f"{ph}_young"]
                    for ph in ("before", "early_rising", "rising", "peak", "falling"))
    res["iii"] = all(c[f"rising_{w}"] >= c[f"falling_{w}"] for w in ("young", "old"))
    first = [r["valid_first"] for sid in order for r in rep[sid]["off"]]
    res["iv"] = all(first)
    print(f"\n(i) {res['i']}  (ii) {res['ii']}  (iii) {res['iii']}  (iv) {res['iv']} "
          f"({sum(first)}/{len(first)} OFF valid at first attempt)")
    allrecs = [r for sid in order for m in ("off", "on") for r in rep[sid][m]]
    atts = [a for r in allrecs for a in r["attempts"]]
    for mode in ("off", "on"):
        aa = [a for sid in order for r in rep[sid][mode] for a in r["attempts"]]
        print(f"{mode}: attempts {len(aa)}, input tokens {sum(a['usage']['input_tokens'] for a in aa)}"
              f" (per call {min(a['usage']['input_tokens'] for a in aa)}-"
              f"{max(a['usage']['input_tokens'] for a in aa)}), output tokens "
              f"{sum(a['usage']['output_tokens'] for a in aa)} (per call "
              f"{min(a['usage']['output_tokens'] for a in aa)}-{max(a['usage']['output_tokens'] for a in aa)}),"
              f" cost ${sum(a['cost'] for a in aa):.5f}")
    print(f"all: {len(allrecs)} decisions, {len(atts)} attempts, retries "
          f"{sum(r['retries'] for r in allrecs)}, fallbacks {sum(r['fallback'] for r in allrecs)}, "
          f"cost ${sum(a['cost'] for a in atts):.5f}")
    print("usage keys seen:", sorted({k for a in atts for k in a["usage"]}))
    json.dump(dict(stats={f"{k[0]}|{k[1]}": v for k, v in stats.items()}, criteria=res),
              open(os.path.join(OUT, "pilot_scores.json"), "w"), indent=2)


if __name__ == "__main__":
    main()

"""
Pilot v2 of the arm-2 prompt: controlled situations, ONE field changed at a time (register C35).
Thinking OFF only, settings A65, template unchanged (prompts/DRAFT_arm2_arm3.md).

Base: day 60; social_norm 0.85; flat deaths (4-week total a week ago = 4-week total now);
deaths_cumulative = 4-week total + 5; current_action normal. Young (band 2) and old (band 8),
both with C34's occupation_flex and response_efficacy.
  Test D: 4-week total in {0, 1, 3, 6, 12, 25, 50, 100}.
  Test T: 4-week total 12; 4-week total a week ago in {4, 12, 25}.
  Test N: 4-week total 12; social_norm in {0.50, 0.70, 0.90}.
  Supplementary T25c: as T with week-ago total 25 but deaths_cumulative 30 (= 25 + 5), because
  T's week-ago total 25 exceeds T's cumulative 17 (an impossible combination).

Modes: --situations (no API call), --run (3 thinking-OFF calls each), --score.
"""
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))
sys.path.insert(0, HERE)
from perception import Perception  # noqa: E402
from population import build_population  # noqa: E402
import step4_prompt_tokens as rt  # noqa: E402
import step4_pilot as v1  # noqa: E402

OUT = v1.OUT
SIT_FILE = os.path.join(OUT, "pilot_v2_situations.json")
REPLY_FILE = os.path.join(OUT, "pilot_v2_replies.json")
N_REP = 3
DAY, NORM = 60, 0.85
D_LEVELS = [0, 1, 3, 6, 12, 25, 50, 100]
T_EARLIER = [4, 12, 25]
N_LEVELS = [0.50, 0.70, 0.90]


def situation(test, level, who, band, total, earlier, norm, cum, vul, occ, eff):
    fields = dict(deaths_28day_mean=total / 28, deaths_cumulative=float(cum),
                  deaths_28day_mean_7d_ago=earlier / 28, current_action="normal",
                  social_norm=norm, age_band=band, vulnerability=vul,
                  occupation_flex=occ, response_efficacy=eff, population=3000, day=DAY)
    return dict(id=f"{test}{level}_{who}", test=test, level=level, who=who, fields=fields,
                prompt=rt.render(Perception(**fields)))


def build_situations():
    pop = build_population(N=3000, seed=0)
    c34 = json.load(open(v1.SIT_FILE))["meta"]
    occ, eff = c34["occupation_flex"], c34["response_efficacy"]
    sits = []
    for who, band in (("young", v1.YOUNG_BAND), ("old", v1.OLD_BAND)):
        vul = float(pop.vulnerability[pop.age_band == band][0])
        a = dict(who=who, band=band, vul=vul, occ=occ, eff=eff)
        for d in D_LEVELS:
            sits.append(situation("D", d, total=d, earlier=d, norm=NORM, cum=d + 5, **a))
        for e in T_EARLIER:
            sits.append(situation("T", e, total=12, earlier=e, norm=NORM, cum=17, **a))
        for n in N_LEVELS:
            sits.append(situation("N", int(round(100 * n)), total=12, earlier=12, norm=n,
                                  cum=17, **a))
        sits.append(situation("T25c", "", total=12, earlier=25, norm=NORM, cum=30, **a))
    return dict(occupation_flex=occ, response_efficacy=eff, day=DAY), sits


def main():
    os.makedirs(OUT, exist_ok=True)
    v1.template_from_md()
    if "--situations" in sys.argv:
        meta, sits = build_situations()
        json.dump(dict(meta=meta, situations=sits), open(SIT_FILE, "w"), indent=2)
        print(json.dumps(meta))
        for s in sits:
            lines = s["prompt"].split("\n")
            print(f"{s['id']:12s} | {lines[2]} | {lines[4]} | {lines[6][:60]}")
        print("\n--- rendered:", sits[4]["id"], "\n" + sits[4]["prompt"])
        print(f"\n{len(sits)} situations x {N_REP} = {len(sits) * N_REP} decisions")
        return
    if "--score" in sys.argv:
        score()
        return
    if "--run" in sys.argv:
        import anthropic
        client = anthropic.Anthropic()
        sits = json.load(open(SIT_FILE))["situations"]
        spent, t0, res = 0.0, time.time(), {}
        for s in sits:
            res[s["id"]] = []
            for _ in range(N_REP):
                rec, spent = v1.ask(client, s["prompt"], False, spent)
                res[s["id"]].append(rec)
            print(f"{s['id']:12s} done; spent so far ${spent:.5f}", flush=True)
        json.dump(dict(model=v1.MODEL, spent=spent, wall_s=time.time() - t0, replies=res),
                  open(REPLY_FILE, "w"), indent=2)
        print(f"total spent ${spent:.5f} in {time.time() - t0:.0f}s")


def score():
    rep = json.load(open(REPLY_FILE))["replies"]
    sits = json.load(open(SIT_FILE))["situations"]
    stats = {}
    print("id | replies (A/B/C) | c mean (sd) | P(stay) mean (sd) | n valid | retries")
    for s in sits:
        recs = rep[s["id"]]
        ps = [r["final"] for r in recs if r["final"]]
        c = [1 - p["normal"] for p in ps]
        sh = [p["stay_home"] for p in ps]
        st = dict(c=float(np.mean(c)), c_sd=float(np.std(c, ddof=1)),
                  stay=float(np.mean(sh)), stay_sd=float(np.std(sh, ddof=1)),
                  n=len(ps), N=len(recs), retries=sum(r["retries"] for r in recs),
                  raw=[r["final"]["raw"] if r["final"] else None for r in recs])
        stats[s["id"]] = st
        print(f"{s['id']:12s} {' '.join('/'.join(map(str, x)) for x in st['raw']):30s} "
              f"{st['c']:.3f} ({st['c_sd']:.3f})  {st['stay']:.3f} ({st['stay_sd']:.3f})  "
              f"{st['n']}/{st['N']}  {st['retries']}")
    atts = [a for recs in rep.values() for r in recs for a in r["attempts"]]
    print(f"decisions {sum(len(v) for v in rep.values())}, attempts {len(atts)}, valid first "
          f"{sum(r['valid_first'] for v in rep.values() for r in v)}, fallbacks "
          f"{sum(r['fallback'] for v in rep.values() for r in v)}, input tokens "
          f"{min(a['usage']['input_tokens'] for a in atts)}-{max(a['usage']['input_tokens'] for a in atts)}"
          f", output {min(a['usage']['output_tokens'] for a in atts)}-"
          f"{max(a['usage']['output_tokens'] for a in atts)}, cost ${sum(a['cost'] for a in atts):.5f}")
    json.dump(stats, open(os.path.join(OUT, "pilot_v2_scores.json"), "w"), indent=2)


if __name__ == "__main__":
    main()

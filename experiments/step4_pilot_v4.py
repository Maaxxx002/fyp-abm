"""
Pilot v4 of the arm-2 prompt: three wordings on internally consistent situations (register C37).
Haiku 5.5, A65 settings (thinking OFF). The frozen template is not edited: W2 and W3 are made
by modifying the RENDERED W1 prompt at fixed anchors (asserted).

Death history (construction rule, C37): day 60; deaths fall only in days 25-60, in three
segments with a constant daily rate within each: a = days 25-31, b = days 32-52, c = days 53-59
(the 4-week total now = b + c; the 4-week total up to a week ago = a + b; cumulative = a + b + c).
  D (flat, X in {0, 3, 12, 50, 100}): constant rate X/28 per day -> a = c = X/4, b = 3X/4,
      cumulative 1.25 X.
  T rising:  a, b, c = 1, 3, 9   (earlier 4, now 12, cumulative 13).
  T falling: a, b, c = 15, 10, 2 (earlier 25, now 12, cumulative 27).
social_norm 0.85, current_action normal, C34/C35 agents (young band 2, old band 8).

  W1: template unchanged.
  W2: W1 + W2_LINE on its own line directly after the deaths paragraph (omitted when the
      4-week total is 0); k = population / 4-week total, rounded half-up.
  W3: W1 with its last two lines (answer instructions) replaced by W3_INSTR; reply = three
      whole numbers summing to 10 (W3_RE), probabilities = numbers / 10.

Modes: --situations, --count, --run, --score.
"""
import json
import os
import re
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))
sys.path.insert(0, HERE)
from population import build_population  # noqa: E402
import step4_prompt_tokens as rt  # noqa: E402
import step4_pilot as v1  # noqa: E402
import step4_pilot_v2 as v2  # noqa: E402
from step4_pilot_v3 import PCT_INSTR  # noqa: E402

OUT = v1.OUT
SIT_FILE = os.path.join(OUT, "pilot_v4_situations.json")
REPLY_FILE = os.path.join(OUT, "pilot_v4_replies.json")
N_REP = 3
NORM = 0.85
HIST = {"D0": (0, 0, 0), "D3": (0.75, 2.25, 0.75), "D12": (3, 9, 3), "D50": (12.5, 37.5, 12.5),
        "D100": (25, 75, 25), "Trise": (1, 3, 9), "Tfall": (15, 10, 2)}
W2_LINE = "That is about 1 in every {k} people in your town in the past four weeks."
W3_INSTR = ("On how many of the next 10 days will you A) stay at home, B) go out but take "
            "precautions, C) go out as normal? Give three whole numbers that add up to 10.")
W3_RE = re.compile(r"^\s*(?:A\s*[=:)]?\s*)?(\d+)\s*[,;/]?\s*(?:B\s*[=:)]?\s*)?(\d+)\s*[,;/]?\s*"
                   r"(?:C\s*[=:)]?\s*)?(\d+)\s*\.?\s*$")
WORDINGS = ("W1", "W2", "W3")


def w2_prompt(p, total):
    if total == 0:
        return p
    lines = p.split("\n")
    assert lines[2].startswith("In the past four weeks,") and lines[3] == ""
    lines.insert(3, W2_LINE.format(k=f"{rt.half_up(3000 / total):,}"))
    return "\n".join(lines)


def w3_prompt(p):
    assert p.count(PCT_INSTR) == 1 and p.endswith(PCT_INSTR)
    return p[: -len(PCT_INSTR)] + W3_INSTR


def parse_w3(text):
    m = W3_RE.match(text or "")
    if not m:
        return None
    a, b, c = (int(x) for x in m.groups())
    if a + b + c != 10:
        return None
    return dict(stay_home=a / 10, precautions=b / 10, normal=c / 10, raw=[a, b, c], sum=10)


def build_situations():
    pop = build_population(N=3000, seed=0)
    c34 = json.load(open(v1.SIT_FILE))["meta"]
    occ, eff = c34["occupation_flex"], c34["response_efficacy"]
    sits = []
    for who, band in (("young", v1.YOUNG_BAND), ("old", v1.OLD_BAND)):
        vul = float(pop.vulnerability[pop.age_band == band][0])
        for name, (a, b, c) in HIST.items():
            s = v2.situation(name, "", who, band, total=b + c, earlier=a + b, norm=NORM,
                             cum=a + b + c, vul=vul, occ=occ, eff=eff)
            s["id"] = f"{name}_{who}"
            s["history"] = dict(a=a, b=b, c=c, now=b + c, earlier=a + b, cumulative=a + b + c)
            p = s.pop("prompt")
            s["prompts"] = dict(W1=p, W2=w2_prompt(p, b + c), W3=w3_prompt(p))
            sits.append(s)
    return sits


def main():
    os.makedirs(OUT, exist_ok=True)
    v1.template_from_md()
    if "--situations" in sys.argv:
        sits = build_situations()
        json.dump(sits, open(SIT_FILE, "w"), indent=2)
        for s in sits:
            h = s["history"]
            print(f"{s['id']:12s} a/b/c {h['a']}/{h['b']}/{h['c']} | "
                  f"{s['prompts']['W1'].split(chr(10))[2]}")
        for w in WORDINGS:
            print(f"\n--- {w}, {sits[2]['id']}\n" + sits[2]["prompts"][w])
        return
    if "--score" in sys.argv:
        score()
        return
    import anthropic
    client = anthropic.Anthropic()
    sits = json.load(open(SIT_FILE))
    if "--count" in sys.argv:
        for w in WORDINGS:
            n = [client.messages.count_tokens(model=v1.MODEL, thinking={"type": "disabled"},
                 messages=[{"role": "user", "content": s["prompts"][w]}]).input_tokens
                 for s in sits]
            print(f"{w} input tokens {min(n)}-{max(n)}")
        return
    if "--run" in sys.argv:
        spent, t0, res = 0.0, time.time(), {}
        for w in WORDINGS:
            res[w] = {}
            v1.parse_saved = v1.parse
            for s in sits:
                res[w][s["id"]] = []
                for _ in range(N_REP):
                    if w == "W3":
                        v1.parse = parse_w3
                    rec, spent = v1.ask(client, s["prompts"][w], False, spent)
                    v1.parse = v1.parse_saved
                    res[w][s["id"]].append(rec)
                print(f"{w} {s['id']:12s} done; spent ${spent:.5f}", flush=True)
        json.dump(dict(model=v1.MODEL, spent=spent, wall_s=time.time() - t0, replies=res),
                  open(REPLY_FILE, "w"), indent=2)
        print(f"total spent ${spent:.5f} in {time.time() - t0:.0f}s")


def score():
    d = json.load(open(REPLY_FILE))
    sits = json.load(open(SIT_FILE))
    stats, crit = {}, {}
    for w in WORDINGS:
        print(f"\n{w}: id | replies | c mean (sd) | P(stay) mean (sd) | n | retries")
        atts = []
        for s in sits:
            recs = d["replies"][w][s["id"]]
            atts += [a for r in recs for a in r["attempts"]]
            fin = [r["final"] for r in recs if r["final"]]
            c = [1 - f["normal"] for f in fin]
            sh = [f["stay_home"] for f in fin]
            st = dict(c=float(np.mean(c)), c_sd=float(np.std(c, ddof=1)), stay=float(np.mean(sh)),
                      stay_sd=float(np.std(sh, ddof=1)), n=len(fin), N=len(recs),
                      retries=sum(r["retries"] for r in recs),
                      valid_first=sum(r["valid_first"] for r in recs),
                      raw=[f["raw"] for f in fin])
            stats[f"{w}|{s['id']}"] = st
            print(f"  {s['id']:12s} {' '.join('/'.join(map(str, x)) for x in st['raw']):26s} "
                  f"{st['c']:.3f} ({st['c_sd']:.3f})  {st['stay']:.3f} ({st['stay_sd']:.3f})  "
                  f"{st['n']}/{st['N']}  {st['retries']}")
        cc = {s["id"]: stats[f"{w}|{s['id']}"]["c"] for s in sits}
        ag = ("young", "old")
        i = all(cc[f"D100_{a}"] > cc[f"D0_{a}"] for a in ag)
        ii = all(cc[f"{n}_old"] >= cc[f"{n}_young"] for n in HIST)
        iii = all(cc[f"Trise_{a}"] >= cc[f"Tfall_{a}"] for a in ag)
        vf = sum(stats[f"{w}|{s['id']}"]["valid_first"] for s in sits)
        crit[w] = dict(i=i, ii=ii, iii=iii, n_pass=int(i) + int(ii) + int(iii),
                       valid_first=vf, decisions=N_REP * len(sits))
        bad = [a["text"] for a in atts if a["parsed"] is None]
        print(f"  (i) {i} [D100 vs D0: young {cc['D100_young']:.3f} vs {cc['D0_young']:.3f}, "
              f"old {cc['D100_old']:.3f} vs {cc['D0_old']:.3f}]  (ii) {ii} "
              f"[{sum(cc[f'{n}_old'] >= cc[f'{n}_young'] for n in HIST)}/{len(HIST)}]  (iii) {iii} "
              f"[rise vs fall: young {cc['Trise_young']:.3f} vs {cc['Tfall_young']:.3f}, old "
              f"{cc['Trise_old']:.3f} vs {cc['Tfall_old']:.3f}]  passes {crit[w]['n_pass']}/3")
        print(f"  valid first {vf}/{N_REP * len(sits)}, attempts {len(atts)}, invalid {bad[:5]}, "
              f"input {min(a['usage']['input_tokens'] for a in atts)}-"
              f"{max(a['usage']['input_tokens'] for a in atts)}, output "
              f"{min(a['usage']['output_tokens'] for a in atts)}-"
              f"{max(a['usage']['output_tokens'] for a in atts)}, cost "
              f"${sum(a['cost'] for a in atts):.5f}")
    # Selection rule (C37): most of (i)-(iii) passed; ties -> W1, then W2. None passes (i) -> stop.
    if not any(crit[w]["i"] for w in WORDINGS):
        winner = None
    else:
        best = max(crit[w]["n_pass"] for w in WORDINGS)
        winner = next(w for w in WORDINGS if crit[w]["n_pass"] == best)
    print(f"\nselection: {winner if winner else 'NONE passes (i): report and stop'}; "
          f"total cost ${d['spent']:.5f}")
    json.dump(dict(stats=stats, criteria=crit, winner=winner),
              open(os.path.join(OUT, "pilot_v4_scores.json"), "w"), indent=2)


if __name__ == "__main__":
    main()

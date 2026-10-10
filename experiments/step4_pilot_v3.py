"""
Pilot v3 of the arm-2 prompt: format and model diagnostic (register C36). DIAGNOSTIC ONLY: the
frozen template, the model decision (A63) and A65 are unchanged for the study.

Situations: C35's base (day 60, social_norm 0.85, flat deaths, cumulative = 4-week total + 5,
current_action normal), Test D levels {0, 3, 12, 50, 100}, young (band 2) and old (band 8).
  V1: claude-haiku-5-5,  one-letter answer, 10 calls per situation.
  V2: claude-sonnet-5-5, percentages (template as frozen), 3 calls per situation.
  V3: claude-sonnet-5-5, one-letter answer, 10 calls per situation.
Thinking OFF: Haiku `{"type": "disabled"}` (A65); Sonnet 5.5 rejects "disabled" with a 400 and
its thinking-off setting is `{"type": "between_tools"}` (docs, checked 10 Oct 2026). Effort,
temperature, top_p, top_k not sent (API defaults), as A65. max_tokens 1024 as A65.
Letter prompt: the rendered percentage prompt with ONLY its answer instructions (the last two
lines) replaced by LETTER_INSTR. Reply rule for letters: LETTER_RE; retries as A61.

Modes: --situations, --count, --run, --score.
"""
import json
import os
import re
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import step4_pilot as v1  # noqa: E402
import step4_pilot_v2 as v2  # noqa: E402

OUT = v1.OUT
SIT_FILE = os.path.join(OUT, "pilot_v3_situations.json")
REPLY_FILE = os.path.join(OUT, "pilot_v3_replies.json")
LEVELS = [0, 3, 12, 50, 100]
PCT_INSTR = ("Give the probability, in percent, that you choose each option. Use whole numbers "
             "that add up to 100. Reply in exactly this form and nothing else:\n"
             "A=<number>, B=<number>, C=<number>")
LETTER_INSTR = "Answer with a single letter: A, B or C."
LETTER_RE = re.compile(r"^\s*([ABC])\s*[.)]?\s*$")
MODELS = {"haiku": "claude-haiku-5-5", "sonnet": "claude-sonnet-5-5"}
PRICE = {"haiku": (0.10e-6, 0.50e-6), "sonnet": (2.00e-6, 10.00e-6)}   # $/token, standard API
THINKING_OFF = {"haiku": {"type": "disabled"}, "sonnet": {"type": "between_tools"}}
VERSIONS = {"V1": ("haiku", "letter", 10), "V2": ("sonnet", "pct", 3),
            "V3": ("sonnet", "letter", 10)}
COST_CAP = 2.00


def letter_prompt(pct_prompt):
    assert pct_prompt.count(PCT_INSTR) == 1 and pct_prompt.endswith(PCT_INSTR)
    return pct_prompt[: -len(PCT_INSTR)] + LETTER_INSTR


def build_situations():
    _, all_v2 = v2.build_situations()
    sits = [s for s in all_v2 if s["test"] == "D" and s["level"] in LEVELS]
    for s in sits:
        s["prompt_pct"] = s.pop("prompt")
        s["prompt_letter"] = letter_prompt(s["prompt_pct"])
    return sits


def parse_letter(text):
    m = LETTER_RE.match(text or "")
    return dict(choice=m.group(1)) if m else None


def call(client, model_key, prompt):
    r = client.messages.create(model=MODELS[model_key], max_tokens=v1.MAX_TOKENS_OFF,
                               thinking=THINKING_OFF[model_key],
                               messages=[{"role": "user", "content": prompt}])
    text = "".join(b.text for b in r.content if b.type == "text")
    usage = r.usage.to_dict() if hasattr(r.usage, "to_dict") else dict(r.usage)
    pin, pout = PRICE[model_key]
    return dict(text=text, stop_reason=r.stop_reason, model=r.model, usage=usage,
                n_thinking_blocks=sum(1 for b in r.content if b.type == "thinking"),
                cost=usage["input_tokens"] * pin + usage["output_tokens"] * pout)


def ask(client, model_key, fmt, prompt):
    parse = parse_letter if fmt == "letter" else v1.parse
    attempts = []
    for _ in range(3):                                                   # 1 + 2 retries (A61)
        a = call(client, model_key, prompt)
        a["parsed"] = parse(a["text"])
        attempts.append(a)
        if a["parsed"] is not None:
            break
    final = attempts[-1]["parsed"]
    return dict(attempts=attempts, valid_first=attempts[0]["parsed"] is not None,
                retries=len(attempts) - 1, final=final, fallback=final is None,
                cost=sum(a["cost"] for a in attempts))


def main():
    os.makedirs(OUT, exist_ok=True)
    v1.template_from_md()
    if "--situations" in sys.argv:
        sits = build_situations()
        json.dump(sits, open(SIT_FILE, "w"), indent=2)
        for s in sits:
            print(f"{s['id']:10s} | {s['prompt_pct'].split(chr(10))[2]}")
        print("\n--- letter prompt,", sits[2]["id"], "\n" + sits[2]["prompt_letter"])
        return
    if "--score" in sys.argv:
        score()
        return
    import anthropic
    client = anthropic.Anthropic()
    sits = json.load(open(SIT_FILE))
    if "--count" in sys.argv:
        for mk in MODELS:
            for fmt in ("pct", "letter"):
                n = [client.messages.count_tokens(
                        model=MODELS[mk], thinking=THINKING_OFF[mk],
                        messages=[{"role": "user", "content": s[f"prompt_{fmt}"]}]).input_tokens
                     for s in sits]
                print(f"{mk:6s} {fmt:6s} input tokens {min(n)}-{max(n)}")
        return
    if "--run" in sys.argv:
        total = sum(n for _, _, n in VERSIONS.values()) * len(sits)
        spent, done, t0, res = 0.0, 0, time.time(), {}
        for ver, (mk, fmt, n) in VERSIONS.items():
            res[ver] = {}
            for s in sits:
                res[ver][s["id"]] = []
                for _ in range(n):
                    rec = ask(client, mk, fmt, s[f"prompt_{fmt}"])
                    res[ver][s["id"]].append(rec)
                    spent += rec["cost"]
                    done += 1
                    if spent > COST_CAP:
                        raise RuntimeError(f"cost cap exceeded (${spent:.4f})")
                print(f"{ver} {s['id']:10s} done; spent ${spent:.5f}", flush=True)
            json.dump(dict(spent=spent, replies=res), open(REPLY_FILE, "w"), indent=2)
        json.dump(dict(spent=spent, wall_s=time.time() - t0, replies=res),
                  open(REPLY_FILE, "w"), indent=2)
        print(f"total spent ${spent:.5f} in {time.time() - t0:.0f}s, {done}/{total} decisions")


def score():
    d = json.load(open(REPLY_FILE))
    sits = json.load(open(SIT_FILE))
    stats = {}
    for ver, (mk, fmt, n) in VERSIONS.items():
        print(f"\n{ver}: {MODELS[mk]}, {fmt}, {n} per situation")
        atts = []
        for s in sits:
            recs = d["replies"][ver][s["id"]]
            atts += [a for r in recs for a in r["attempts"]]
            fin = [r["final"] for r in recs if r["final"]]
            if fmt == "letter":
                ch = [f["choice"] for f in fin]
                cnt = {k: ch.count(k) for k in "ABC"}
                st = dict(n=len(fin), N=len(recs), counts=cnt,
                          caution=(cnt["A"] + cnt["B"]) / len(fin), stay=cnt["A"] / len(fin))
                txt = f"A/B/C = {cnt['A']}/{cnt['B']}/{cnt['C']}"
            else:
                c = [1 - f["normal"] for f in fin]
                sh = [f["stay_home"] for f in fin]
                st = dict(n=len(fin), N=len(recs), raw=[f["raw"] for f in fin],
                          caution=float(np.mean(c)), caution_sd=float(np.std(c, ddof=1)),
                          stay=float(np.mean(sh)), stay_sd=float(np.std(sh, ddof=1)))
                txt = (" ".join("/".join(map(str, f["raw"])) for f in fin) +
                       f"  sd c {st['caution_sd']:.3f} sd stay {st['stay_sd']:.3f}")
            st.update(retries=sum(r["retries"] for r in recs),
                      valid_first=sum(r["valid_first"] for r in recs))
            stats[f"{ver}|{s['id']}"] = st
            print(f"  {s['id']:10s} caution {st['caution']:.3f} stay {st['stay']:.3f} "
                  f"n={st['n']}/{st['N']} retries {st['retries']} | {txt}")
        bad = [a["text"] for a in atts if a["parsed"] is None]
        print(f"  attempts {len(atts)}, invalid {len(bad)} {bad[:5]}, input tokens "
              f"{min(a['usage']['input_tokens'] for a in atts)}-"
              f"{max(a['usage']['input_tokens'] for a in atts)}, output "
              f"{min(a['usage']['output_tokens'] for a in atts)}-"
              f"{max(a['usage']['output_tokens'] for a in atts)}, thinking blocks "
              f"{sum(a['n_thinking_blocks'] for a in atts)}, models "
              f"{sorted({a['model'] for a in atts})}, stop "
              f"{sorted({a['stop_reason'] for a in atts})}, cost "
              f"${sum(a['cost'] for a in atts):.5f}")
    print(f"\ntotal cost ${d['spent']:.5f}")
    json.dump(stats, open(os.path.join(OUT, "pilot_v3_scores.json"), "w"), indent=2)


if __name__ == "__main__":
    main()

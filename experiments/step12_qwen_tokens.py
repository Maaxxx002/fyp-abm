"""
Step 12 Part 4 (register C57): offline Qwen token count. NO API CALLS -- the tokenizer runs locally.

Run in a separate environment with `tokenizers` and `jinja2` installed (not the project interpreter):
    <venv python> experiments/step12_qwen_tokens.py <tokenizer_dir> [prompts.json]
<tokenizer_dir> holds tokenizer.json and chat_template.jinja downloaded from the Hugging Face repo
Qwen/Qwen3.8-Flash-Next (pinned commit recorded in the register). Only data files are loaded; no
model code is executed (`tokenizers.Tokenizer.from_file`; the chat template is rendered in a jinja2
sandbox).

Counts, per prompt: (1) the raw prompt text; (2) the prompt wrapped by the repo's chat template as a
single user message with add_generation_prompt=True and enable_thinking=False (the framing an API
call would add; whether Alibaba bills exactly this framing is not documented on the pages read).
Reply: "A=10, B=60, C=30" alone and followed by the end-of-turn token <|im_end|>.
Cost per call at $0.15 / $0.47 per M input / output tokens (Model Studio, Singapore, International).
"""
import json
import os
import sys

from jinja2.sandbox import ImmutableSandboxedEnvironment
from tokenizers import Tokenizer

IN_PRICE, OUT_PRICE = 0.15e-6, 0.47e-6
REPLY = "A=10, B=60, C=30"


def main():
    tok_dir = sys.argv[1]
    here = os.path.dirname(os.path.abspath(__file__))
    path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(here, "..", "results", "step7", "step12_prompts.json")
    tok = Tokenizer.from_file(os.path.join(tok_dir, "tokenizer.json"))
    env = ImmutableSandboxedEnvironment(trim_blocks=True, lstrip_blocks=True)

    def raise_exception(msg):
        raise ValueError(msg)
    env.globals["raise_exception"] = raise_exception
    env.filters["tojson"] = lambda x, **kw: json.dumps(x, ensure_ascii=False)
    tmpl = env.from_string(open(os.path.join(tok_dir, "chat_template.jinja"), encoding="utf-8").read())

    def n(text):
        return len(tok.encode(text, add_special_tokens=False).ids)

    def framed(text):
        s = tmpl.render(messages=[{"role": "user", "content": text}], add_generation_prompt=True,
                        enable_thinking=False)
        return s, n(s)

    d = json.load(open(path, encoding="utf-8"))
    example, _ = framed("PROMPT")
    print(f"chat-template framing (enable_thinking=False, add_generation_prompt=True), with PROMPT as the text:\n"
          f"{example!r}")
    out = {"reply_raw": n(REPLY), "reply_with_end": n(REPLY + "<|im_end|>")}
    print(f"reply {REPLY!r}: {out['reply_raw']} tokens; with <|im_end|>: {out['reply_with_end']}")
    for name, items in (("C37 pilot prompts", d["c37"]), ("C53 random sample", d["c53_sample"])):
        raw = [n(x["text"]) for x in items]
        fr = [framed(x["text"])[1] for x in items]
        rows = {"n": len(items), "raw_min": min(raw), "raw_max": max(raw), "raw_mean": sum(raw) / len(raw),
                "framed_min": min(fr), "framed_max": max(fr), "framed_mean": sum(fr) / len(fr),
                "chars_mean": sum(len(x["text"]) for x in items) / len(items)}
        if name.startswith("C37"):
            for w in ("W1", "W2", "W3"):
                sub = [(r, f) for r, f, x in zip(raw, fr, items) if x["wording"] == w]
                rows[w] = dict(raw=[min(r for r, _ in sub), max(r for r, _ in sub)],
                               framed=[min(f for _, f in sub), max(f for _, f in sub)])
        cost = lambda i, o: i * IN_PRICE + o * OUT_PRICE  # noqa: E731
        rows["cost_per_call_framed_mean"] = cost(rows["framed_mean"], out["reply_with_end"])
        rows["cost_per_call_raw_mean"] = cost(rows["raw_mean"], out["reply_raw"])
        rows["cost_per_call_framed_max"] = cost(rows["framed_max"], out["reply_with_end"])
        out[name] = rows
        print(f"\n{name}: n {rows['n']}; mean characters {rows['chars_mean']:.0f}; raw tokens {rows['raw_min']}-"
              f"{rows['raw_max']} (mean {rows['raw_mean']:.1f}); framed {rows['framed_min']}-{rows['framed_max']} "
              f"(mean {rows['framed_mean']:.1f})")
        for w in ("W1", "W2", "W3"):
            if w in rows:
                print(f"  {w}: raw {rows[w]['raw'][0]}-{rows[w]['raw'][1]}; framed {rows[w]['framed'][0]}-"
                      f"{rows[w]['framed'][1]}")
        print(f"  cost per call: framed mean + reply with end ${rows['cost_per_call_framed_mean']:.8f}; raw mean + "
              f"reply ${rows['cost_per_call_raw_mean']:.8f}; framed max + reply with end "
              f"${rows['cost_per_call_framed_max']:.8f}")
    json.dump(out, open(os.path.join(os.path.dirname(path), "step12_qwen_tokens.json"), "w"), indent=1)


if __name__ == "__main__":
    main()

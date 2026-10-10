"""
Arm 3, step 1: generate K = 5 rules (A51) from the frozen arm-3 instruction v1 (A66), run the
A53 mechanical checks, freeze each passing rule (A54), and compute each rule's caution curve on
the C37 pilot situations (E24's proposed curve). No epidemic simulation. Register C38.

Model claude-haiku-5-5 with A65 settings (thinking {"type": "disabled"}; effort, temperature,
top_p, top_k not sent; no system prompt; the instruction is the single user message).
max_tokens = MAX_TOKENS (implementation cap so code cannot be cut off; a reply that stops at
max_tokens fails check 1). Each attempt is a fresh, independent call.

Code extraction: the first fenced block (```python or ```) in the reply if there is one,
otherwise the whole reply, stripped.

A53 checks, in this order (a rule is only executed after the static check passes):
  (3) static: the code parses; the only imports are `math`; no forbidden names
      (FORBIDDEN_NAMES) or dunder attributes; defines decide(p) with one parameter; every
      attribute read on that parameter is a Perception field.
  (1) runs: executed with a restricted set of builtins (imports limited to math); every
      grid call returns without error.
  (2) valid probabilities on the grid: a dict with exactly the keys stay_home, precautions,
      normal; values real, finite, >= 0, summing to 1 within 1e-9.
  (3) dynamic: on the grid, p is a proxy that raises on any attribute that is not a field.
  (4) deterministic: a second, fresh execution gives identical outputs on the whole grid
      evaluated in reverse order, and two back-to-back repeat calls per grid point in the
      first execution give identical outputs.

Usage:  python experiments/step5_arm3_generate.py --run      (API calls; writes src/arm3_rules/v1)
        python experiments/step5_arm3_generate.py --curves   (no API calls)
"""
import ast
import dataclasses
import datetime
import hashlib
import itertools
import json
import math
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, HERE)
from perception import Perception  # noqa: E402
from population import build_population  # noqa: E402
import step5_freeze_prompts as fz  # noqa: E402

MODEL = "claude-haiku-5-5"
PRICE_IN, PRICE_OUT = 0.10e-6, 0.50e-6
COST_CAP = 1.00
K = 5
MAX_ATTEMPTS_PER_RULE = 5          # safety stop: report rather than keep regenerating
MAX_TOKENS = 8192
ARM3_SHA = "fb28ae6f11f7468a25269c4d789995fb1d5ca5a6242723ec9cc843e7ebfb058f"   # A66
RULE_DIR = os.path.join(ROOT, "src", "arm3_rules", "v1")
OUT = os.path.join(ROOT, "results", "step5")
FIELDS = tuple(f.name for f in dataclasses.fields(Perception))
KEYS = {"stay_home", "precautions", "normal"}
FORBIDDEN_NAMES = {"open", "exec", "eval", "compile", "__import__", "input", "print", "globals",
                   "locals", "vars", "getattr", "setattr", "delattr", "breakpoint", "help",
                   "exit", "quit", "memoryview", "id", "hash", "dir", "type", "object",
                   "random", "time", "os", "sys"}
SAFE_BUILTINS = {n: getattr(__builtins__, n) if not isinstance(__builtins__, dict)
                 else __builtins__[n] for n in (
                     "abs", "min", "max", "sum", "round", "float", "int", "bool", "len", "range",
                     "enumerate", "zip", "sorted", "dict", "list", "tuple", "str", "isinstance",
                     "pow", "map", "filter", "any", "all", "reversed", "ValueError", "TypeError",
                     "ZeroDivisionError", "ArithmeticError", "OverflowError", "Exception")}


def safe_import(name, *args, **kw):
    if name != "math":
        raise ImportError(f"import of {name!r} not allowed")
    return math


class P:
    """Perception proxy: raises on any attribute that is not a Perception field."""
    __slots__ = ("_v",)

    def __init__(self, values):
        object.__setattr__(self, "_v", values)

    def __getattr__(self, name):
        v = object.__getattribute__(self, "_v")
        if name not in v:
            raise AttributeError(f"non-Perception attribute {name!r}")
        return v[name]


def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def extract_code(reply):
    m = re.search(r"```(?:python)?[ \t]*\n(.*?)```", reply, re.S)
    return (m.group(1) if m else reply).strip() + "\n"


def static_check(code):
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"syntax error: {e}"
    decide = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "decide"]
    if len(decide) != 1:
        return "no single top-level decide()"
    args = decide[0].args
    if len(args.args) != 1 or args.vararg or args.kwarg or args.kwonlyargs:
        return "decide() must take exactly one parameter"
    pname = args.args[0].arg
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(a.name != "math" for a in node.names):
                return f"import not allowed: {[a.name for a in node.names]}"
        elif isinstance(node, ast.ImportFrom):
            if node.module != "math":
                return f"import not allowed: from {node.module}"
        elif isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            return f"forbidden name: {node.id}"
        elif isinstance(node, ast.Attribute):
            if node.attr.startswith("__"):
                return f"dunder attribute: {node.attr}"
            if isinstance(node.value, ast.Name) and node.value.id == pname \
                    and node.attr not in FIELDS:
                return f"non-Perception attribute: {pname}.{node.attr}"
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            return "global/nonlocal statement"
    return None


def load(code):
    ns = {"__builtins__": dict(SAFE_BUILTINS, __import__=safe_import), "__name__": "arm3_rule"}
    exec(compile(code, "<arm3_rule>", "exec"), ns)
    return ns["decide"]


def grids():
    """Typical + extreme inputs. Grid A: structured product at population 3,000 with each
    band's own vulnerability. Grid B: 20,000 random points over wide ranges (seeded)."""
    pop = build_population(N=3000, seed=0)
    vul = {b: float(pop.vulnerability[pop.age_band == b][0]) for b in range(10)}
    pts = []
    for day, d28, d7, cum, norm, band, occ, eff, act in itertools.product(
            [0, 7, 60, 600], [0.0, 0.1, 3.6, 100.0], [0.0, 0.1, 3.6, 100.0],
            [0.0, 10.0, 3000.0], [0.0, 0.85, 1.0], [0, 2, 8, 9], [0.0, 0.41, 1.0],
            [0.0, 0.8, 1.0], ["stay_home", "precautions", "normal"]):
        pts.append(dict(deaths_28day_mean=d28, deaths_cumulative=cum,
                        deaths_28day_mean_7d_ago=d7, current_action=act, social_norm=norm,
                        age_band=band, vulnerability=vul[band], occupation_flex=occ,
                        response_efficacy=eff, population=3000, day=day))
    n_a = len(pts)
    rng = np.random.default_rng(20261010)
    acts = ["stay_home", "precautions", "normal"]
    for _ in range(20000):
        pts.append(dict(
            deaths_28day_mean=float(rng.choice([0.0, rng.uniform(0, 5), rng.uniform(0, 1e4)])),
            deaths_cumulative=float(rng.choice([0.0, rng.uniform(0, 100), rng.uniform(0, 1e6)])),
            deaths_28day_mean_7d_ago=float(rng.choice([0.0, rng.uniform(0, 5),
                                                       rng.uniform(0, 1e4)])),
            current_action=acts[rng.integers(3)], social_norm=float(rng.uniform(0, 1)),
            age_band=int(rng.integers(10)), vulnerability=float(rng.uniform(0, 1)),
            occupation_flex=float(rng.uniform(0, 1)), response_efficacy=float(rng.uniform(0, 1)),
            population=int(rng.choice([1, 3000, 100000])), day=int(rng.integers(0, 10001))))
    return pts, n_a


def valid_probs(out):
    if not isinstance(out, dict) or set(out) != KEYS:
        return f"bad return value {out!r}"[:200]
    vals = []
    for k in KEYS:
        v = out[k]
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            return f"{k} is {type(v).__name__}"
        if not math.isfinite(v) or v < 0:
            return f"{k} = {v}"
        vals.append(float(v))
    if abs(sum(vals) - 1.0) > 1e-9:
        return f"sum = {sum(vals)!r}"
    return None


def mechanical_checks(code, pts):
    res = dict(static=None, runs=None, probs=None, fields=None, deterministic=None)
    err = static_check(code)
    res["static"] = err or "pass"
    if err:
        return False, res
    try:
        f1, f2 = load(code), load(code)
    except Exception as e:                                     # noqa: BLE001
        res["runs"] = f"load failed: {type(e).__name__}: {e}"
        return False, res
    out1 = []
    for x in pts:
        try:
            o = f1(P(x))
        except AttributeError as e:
            res["fields"] = f"{e} at {x}"
            return False, res
        except Exception as e:                                 # noqa: BLE001
            res["runs"] = f"{type(e).__name__}: {e} at {x}"[:400]
            return False, res
        bad = valid_probs(o)
        if bad:
            res["probs"] = f"{bad} at {x}"[:400]
            return False, res
        out1.append(dict(o))
    res.update(runs="pass", probs="pass", fields="pass")
    # fresh execution, grid in reverse order; then two back-to-back calls per point in the
    # first execution (catches hidden state that a same-order replay can miss)
    for x, o in zip(reversed(pts), reversed(out1)):
        if f2(P(x)) != o:
            res["deterministic"] = f"fresh execution differs at {x}"[:400]
            return False, res
    for x, o in zip(pts, out1):
        if f1(P(x)) != o or f1(P(x)) != o:
            res["deterministic"] = f"repeated call differs at {x}"[:400]
            return False, res
    res["deterministic"] = "pass"
    return True, res


def generate():
    import anthropic
    client = anthropic.Anthropic()
    instr = open(fz.ARM3_FILE, encoding="utf-8", newline="").read()
    assert sha256(instr) == ARM3_SHA, "frozen arm-3 instruction hash mismatch"
    os.makedirs(RULE_DIR, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    pts, n_a = grids()
    print(f"grid: {len(pts)} points ({n_a} structured + {len(pts) - n_a} random)")
    spent, log, manifest = 0.0, [], dict(rules=[])
    for k in range(1, K + 1):
        for attempt in range(1, MAX_ATTEMPTS_PER_RULE + 1):
            when = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
            r = client.messages.create(model=MODEL, max_tokens=MAX_TOKENS,
                                       thinking={"type": "disabled"},
                                       messages=[{"role": "user", "content": instr}])
            reply = "".join(b.text for b in r.content if b.type == "text")
            u = r.usage
            cost = u.input_tokens * PRICE_IN + u.output_tokens * PRICE_OUT
            spent += cost
            code = extract_code(reply)
            if r.stop_reason != "end_turn":
                ok, checks = False, dict(stop_reason=f"stop_reason {r.stop_reason}")
            else:
                ok, checks = mechanical_checks(code, pts)
            entry = dict(rule=k, attempt=attempt, utc=when, ok=ok, checks=checks,
                         model_served=r.model, request_id=getattr(r, "_request_id", None),
                         stop_reason=r.stop_reason, input_tokens=u.input_tokens,
                         output_tokens=u.output_tokens, cost=cost, reply_sha256=sha256(reply),
                         code_sha256=sha256(code), fenced=reply.strip() != code.strip())
            log.append(entry)
            tag = f"rule_{k}" if ok else f"rejected_rule_{k}_attempt_{attempt}"
            with open(os.path.join(RULE_DIR if ok else OUT, f"{tag}_reply.txt"), "w",
                      encoding="utf-8", newline="") as f:
                f.write(reply)
            print(f"rule {k} attempt {attempt}: {'PASS' if ok else 'FAIL'} {checks} "
                  f"{u.input_tokens}/{u.output_tokens} tokens ${cost:.5f}", flush=True)
            if spent > COST_CAP:
                raise RuntimeError(f"cost cap ${COST_CAP} exceeded (${spent:.4f})")
            if ok:
                path = os.path.join(RULE_DIR, f"rule_{k}.py")
                assert not os.path.exists(path), f"{path} exists: frozen rules are never rewritten"
                with open(path, "w", encoding="utf-8", newline="") as f:
                    f.write(code)
                manifest["rules"].append(dict(
                    rule=k, file=f"src/arm3_rules/v1/rule_{k}.py", code_sha256=sha256(code),
                    reply_file=f"src/arm3_rules/v1/rule_{k}_reply.txt",
                    reply_sha256=sha256(reply), attempts=attempt, **{
                        x: entry[x] for x in ("utc", "model_served", "request_id",
                                              "input_tokens", "output_tokens", "cost")}))
                break
        else:
            raise RuntimeError(f"rule {k}: {MAX_ATTEMPTS_PER_RULE} attempts failed; stopping")
    manifest.update(
        prompt_file="prompts/frozen_v1/arm3_instruction_v1.txt", prompt_sha256=ARM3_SHA,
        model_requested=MODEL, settings=dict(thinking={"type": "disabled"}, max_tokens=MAX_TOKENS,
                                             effort="not sent (API default medium)",
                                             temperature="not sent (API default 1)",
                                             system_prompt=None),
        grid_points=len(pts), total_cost=spent, generation_log=log)
    with open(os.path.join(RULE_DIR, "manifest.json"), "w", encoding="utf-8", newline="") as f:
        json.dump(manifest, f, indent=2)
    print(f"total spent ${spent:.5f}; {len(log)} calls for {K} rules")


def curves():
    sits = json.load(open(os.path.join(ROOT, "results", "step4", "pilot_v4_situations.json")))
    w1 = json.load(open(os.path.join(ROOT, "results", "step4", "pilot_v4_scores.json")))["stats"]
    order = ["D0", "D3", "D12", "D50", "D100", "Trise", "Tfall"]
    man = json.load(open(os.path.join(RULE_DIR, "manifest.json")))
    for r in man["rules"]:
        code = open(os.path.join(ROOT, r["file"]), encoding="utf-8", newline="").read()
        assert sha256(code) == r["code_sha256"], f"rule {r['rule']} hash mismatch"
    rows = {}
    for who in ("young", "old"):
        print(f"\n{who}: caution c = 1 - P(normal) [P(stay home)]")
        print("        " + "".join(f"{n:>14s}" for n in order))
        w = [w1[f"W1|{n}_{who}"] for n in order]
        print("arm2 W1 " + "".join(f"{x['c']:7.3f} [{x['stay']:.2f}]" for x in w))
        for r in man["rules"]:
            f = load(open(os.path.join(ROOT, r["file"]), encoding="utf-8").read())
            vals = []
            for n in order:
                s = next(s for s in sits if s["id"] == f"{n}_{who}")
                o = f(P(dict(s["fields"])))
                vals.append((1 - o["normal"], o["stay_home"]))
            rows[f"rule_{r['rule']}|{who}"] = vals
            print(f"rule {r['rule']}  " + "".join(f"{c:7.3f} [{s:.2f}]" for c, s in vals))
    json.dump(rows, open(os.path.join(OUT, "arm3_curves.json"), "w"), indent=2)


if __name__ == "__main__":
    if "--run" in sys.argv:
        generate()
    if "--curves" in sys.argv:
        curves()

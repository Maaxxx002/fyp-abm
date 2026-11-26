"""
Step 13 (register C58): prompt v2 DRAFT (A74), the Qwen client (A72) and a 20-call smoke test.

  --write-v2   write prompts/v2/arm3_instruction_v2.txt from v1 (refuses to overwrite a different
               file); print SHA-256 and length of both v2 files. The v2 arm-2 template is a byte
               copy of v1's (checked here and in tests/test_render_v2.py).
  --examples   re-run C55's arm-1 S1 run (N = 15,000, seed 0, 7-day window), reading start-of-day
               state and actions on the C58 days without changing the run (outputs asserted equal
               to the step-12 cache); print the band-7 examples at days 3, 10, 45 and write the 10
               smoke-test prompts (days 3, 10, 30, 45, 90 x bands 2 and 8).
  --plan       print the planned calls and a rough cost. No network.
  --offline    exercise the client with a fake API (valid, invalid-then-valid, 429-then-valid,
               request cap). No network.
  --run        THE ONLY MODE THAT SPENDS CREDITS: 10 prompts x 2 repeats, one at a time, hard cap
               MAX_REQUESTS HTTP requests. Writes results/step13/smoke_log.json.
  --score      summarise the smoke log.

Usage:  py -3.14 experiments/step13_v2_smoke.py --write-v2 | --examples | --plan | --offline | --run | --score
"""
import hashlib
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
OUT = os.path.join(ROOT, "results", "step13")
V1 = os.path.join(ROOT, "prompts", "frozen_v1")
V2 = os.path.join(ROOT, "prompts", "v2")
PROMPTS_FILE = os.path.join(OUT, "smoke_prompts.json")
LOG_FILE = os.path.join(OUT, "smoke_log.json")
CACHE12 = os.path.join(ROOT, "results", "step7", "step12_runs.npz")

N, SEED = 15_000, 0
S1 = dict(R0=3.0, T_H=14.0)
EXAMPLE_DAYS, EXAMPLE_BAND = (3, 10, 45), 7
SMOKE_DAYS, SMOKE_BANDS = (3, 10, 30, 45, 90), (2, 8)
REPEATS = 2
MAX_REQUESTS = 25                                     # approved for step 13 (Max)
PAYG_PER_CALL = 0.00005304                            # C57: framed mean + reply, $0.15 / $0.47 per M
ACT = {0: "normal", 1: "precautions", 2: "stay_home"}  # shared_world action codes

ARM3_V1_LINES = """- p.deaths_28day_mean (float, >= 0): deaths per day, averaged over the past 28 days (over the
  days so far, if fewer than 28). {deaths_recent} shows this as a whole-number total: the
  average times min(28, day), rounded.
- p.deaths_28day_mean_7d_ago (float, >= 0): the same average as it was 7 days ago (0 before
  day 7). {deaths_earlier} shows this as a whole-number total: the average times
  min(28, day - 7), rounded."""
ARM3_V2_LINES = """- p.deaths_7day_mean (float, >= 0): deaths per day, averaged over the past 7 days (over the
  days so far, if fewer than 7). {deaths_recent} shows this as a whole-number total: the
  average times min(7, day), rounded.
- p.deaths_7day_mean_7d_ago (float, >= 0): the same average as it was 7 days ago (0 before
  day 7). {deaths_earlier} shows this as a whole-number total: the average times
  min(7, day - 7), rounded."""


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def write_v2():
    t1 = open(os.path.join(V1, "arm2_template_v1.txt"), "rb").read()
    t2 = open(os.path.join(V2, "arm2_template_v2.txt"), "rb").read()
    assert t1 == t2, "v2 template must be a byte copy of v1"
    a1 = open(os.path.join(V1, "arm3_instruction_v1.txt"), encoding="utf-8", newline="").read()
    assert a1.count(ARM3_V1_LINES) == 1
    a2 = a1.replace(ARM3_V1_LINES, ARM3_V2_LINES)
    path = os.path.join(V2, "arm3_instruction_v2.txt")
    if os.path.exists(path):
        assert open(path, encoding="utf-8", newline="").read() == a2, f"{path} differs; not overwritten"
    else:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(a2)
    for name in ("arm2_template_v2.txt", "arm3_instruction_v2.txt"):
        b = open(os.path.join(V2, name), "rb").read()
        print(f"prompts/v2/{name}  sha256 {sha256(b)}  {len(b.decode('utf-8'))} chars (DRAFT, not frozen)")


def examples():
    from population import build_population
    from shared_world import CBFArm1, run_shared_world, own_health_of, NEVER_ILL
    import render_v2 as r2

    days = sorted(set(EXAMPLE_DAYS) | set(SMOKE_DAYS))

    class Recorder(CBFArm1):
        """CBF unchanged; reads run_shared_world's start-of-day state and actions (read-only)."""
        snap = {}

        def transitions(self, view):
            f = sys._getframe(1)
            if f.f_code.co_name == "run_shared_world":
                t = f.f_locals["t"]
                if t in days and t not in self.snap:   # first call of day t: the pre-sub-step check
                    self.snap[t] = (f.f_locals["state"].copy(), f.f_locals["action"].copy())
            return super().transitions(view)

    pop = build_population(N=N, seed=0)
    dec = Recorder()
    t0 = time.time()
    o = run_shared_world(N=N, seed=SEED, decision=dec, days=600, f_D=pop.vulnerability, window=7,
                         detection_rate=0.7, **S1)
    print(f"run {time.time() - t0:.0f}s")
    c = np.load(CACHE12)
    for k in ("incidence", "prevalence", "S", "awareness_signal", "deaths"):
        assert np.array_equal(np.asarray(o[k], float), c[f"arm1|arm1|S1|{SEED}#{k}"]), k
    print("outputs equal to the C55 cache (arm1|S1|seed 0): incidence, prevalence, S, awareness_signal, deaths")
    rep = o["reported_deaths"]
    # the 7-day signal is the mean of reported deaths over the days strictly before today
    for t in days:
        assert np.isclose(o["awareness_signal"][t], rep[max(0, t - 7):t].mean() if t else 0.0)

    def prompt_for(day, band):
        state, action = dec.snap[day]
        ok = (own_health_of(state) == NEVER_ILL) & (np.asarray(pop.age_band) == band)
        i = int(np.flatnonzero(ok)[0])
        p = r2.perception_from_world(day, o["awareness_signal"], rep, o["social_norm"], N,
                                     (pop.age_band[i], pop.vulnerability[i], pop.occupation_flex[i],
                                      pop.response_efficacy[i]), ACT[int(action[i])])
        return dict(id=f"d{day}_b{band}", day=day, band=band, agent=i,
                    fields={k: getattr(p, k) for k in r2.FIELD_PLACEHOLDER}, prompt=r2.render(p))

    for day in EXAMPLE_DAYS:
        e = prompt_for(day, EXAMPLE_BAND)
        print(f"\n===== day {day}, agent {e['agent']} (band {EXAMPLE_BAND}), fields {e['fields']}\n{e['prompt']}")
    smoke = [prompt_for(d, b) for d in SMOKE_DAYS for b in SMOKE_BANDS]
    os.makedirs(OUT, exist_ok=True)
    json.dump(dict(run=dict(N=N, seed=SEED, scenario="S1", window=7, arm="arm1 (CBF)"), prompts=smoke),
              open(PROMPTS_FILE, "w"), indent=1)
    print("\nsmoke prompts:")
    for s in smoke:
        print(f"  {s['id']:8s} agent {s['agent']:5d} action {s['fields']['current_action']:11s} | "
              f"{s['prompt'].split(chr(10))[2]}")


def plan():
    n = len(SMOKE_DAYS) * len(SMOKE_BANDS) * REPEATS
    print(f"planned: {len(SMOKE_DAYS) * len(SMOKE_BANDS)} prompts x {REPEATS} repeats = {n} decisions, "
          f"one request each if every reply is valid; hard cap {MAX_REQUESTS} HTTP requests "
          f"(A61/transport retries count toward it)")
    print(f"rough cost at pay-as-you-go prices (C57, ${PAYG_PER_CALL}/call): ${n * PAYG_PER_CALL:.4f} for {n}, "
          f"${MAX_REQUESTS * PAYG_PER_CALL:.4f} at the cap. Token Plan bills Credits; no Credit rate is "
          f"published for qwen3.8-flash.")


class _Fake:
    """Offline stand-in for openai.OpenAI: scripted replies, no network."""

    def __init__(self, script):
        import httpx2 as httpx
        import openai
        self.script, self.httpx, self.openai = list(script), httpx, openai
        self.chat = self
        self.completions = self
        self.with_raw_response = self
        self.sent = []

    def create(self, **kw):
        self.sent.append(kw)
        kind = self.script.pop(0)
        req = self.httpx.Request("POST", "https://example.invalid/chat/completions")
        if kind == 429:
            resp = self.httpx.Response(429, request=req, headers={"x-request-id": "fake"},
                                       json={"error": {"code": "Throttling", "message": "Too many requests."}})
            raise self.openai.RateLimitError("rate limited", response=resp, body=resp.json())
        body = {"id": "fake", "object": "chat.completion", "created": 0, "model": "qwen3.8-flash",
                "choices": [{"index": 0, "finish_reason": "stop",
                             "message": {"role": "assistant", "content": kind}}],
                "usage": {"prompt_tokens": 306, "completion_tokens": 14, "total_tokens": 320}}
        resp = self.httpx.Response(200, request=req, json=body, headers={"x-request-id": "fake"})

        class Raw:
            status_code, headers = 200, resp.headers

            def parse(_self):
                from openai.types.chat import ChatCompletion
                return ChatCompletion.model_validate(body)
        return Raw()


def offline():
    import qwen_client as qc
    waits = []
    fake = _Fake(["A=10, B=60, C=30", "I would stay home.", "A=33, B=33, C=33", 429, "A=0, B=50, C=50",
                  "x", "y", "z", "A=1, B=1, C=1"])
    q = qc.QwenArm2(fake, max_requests=8, sleep=waits.append)
    r1, r2_, r3, r4 = q.ask("p1"), q.ask("p2"), q.ask("p3"), q.ask("p4")
    assert r1["valid_first"] and r1["final"]["raw"] == [10, 60, 30] and r1["retries"] == 0
    assert not r2_["valid_first"] and r2_["retries"] == 1 and r2_["final"]["sum"] == 99      # A64 98-102
    assert r3["valid_first"] and r3["final"]["raw"] == [0, 50, 50] and waits == [qc.RETRY_WAIT_S]
    assert r4["fallback"] and r4["retries"] == 2                                              # A61
    try:
        q.ask("p5")
        raise AssertionError("cap not enforced")
    except qc.RequestCapReached:
        pass
    assert q.n_requests == 8 and all(k["extra_body"] == {"enable_thinking": False} for k in fake.sent)
    assert all(k["model"] == "qwen3.8-flash" and "temperature" not in k and "top_p" not in k for k in fake.sent)
    assert q.requests[3]["http_status"] == 429 and q.requests[3]["error"]["code"] == "Throttling"
    print(f"offline client check OK: {q.n_requests} fake requests; valid / A64-rescaled / 429-retry / "
          f"A61-fallback / cap paths; request kwargs {sorted(fake.sent[0])}")


def run():
    import qwen_client as qc
    sm = json.load(open(PROMPTS_FILE))["prompts"]
    plan()
    q = qc.QwenArm2(qc.make_client(), max_requests=MAX_REQUESTS)
    decisions, t0 = [], time.time()
    try:
        for rep in range(REPEATS):
            for s in sm:                                         # one at a time
                d = q.ask(s["prompt"])
                decisions.append(dict(id=s["id"], repeat=rep, **d))
                print(f"  {s['id']:8s} rep {rep}: {q.requests[-1]['text']!r} "
                      f"({q.requests[-1]['seconds']:.2f}s)", flush=True)
    except qc.RequestCapReached as e:
        print(f"STOPPED: {e}")
    json.dump(dict(model=qc.MODEL, extra_body=qc.EXTRA_BODY, max_tokens=qc.MAX_TOKENS,
                   wall_s=time.time() - t0, n_requests=q.n_requests, decisions=decisions,
                   requests=q.requests), open(LOG_FILE, "w"), indent=1)
    print(f"{q.n_requests} requests in {time.time() - t0:.0f}s; log {os.path.relpath(LOG_FILE, ROOT)}")


def score():
    d = json.load(open(LOG_FILE))
    sm = {s["id"]: s for s in json.load(open(PROMPTS_FILE))["prompts"]}
    reqs = {r["i"]: r for r in d["requests"]}
    dec = d["decisions"]
    print(f"requests {d['n_requests']}; decisions {len(dec)}; valid first {sum(x['valid_first'] for x in dec)}/"
          f"{len(dec)}; fallbacks {sum(x['fallback'] for x in dec)}")
    st = [r["http_status"] for r in d["requests"]]
    print(f"HTTP statuses {sorted(set(st))}; non-200 {sum(s != 200 for s in st)}")
    u = [r["usage"] for r in d["requests"] if r.get("usage")]
    reas = [((x.get("completion_tokens_details") or {}).get("reasoning_tokens")) for x in u]
    print(f"prompt tokens {min(x['prompt_tokens'] for x in u)}-{max(x['prompt_tokens'] for x in u)}; completion "
          f"{min(x['completion_tokens'] for x in u)}-{max(x['completion_tokens'] for x in u)}; reasoning tokens "
          f"{sorted(set(map(str, reas)))}; reasoning text chars {sorted(set(r.get('reasoning_text_chars', 0) for r in d['requests']))}")
    secs = [r["seconds"] for r in d["requests"]]
    print(f"seconds per request {min(secs):.2f}-{max(secs):.2f} (mean {np.mean(secs):.2f}); wall {d['wall_s']:.0f}s")
    hdr = sorted({k for r in d["requests"] for k in r.get("headers", {})})
    print(f"response header names: {hdr}")
    print("\nid | action | rep 0 | rep 1 | same | caution 0 / 1")
    caution = {}
    for sid in sm:
        rows = [x for x in dec if x["id"] == sid]
        txt = [reqs[x["attempts"][-1]]["text"] for x in rows]
        cs = [1 - x["final"]["normal"] if x["final"] else None for x in rows]
        caution[sid] = cs
        print(f"{sid:8s} | {sm[sid]['fields']['current_action']:11s} | {' | '.join(map(repr, txt))} | "
              f"{len(set(txt)) == 1} | {' / '.join('-' if c is None else f'{c:.2f}' for c in cs)}")
    old_ge = sum(np.mean(caution[f"d{dd}_b8"]) >= np.mean(caution[f"d{dd}_b2"]) for dd in SMOKE_DAYS)
    print(f"band-8 caution >= band-2 on {old_ge}/{len(SMOKE_DAYS)} days (mean over repeats)")


if __name__ == "__main__":
    for flag, fn in (("--write-v2", write_v2), ("--examples", examples), ("--plan", plan),
                     ("--offline", offline), ("--run", run), ("--score", score)):
        if flag in sys.argv:
            fn()

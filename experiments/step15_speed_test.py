"""
Pilot step 2, speed test (register C59 Step 2; results C60).

Levels 1, 2, 4, 8 concurrent requests, 15 requests each, in that order; the 10 smoke prompts
(results/step13/smoke_prompts.json) cycled; A79 settings (src/qwen_client.py); one HTTP request per
call, NO retries of any kind (transport or A61); every non-200 reply logged with its headers. If a
level has any error, that level is finished and no higher level is run. Ledger
results/pilot/step2/requests.jsonl, hard cap 60 (counts survive restarts).

Per request: wall-clock start and end (so a level's wall time is measured, not summed), total
seconds, and the server-side headers req-cost-time and x-envoy-upstream-service-time (ms).

  --offline   fake client with a fake delay, no network: concurrency, cap and stop-after-error checks
  --plan      print planned calls and rough cost
  --run       THE ONLY MODE THAT SPENDS CREDITS
  --score     summarise results/pilot/step2/speed_log.json

Usage:  py -3.14 experiments/step15_speed_test.py --offline | --plan | --run | --score
"""
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
PROMPTS_FILE = os.path.join(ROOT, "results", "step13", "smoke_prompts.json")
OUT = os.path.join(ROOT, "results", "pilot", "step2")
LEDGER_FILE = os.path.join(OUT, "requests.jsonl")
LOG_FILE = os.path.join(OUT, "speed_log.json")
LEVELS = (1, 2, 4, 8)
PER_LEVEL = 15
MAX_REQUESTS = 60                                     # approved for step 2 (Max)
PAYG_PER_CALL = 0.00005304                            # C57
SERVER_HEADERS = ("req-cost-time", "x-envoy-upstream-service-time")


def run_levels(q, prompts, levels=LEVELS, per_level=PER_LEVEL, log=print):
    """Returns (records per level, stop reason). One request per task; no retries."""
    import qwen_client as qc
    out, stop = {}, None
    for level in levels:
        tasks = [(j, prompts[j % len(prompts)]) for j in range(per_level)]

        def one(task, level=level):
            j, s = task
            try:
                rec = q._request(s["prompt"], key=f"L{level}|{j}|{s['id']}")
            except qc.RequestCapReached as e:
                return dict(level=level, j=j, id=s["id"], cap_reached=str(e))
            rec = dict(rec, level=level, j=j, id=s["id"], parsed=qc.parse(rec["text"]) if rec["error"] is None else None)
            return rec

        with ThreadPoolExecutor(max_workers=level) as pool:
            recs = list(pool.map(one, tasks))
        out[level] = recs
        errs = [r for r in recs if r.get("cap_reached") or r.get("error") or r.get("http_status") != 200]
        log(f"level {level}: {len(recs)} requests, {len(errs)} errors")
        if any(r.get("cap_reached") for r in recs):
            stop = f"request cap reached at level {level}"
            break
        if errs:
            stop = f"error(s) at level {level}; no higher level run"
            break
    return out, stop


def summarise(levels_recs):
    rows = {}
    for level, recs in levels_recs.items():
        ok = [r for r in recs if not r.get("cap_reached")]
        secs = np.array([r["seconds"] for r in ok])
        wall = max(r["t_end"] for r in ok) - min(r["t_start"] for r in ok)
        srv = {h: [float(r["headers"][h]) / 1000 for r in ok if h in r.get("headers", {})] for h in SERVER_HEADERS}
        rows[level] = dict(
            n=len(ok), errors=sum(1 for r in recs if r.get("cap_reached") or r.get("error") or r.get("http_status") != 200),
            statuses=sorted({str(r.get("http_status")) for r in ok}),
            median_s=float(np.median(secs)), p95_s=float(np.percentile(secs, 95)), min_s=float(secs.min()),
            max_s=float(secs.max()), wall_s=float(wall), rps=len(ok) / wall,
            valid=sum(1 for r in ok if r.get("parsed")),
            **{f"{h}_median_s": (float(np.median(v)) if v else None) for h, v in srv.items()},
            **{f"{h}_n": len(v) for h, v in srv.items()},
            client_minus_envoy_median_s=(float(np.median([r["seconds"] - float(r["headers"]["x-envoy-upstream-service-time"]) / 1000
                                                         for r in ok if "x-envoy-upstream-service-time" in r.get("headers", {})]))
                                         if srv["x-envoy-upstream-service-time"] else None),
            error_details=[dict(status=r.get("http_status"), error=r.get("error"), headers=r.get("headers"))
                           for r in recs if r.get("error") or r.get("http_status") != 200])
    return rows


def print_rows(rows):
    print("level | n | errors | median s | p95 s | min-max s | wall s | req/s | server req-cost median s | "
          "envoy upstream median s | client - envoy median s | valid replies")
    for level, r in rows.items():
        print(f"{level} | {r['n']} | {r['errors']} | {r['median_s']:.3f} | {r['p95_s']:.3f} | {r['min_s']:.2f}-{r['max_s']:.2f} | "
              f"{r['wall_s']:.2f} | {r['rps']:.2f} | {r['req-cost-time_median_s']} | "
              f"{r['x-envoy-upstream-service-time_median_s']} | {r['client_minus_envoy_median_s']} | {r['valid']}/{r['n']}")
        for e in r["error_details"]:
            print(f"    error: {e}")


class _FakeConcurrent:
    """Offline stand-in for openai.OpenAI: fixed delay, thread-safe, optional injected 429."""

    def __init__(self, delay, fail_at=()):
        import httpx2 as httpx
        import openai
        self.httpx, self.openai, self.delay, self.fail_at = httpx, openai, delay, set(fail_at)
        self.chat = self.completions = self.with_raw_response = self
        self.lock, self.n, self.active, self.max_active = threading.Lock(), 0, 0, 0

    def create(self, **kw):
        with self.lock:
            self.n += 1
            n = self.n
            self.active += 1
            self.max_active = max(self.max_active, self.active)
        time.sleep(self.delay)
        with self.lock:
            self.active -= 1
        req = self.httpx.Request("POST", "https://example.invalid/chat/completions")
        hdr = {"x-request-id": f"fake{n}", "req-cost-time": str(int(self.delay * 900)),
               "x-envoy-upstream-service-time": str(int(self.delay * 950))}
        if n in self.fail_at:
            resp = self.httpx.Response(429, request=req, headers=hdr,
                                       json={"error": {"code": "Throttling", "message": "Too many requests."}})
            raise self.openai.RateLimitError("rate limited", response=resp, body=resp.json())
        body = {"id": f"fake{n}", "object": "chat.completion", "created": 0, "model": "qwen3.8-flash",
                "choices": [{"index": 0, "finish_reason": "stop",
                             "message": {"role": "assistant", "content": "A=10, B=60, C=30"}}],
                "usage": {"prompt_tokens": 317, "completion_tokens": 13, "total_tokens": 330}}
        headers = self.httpx.Headers(hdr)

        class Raw:
            status_code = 200

            def __init__(self):
                self.headers = headers

            def parse(_self):
                from openai.types.chat import ChatCompletion
                return ChatCompletion.model_validate(body)
        return Raw()


def offline():
    import tempfile
    import qwen_client as qc
    prompts = [dict(id=f"p{i}", prompt=f"prompt {i}") for i in range(10)]
    quiet = lambda *a: None  # noqa: E731
    with tempfile.TemporaryDirectory() as tmp:
        # 1. all levels, concurrency real, cap exactly used
        fake = _FakeConcurrent(0.05)
        q = qc.QwenArm2(fake, max_requests=60, ledger_path=os.path.join(tmp, "a.jsonl"))
        recs, stop = run_levels(q, prompts, log=quiet)
        rows = summarise(recs)
        assert stop is None and list(recs) == [1, 2, 4, 8] and q.n_requests == 60 and fake.n == 60
        assert fake.max_active == 8 and all(r["errors"] == 0 for r in rows.values())
        assert rows[8]["wall_s"] < 0.5 * sum(r["seconds"] for r in recs[8])          # measured, not summed
        assert rows[1]["wall_s"] > 0.9 * sum(r["seconds"] for r in recs[1])
        keys = [json.loads(x)["key"] for x in open(os.path.join(tmp, "a.jsonl"))]
        assert len(keys) == len(set(keys)) == 60
        # 2. an error at level 2 -> level 2 finished, levels 4 and 8 not run, no retry
        fake = _FakeConcurrent(0.02, fail_at={20})
        q = qc.QwenArm2(fake, max_requests=60, ledger_path=os.path.join(tmp, "b.jsonl"))
        recs, stop = run_levels(q, prompts, log=quiet)
        assert list(recs) == [1, 2] and len(recs[2]) == 15 and fake.n == 30 and q.n_requests == 30
        assert "level 2" in stop and summarise(recs)[2]["errors"] == 1
        # 3. cap across a restart: 50 lines already in the ledger -> only 10 more requests
        path = os.path.join(tmp, "c.jsonl")
        led = qc.Ledger(path)
        for _ in range(50):
            led.reserve(60, dict(key="earlier"))
        fake = _FakeConcurrent(0.01)
        q = qc.QwenArm2(fake, max_requests=60, ledger_path=path)
        recs, stop = run_levels(q, prompts, log=quiet)
        assert fake.n == 10 and q.n_requests == 60 and "cap" in stop
    print(f"offline speed-test check OK: 60 fake requests over levels 1/2/4/8 (max {8} in flight; level-8 wall "
          f"{rows[8]['wall_s']:.2f}s vs level-1 {rows[1]['wall_s']:.2f}s for 15 x 0.05s); stop after an error at "
          f"level 2 (30 requests, no retry); cap 60 held with 50 earlier ledger lines (10 sent)")


def plan():
    n = len(LEVELS) * PER_LEVEL
    print(f"planned: levels {LEVELS} x {PER_LEVEL} requests = {n} requests (fewer if a level has an error); "
          f"no retries; hard cap {MAX_REQUESTS} in {os.path.relpath(LEDGER_FILE, ROOT)}")
    print(f"rough cost at pay-as-you-go prices (C57, ${PAYG_PER_CALL}/call): ${n * PAYG_PER_CALL:.4f}. Token Plan "
          f"bills Credits; no Credit rate is published for qwen3.8-flash.")


def run():
    import qwen_client as qc
    prompts = json.load(open(PROMPTS_FILE))["prompts"]
    plan()
    q = qc.QwenArm2(qc.make_client(), max_requests=MAX_REQUESTS, ledger_path=LEDGER_FILE)
    t0 = time.time()
    recs, stop = run_levels(q, prompts)
    json.dump(dict(settings=qc.SETTINGS, levels=list(recs), stop=stop, wall_total_s=time.time() - t0,
                   n_requests=q.n_requests, records={str(k): v for k, v in recs.items()}),
              open(LOG_FILE, "w"), indent=1)
    print(f"stop: {stop}; {q.n_requests} requests in ledger; log {os.path.relpath(LOG_FILE, ROOT)}")


def score():
    d = json.load(open(LOG_FILE))
    recs = {int(k): v for k, v in d["records"].items()}
    rows = summarise(recs)
    print(f"stop: {d['stop']}; requests {d['n_requests']}; total wall {d['wall_total_s']:.1f}s")
    print_rows(rows)
    ok = [lv for lv, r in rows.items() if r["errors"] == 0]
    print(f"operating concurrency (highest level with 0 errors, C59): {max(ok) if ok else None}")
    json.dump({str(k): v for k, v in rows.items()}, open(os.path.join(OUT, "speed_scores.json"), "w"), indent=1)


if __name__ == "__main__":
    for flag, fn in (("--offline", offline), ("--plan", plan), ("--run", run), ("--score", score)):
        if flag in sys.argv:
            fn()

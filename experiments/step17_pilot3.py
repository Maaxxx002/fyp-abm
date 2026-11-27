"""
Pilot step 3 (register C59 Steps 3a-3c; results C62). Concurrency 8, A79 settings, one ledger per
step (results/pilot/step3a|3b|3c/requests.jsonl).

  3a  A62 checks on v2: results/pilot/situations_a62.json (file hash checked against C59, every
      prompt re-rendered and compared), 14 situations x 3 repeats = 42 decisions, cap 50; A61/A64
      via src/qwen_client.py. Scored as C37: caution c = 1 - P(normal), mean over valid replies,
      strict comparison of means, ties pass "at least": (i) c(D125) > c(D0) for both bands;
      (ii) c(band 8) >= c(band 2) in all 7 histories; (iii) c(Trise) >= c(Tfall) for both bands;
      (iv) every decision valid within A61's attempts (first-attempt validity reported alongside).
  freeze-v2  only if (i)-(iv) all pass: byte copies of prompts/v2/* into prompts/frozen_v2/.
  3b  K = 5 arm-3 rules from prompts/frozen_v2/arm3_instruction_v2.txt; max_tokens 8192;
      finish_reason "length" = failed generation; A53 checks exactly as
      experiments/step5_arm3_generate.py (its code, with the field list switched to PerceptionV2
      and the grid's population to 15,000); a rule is regenerated only after a failed check (A51),
      every attempt logged; cap 15. Rules 1-5 are first generated in parallel, then each failed
      rule again, round by round. Frozen per A54 in src/arm3_rules/qwen_v2/ only if all 5 pass.
  3c  repeat pilot: results/pilot/situations_repeat.json (hash checked), 20 x 20 = 400 decisions
      in the order of a permutation drawn with SHUFFLE_SEED, cap 420. Scored with src/reuse_rule.py.

Modes: --offline, --plan3a, --run3a, --score3a, --freeze-v2, --plan3b, --run3b, --plan3c, --run3c,
       --score3c.   Usage:  py -3.14 experiments/step17_pilot3.py <mode>
"""
import dataclasses
import datetime
import hashlib
import json
import os
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, HERE)
import render_v2 as r2  # noqa: E402
from perception import PerceptionV2  # noqa: E402

PILOT = os.path.join(ROOT, "results", "pilot")
A62_FILE, A62_SHA = os.path.join(PILOT, "situations_a62.json"), "5ba91ee7bf9e31121f7398a9f4696928030b3f842730f5e62d88a693b8a50f70"
REP_FILE, REP_SHA = os.path.join(PILOT, "situations_repeat.json"), "8ce24dc03aee1340e407485c3c223e81f041c61c82b47a74ea637601d7f327c0"
V2, FROZEN_V2 = os.path.join(ROOT, "prompts", "v2"), os.path.join(ROOT, "prompts", "frozen_v2")
ARM3_V2_SHA = "a4c50433aff063419169c3753e1569cb234dd60bc0690ce286a748f810bb7ed9"     # C58
ARM2_V2_SHA = "fc75ff228eec760454b2a63f98a09a7be756791a50d6b54395f5029152533259"
RULE_DIR = os.path.join(ROOT, "src", "arm3_rules", "qwen_v2")
CONC = 8
PAYG_PER_CALL = 0.00005304                                       # C57 (arm-2 sized prompt)
CAP = {"3a": 50, "3b": 15, "3c": 420, "3a_rescore": 300}
REPEATS_3A, REPEATS_3C, REPEATS_3A_RESCORE = 3, 20, 20       # C59; C63
SHUFFLE_SEED = 20261128
K_RULES, ARM3_MAX_TOKENS = 5, 8192
HISTS = ("D0", "D4", "D15", "D63", "D125", "Trise", "Tfall")


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def step_dir(step):
    return os.path.join(PILOT, f"step{step}")


def load_situations(path, want_sha):
    data = open(path, encoding="utf-8").read()
    assert sha(data) == want_sha, f"{path}: SHA-256 differs from C59"
    sits = json.loads(data)["situations"]
    for s in sits:
        assert sha(s["prompt"]) == s["prompt_sha256"], s["id"]
        assert r2.render(PerceptionV2(**s["fields"])) == s["prompt"], f"{s['id']}: renderer changed"
    return sits


def ask_all(q, tasks, conc=CONC):
    """tasks: [(key, prompt)]. Returns one result per task, in task order (concurrent)."""
    import qwen_client as qc

    def one(t):
        try:
            return dict(key=t[0], **q.ask(t[1], key=t[0]))
        except qc.RequestCapReached as e:
            return dict(key=t[0], cap_reached=str(e))
    with ThreadPoolExecutor(max_workers=conc) as pool:
        return list(pool.map(one, tasks))


def request_stats(q):
    rs = q.requests
    if not rs:
        return {}
    u = [r["usage"] for r in rs if r.get("usage")]
    return dict(requests_this_session=len(rs), requests_in_ledger=q.n_requests,
                statuses=sorted({str(r.get("http_status")) for r in rs}),
                errors=[dict(status=r.get("http_status"), error=r.get("error")) for r in rs if r.get("error")],
                prompt_tokens=[min(x["prompt_tokens"] for x in u), max(x["prompt_tokens"] for x in u)] if u else None,
                completion_tokens=[min(x["completion_tokens"] for x in u), max(x["completion_tokens"] for x in u)] if u else None,
                prompt_tokens_total=sum(x["prompt_tokens"] for x in u), completion_tokens_total=sum(x["completion_tokens"] for x in u),
                reasoning_details=sorted({str(x.get("completion_tokens_details")) for x in u}),
                reasoning_text_chars=sorted({r.get("reasoning_text_chars", 0) for r in rs}),
                finish_reasons=sorted({str(r.get("finish_reason")) for r in rs}),
                wall_s=max(r["t_end"] for r in rs) - min(r["t_start"] for r in rs),
                seconds_median=float(np.median([r["seconds"] for r in rs])))


def save_run(step, q, results, extra=None):
    out = dict(settings=q.settings, results=results, requests=q.requests, stats=request_stats(q), **(extra or {}))
    json.dump(out, open(os.path.join(step_dir(step), "run.json"), "w"), indent=1)
    return out


def text_of(q_requests, i):
    return next(r["text"] for r in q_requests if r["i"] == i)


# ---------------------------------------------------------------- 3a
def tasks_3a(sits, repeats=REPEATS_3A):
    return [(f"{s['id']}|rep{k}", s["prompt"]) for k in range(repeats) for s in sits]


def plan(step, n):
    print(f"step {step}: planned {n} decisions (one request each if every reply is valid), concurrency {CONC}, hard cap "
          f"{CAP[step]} requests in results/pilot/step{step}/requests.jsonl")
    print(f"  rough cost at pay-as-you-go prices (C57, ${PAYG_PER_CALL}/arm-2 call): ${n * PAYG_PER_CALL:.4f} "
          f"(arm-3 calls are larger, see --plan3b). Token Plan bills Credits; rate not published.")


def run_3a(client_factory=None, step="3a", repeats=REPEATS_3A):
    import qwen_client as qc
    sits = load_situations(A62_FILE, A62_SHA)
    tasks = tasks_3a(sits, repeats)
    plan(step, len(tasks))
    q = qc.QwenArm2((client_factory or qc.make_client)(), max_requests=CAP[step],
                    ledger_path=os.path.join(step_dir(step), "requests.jsonl"))
    res = ask_all(q, tasks)
    out = save_run(step, q, res)
    print(json.dumps(out["stats"], indent=1))


def score_3a(path=None, quiet=False, results=None, out_name="scores.json", stats=None):
    d = dict(results=results, stats=stats) if results is not None else json.load(open(path or os.path.join(step_dir("3a"), "run.json")))
    by = {}
    for r in d["results"]:
        sid = r["key"].split("|")[0]
        by.setdefault(sid, []).append(r)
    rows, lines = {}, []
    for h in HISTS:
        for band in (2, 8):
            sid = f"{h}_b{band}"
            rs = by[sid]
            fin = [r["final"] for r in rs if r.get("final")]
            c = [1 - f["normal"] for f in fin]
            rows[sid] = dict(c=float(np.mean(c)) if c else None, c_sd=float(np.std(c, ddof=1)) if len(c) > 1 else None,
                             stay=float(np.mean([f["stay_home"] for f in fin])) if fin else None,
                             n=len(fin), N=len(rs), valid_first=sum(bool(r.get("valid_first")) for r in rs),
                             retries=sum(r.get("retries", 0) for r in rs), raw=[f["raw"] for f in fin],
                             fallbacks=sum(bool(r.get("fallback")) for r in rs),
                             transport_errors=sum(r.get("transport_error") is not None for r in rs),
                             cap=sum("cap_reached" in r for r in rs), cs=c)
            x = rows[sid]
            lines.append(f"{sid:9s} | {' '.join('/'.join(map(str, v)) for v in x['raw']):30s} | c {x['c']:.3f} (sd "
                         f"{x['c_sd']:.3f}) | P(stay) {x['stay']:.3f} | valid {x['n']}/{x['N']} | first {x['valid_first']}/"
                         f"{x['N']} | retries {x['retries']}" if x["c"] is not None else f"{sid}: no valid replies")
    c = {k: v["c"] for k, v in rows.items()}
    ok = all(v is not None for v in c.values())
    crit = dict(
        i=ok and all(c[f"D125_b{b}"] > c[f"D0_b{b}"] for b in (2, 8)),
        ii=ok and all(c[f"{h}_b8"] >= c[f"{h}_b2"] for h in HISTS),
        ii_count=sum(c[f"{h}_b8"] >= c[f"{h}_b2"] for h in HISTS) if ok else None,
        iii=ok and all(c[f"Trise_b{b}"] >= c[f"Tfall_b{b}"] for b in (2, 8)),
        iv=all(v["n"] == v["N"] and v["fallbacks"] == 0 for v in rows.values()),
        valid_first=sum(v["valid_first"] for v in rows.values()), decisions=sum(v["N"] for v in rows.values()))
    crit["all_pass"] = crit["i"] and crit["ii"] and crit["iii"] and crit["iv"]
    if not quiet:
        print("situation | replies | caution | P(stay) | validity")
        print("\n".join(lines))
        print(f"(i) c(D125) > c(D0): {crit['i']} [b2 {c['D125_b2']:.3f} vs {c['D0_b2']:.3f}; b8 {c['D125_b8']:.3f} vs "
              f"{c['D0_b8']:.3f}]")
        print(f"(ii) c(b8) >= c(b2) in all 7: {crit['ii']} [{crit['ii_count']}/7; failing: "
              f"{[h for h in HISTS if not c[f'{h}_b8'] >= c[f'{h}_b2']]}]")
        print(f"(iii) c(Trise) >= c(Tfall): {crit['iii']} [b2 {c['Trise_b2']:.3f} vs {c['Tfall_b2']:.3f}; b8 "
              f"{c['Trise_b8']:.3f} vs {c['Tfall_b8']:.3f}]")
        print(f"(iv) every decision valid within A61's attempts: {crit['iv']}; first-attempt valid "
              f"{crit['valid_first']}/{crit['decisions']}")
        print(f"ALL PASS: {crit['all_pass']}")
        print("differences in mean caution (SE = sqrt(s1^2/n1 + s2^2/n2), ddof 1):")
        for name, (x, y) in comparisons().items():
            dd, se = diff_se(rows[x]["cs"], rows[y]["cs"])
            print(f"  {name}: {dd:+.3f} (SE {se:.3f}; n {len(rows[x]['cs'])}/{len(rows[y]['cs'])})")
        if d.get("stats"):
            print(json.dumps(d["stats"], indent=1))
    json.dump(dict(rows=rows, criteria=crit,
                   differences={n: dict(zip(("diff", "se"), diff_se(rows[x]["cs"], rows[y]["cs"])))
                                for n, (x, y) in comparisons().items()}),
              open(os.path.join(os.path.dirname(path) if path else step_dir("3a"), out_name), "w"), indent=1)
    return rows, crit


def comparisons():
    """Every C59 3a comparison as (left, right): left should be >= (or > for (i)) right."""
    c = {f"(i) D125 - D0, band {b}": (f"D125_b{b}", f"D0_b{b}") for b in (2, 8)}
    c.update({f"(ii) band 8 - band 2, {h}": (f"{h}_b8", f"{h}_b2") for h in HISTS})
    c.update({f"(iii) Trise - Tfall, band {b}": (f"Trise_b{b}", f"Tfall_b{b}") for b in (2, 8)})
    return c


def diff_se(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    return float(x.mean() - y.mean()), float(np.sqrt(x.var(ddof=1) / len(x) + y.var(ddof=1) / len(y)))


def run_3a_rescore():
    run_3a(step="3a_rescore", repeats=REPEATS_3A_RESCORE)


def score_3a_rescore():
    rows, crit = score_3a(path=os.path.join(step_dir("3a_rescore"), "run.json"))
    print("\n===== information only: pooled 23 repeats (C62's 3 + C63's 20)")
    pooled = (json.load(open(os.path.join(step_dir("3a"), "run.json")))["results"]
              + json.load(open(os.path.join(step_dir("3a_rescore"), "run.json")))["results"])
    score_3a(results=pooled, out_name="scores_pooled23.json", path=os.path.join(step_dir("3a_rescore"), "run.json"))
    return rows, crit


def freeze_v2(c63=False):
    """C59: freeze only if 3a passes. C63 (Max, 27 Nov 2026): after the re-score, freeze whatever
    its verdict; the A62 checks become a reported diagnostic if any fails."""
    if c63:
        _, crit = score_3a(path=os.path.join(step_dir("3a_rescore"), "run.json"), quiet=True, out_name="scores.json")
        print(f"C63 freeze: re-score verdict all-pass = {crit['all_pass']} (frozen either way, C63)")
    else:
        _, crit = score_3a(quiet=True)
        assert crit["all_pass"], "3a did not pass (i)-(iv): v2 is NOT frozen"
    os.makedirs(FROZEN_V2, exist_ok=True)
    for name, want in (("arm2_template_v2.txt", ARM2_V2_SHA), ("arm3_instruction_v2.txt", ARM3_V2_SHA)):
        b = open(os.path.join(V2, name), "rb").read()
        assert hashlib.sha256(b).hexdigest() == want, f"draft {name} changed since C58"
        dst = os.path.join(FROZEN_V2, name)
        if os.path.exists(dst):
            assert open(dst, "rb").read() == b, f"{dst} is frozen and differs; not overwritten"
        else:
            open(dst, "wb").write(b)
        print(f"prompts/frozen_v2/{name}  sha256 {hashlib.sha256(b).hexdigest()}  {len(b.decode('utf-8'))} chars")


# ---------------------------------------------------------------- 3b
def arm3_checker():
    """step5's A53 checks, with the field list switched to PerceptionV2 and a v2 grid."""
    import itertools
    import step5_arm3_generate as g5
    from population import build_population
    g5.FIELDS = tuple(f.name for f in dataclasses.fields(PerceptionV2))
    pop = build_population(N=15_000, seed=0)
    vul = {b: float(pop.vulnerability[pop.age_band == b][0]) for b in range(10)}
    pts = []
    for day, d7, d7a, cum, norm, band, occ, eff, act in itertools.product(
            [0, 7, 60, 600], [0.0, 0.1, 3.6, 100.0], [0.0, 0.1, 3.6, 100.0], [0.0, 10.0, 3000.0], [0.0, 0.85, 1.0],
            [0, 2, 8, 9], [0.0, 0.41, 1.0], [0.0, 0.8, 1.0], ["stay_home", "precautions", "normal"]):
        pts.append(dict(deaths_7day_mean=d7, deaths_cumulative=cum, deaths_7day_mean_7d_ago=d7a, current_action=act,
                        social_norm=norm, age_band=band, vulnerability=vul[band], occupation_flex=occ,
                        response_efficacy=eff, population=15_000, day=day))
    n_a = len(pts)
    rng = np.random.default_rng(20261010)
    acts = ["stay_home", "precautions", "normal"]
    for _ in range(20000):
        pts.append(dict(
            deaths_7day_mean=float(rng.choice([0.0, rng.uniform(0, 5), rng.uniform(0, 1e4)])),
            deaths_cumulative=float(rng.choice([0.0, rng.uniform(0, 100), rng.uniform(0, 1e6)])),
            deaths_7day_mean_7d_ago=float(rng.choice([0.0, rng.uniform(0, 5), rng.uniform(0, 1e4)])),
            current_action=acts[rng.integers(3)], social_norm=float(rng.uniform(0, 1)),
            age_band=int(rng.integers(10)), vulnerability=float(rng.uniform(0, 1)),
            occupation_flex=float(rng.uniform(0, 1)), response_efficacy=float(rng.uniform(0, 1)),
            population=int(rng.choice([1, 15_000, 100000])), day=int(rng.integers(0, 10001))))
    return g5, pts, n_a


def generate_rules(q, instr, g5, pts, stage_dir, log=print):
    """Rounds of parallel attempts for the rules still missing; stops at the cap."""
    import qwen_client as qc
    os.makedirs(stage_dir, exist_ok=True)
    pending, done, attempts_log, attempt_no = list(range(1, K_RULES + 1)), {}, [], {k: 0 for k in range(1, K_RULES + 1)}
    stop = None
    while pending and stop is None:
        room = CAP["3b"] - q.n_requests
        batch = pending[:max(0, room)]
        if not batch:
            stop = "cap reached"
            break
        for k in batch:
            attempt_no[k] += 1

        def one(k):
            try:
                return k, q._attempt(instr, key=f"rule{k}|attempt{attempt_no[k]}")
            except qc.RequestCapReached as e:
                return k, dict(cap_reached=str(e))
        with ThreadPoolExecutor(max_workers=min(CONC, len(batch))) as pool:
            got = list(pool.map(one, batch))
        for k, rec in got:
            if "cap_reached" in rec:
                stop = "cap reached"
                continue
            when = datetime.datetime.fromtimestamp(rec["t_start"], datetime.timezone.utc).isoformat(timespec="seconds")
            entry = dict(rule=k, attempt=attempt_no[k], utc=when, i=rec["i"], http_status=rec.get("http_status"),
                         finish_reason=rec.get("finish_reason"), model_served=rec.get("model"),
                         response_id=rec.get("response_id"), usage=rec.get("usage"), error=rec.get("error"))
            if rec.get("error"):
                ok, checks = False, dict(transport_error=rec["error"])
            elif rec["finish_reason"] == "length":
                ok, checks = False, dict(finish_reason="length (failed generation, C59)")
            elif rec["finish_reason"] != "stop":
                ok, checks = False, dict(finish_reason=f"finish_reason {rec['finish_reason']}")
            else:
                code = g5.extract_code(rec["text"])
                ok, checks = g5.mechanical_checks(code, pts)
                entry.update(code_sha256=sha(code), reply_sha256=sha(rec["text"]),
                             fenced=rec["text"].strip() != code.strip())
            entry.update(ok=ok, checks=checks)
            attempts_log.append(entry)
            tag = f"rule_{k}" if ok else f"rejected_rule_{k}_attempt_{attempt_no[k]}"
            if rec.get("text") is not None:
                with open(os.path.join(stage_dir, f"{tag}_reply.txt"), "w", encoding="utf-8", newline="") as f:
                    f.write(rec["text"])
            if ok:
                with open(os.path.join(stage_dir, f"rule_{k}.py"), "w", encoding="utf-8", newline="") as f:
                    f.write(g5.extract_code(rec["text"]))
                done[k] = entry
                pending.remove(k)
            u = rec.get("usage") or {}
            log(f"rule {k} attempt {attempt_no[k]}: {'PASS' if ok else 'FAIL'} {checks} finish {rec.get('finish_reason')} "
                f"tokens {u.get('prompt_tokens')}/{u.get('completion_tokens')}")
    return done, pending, attempts_log, stop


def run_3b(client_factory=None, stage=None, rule_dir=RULE_DIR, log=print, instr_path=None):
    import qwen_client as qc
    path = instr_path or os.path.join(FROZEN_V2, "arm3_instruction_v2.txt")
    instr = open(path, encoding="utf-8", newline="").read()
    assert sha(instr) == ARM3_V2_SHA, "frozen arm-3 instruction v2 hash mismatch"
    g5, pts, n_a = arm3_checker()
    log(f"grid: {len(pts)} points ({n_a} structured + {len(pts) - n_a} random)")
    sd = step_dir("3b") if stage is None else stage
    q = qc.QwenArm2((client_factory or qc.make_client)(), max_requests=CAP["3b"],
                    ledger_path=os.path.join(sd, "requests.jsonl"), max_tokens=ARM3_MAX_TOKENS)
    done, pending, alog, stop = generate_rules(q, instr, g5, pts, os.path.join(sd, "staged"), log=log)
    out = save_run("3b", q, dict(done=done, pending=pending, stop=stop), extra=dict(attempts=alog)) if stage is None else None
    if pending:
        log(f"STOP: rules {pending} still fail after {q.n_requests} requests (cap {CAP['3b']}); nothing frozen")
        return done, pending, alog
    os.makedirs(rule_dir, exist_ok=True)
    manifest = dict(rules=[], prompt_file="prompts/frozen_v2/arm3_instruction_v2.txt", prompt_sha256=ARM3_V2_SHA,
                    model_requested=qc.MODEL, settings=q.settings, system_prompt=None, grid_points=len(pts),
                    generation_log=alog, frozen_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"))
    for k in range(1, K_RULES + 1):
        for suffix in (".py", "_reply.txt"):
            src, dst = os.path.join(sd, "staged", f"rule_{k}{suffix}"), os.path.join(rule_dir, f"rule_{k}{suffix}")
            assert not os.path.exists(dst), f"{dst} exists: frozen rules are never rewritten"
            shutil.copyfile(src, dst)
        code = open(os.path.join(rule_dir, f"rule_{k}.py"), encoding="utf-8", newline="").read()
        e = done[k]
        manifest["rules"].append(dict(rule=k, file=f"src/arm3_rules/qwen_v2/rule_{k}.py", code_sha256=sha(code),
                                      reply_file=f"src/arm3_rules/qwen_v2/rule_{k}_reply.txt", reply_sha256=e["reply_sha256"],
                                      attempts=e["attempt"], utc=e["utc"], model_served=e["model_served"],
                                      response_id=e["response_id"], usage=e["usage"], finish_reason=e["finish_reason"]))
        assert code_sha_ok(code, e)
    with open(os.path.join(rule_dir, "manifest.json"), "w", encoding="utf-8", newline="") as f:
        json.dump(manifest, f, indent=2)
    log(f"frozen {K_RULES} rules in {os.path.relpath(rule_dir, ROOT)}; {q.n_requests} requests")
    return done, pending, alog


def code_sha_ok(code, entry):
    return sha(code) == entry["code_sha256"]


# ---------------------------------------------------------------- 3c
def tasks_3c(sits):
    base = [(f"{s['id']}|rep{k}", s["prompt"]) for s in sits for k in range(REPEATS_3C)]
    order = np.random.default_rng(SHUFFLE_SEED).permutation(len(base))
    return [base[i] for i in order]


def run_3c(client_factory=None):
    import qwen_client as qc
    sits = load_situations(REP_FILE, REP_SHA)
    tasks = tasks_3c(sits)
    plan("3c", len(tasks))
    q = qc.QwenArm2((client_factory or qc.make_client)(), max_requests=CAP["3c"],
                    ledger_path=os.path.join(step_dir("3c"), "requests.jsonl"))
    res = ask_all(q, tasks)
    out = save_run("3c", q, res, extra=dict(shuffle_seed=SHUFFLE_SEED, order=[t[0] for t in tasks]))
    print(json.dumps(out["stats"], indent=1))


def score_3c(path=None):
    import reuse_rule as rr
    import step16_reuse_groups as s16
    from step14_pilot_inputs import PHASES
    d = json.load(open(path or os.path.join(step_dir("3c"), "run.json")))
    sits = {s["id"]: s for s in load_situations(REP_FILE, REP_SHA)}
    ans = {sid: [] for sid in sits}
    for r in d["results"]:
        if r.get("final"):
            ans[r["key"].split("|")[0]].append(r["final"])
    n_dec = len(d["results"])
    invalid_first = sum(not r.get("valid_first") for r in d["results"])
    fallbacks = sum(bool(r.get("fallback")) for r in d["results"])
    print(f"decisions {n_dec}; valid at first attempt {n_dec - invalid_first}/{n_dec}; retries "
          f"{sum(r.get('retries', 0) for r in d['results'])}; fallbacks {fallbacks}; transport errors "
          f"{sum(r.get('transport_error') is not None for r in d['results'])}; cap stops {sum('cap_reached' in r for r in d['results'])}")
    A = {sid: [f["stay_home"] for f in v] for sid, v in ans.items()}
    AB = {sid: [f["stay_home"] + f["precautions"] for f in v] for sid, v in ans.items()}
    print("\nsituation | phase | day | band | action | n | mean A | SD A (pp) | mean A+B | SD A+B (pp)")
    sdA = []
    for sid, s in sits.items():
        a, ab = np.array(A[sid]), np.array(AB[sid])
        sa = 0.0 if np.ptp(a) == 0 else float(a.std(ddof=1))
        sab = 0.0 if np.ptp(ab) == 0 else float(ab.std(ddof=1))
        sdA.append(100 * sa)
        print(f"{sid:9s} | {s['phase']:7s} | {s['day']:3d} | {s['fields']['age_band']} | {s['fields']['current_action']:11s} | "
              f"{len(a)} | {a.mean():.3f} | {100 * sa:.2f} | {ab.mean():.3f} | {100 * sab:.2f}")
    print(f"per-situation SD of A: median {np.median(sdA):.2f} pp, max {max(sdA):.2f} pp (n = {len(sdA)} situations)")
    groups, _ = s16.load_groups()
    sums = {stub: {p: rr.group_sums(groups[stub][p]) for p in PHASES} for stub in groups}
    out = {}
    for label, vals in (("A", A), ("A+B", AB)):
        by_phase = {p: [vals[sid] for sid, s in sits.items() if s["phase"] == p] for p in PHASES}
        out[label] = {}
        print(f"\n--- {label}: R_f(m) per stub and phase (mean sigma^2, mean b over the phase's 4 situations)")
        print("stub | phase | mean sigma^2 | mean b | R(1) | R(3) | R(1) 95% boot: repeats only | two-level")
        for stub in sums:
            for p in PHASES:
                st = [rr.situation_stats(v) for v in by_phase[p]]
                ms2, mb = float(np.mean([x[1] for x in st])), float(np.mean([x[2] for x in st]))
                r1, r3 = rr.phase_ratio(by_phase[p], sums[stub][p], 1), rr.phase_ratio(by_phase[p], sums[stub][p], 3)
                b1 = rr.bootstrap_ratio(by_phase[p], sums[stub][p], 1)
                b2 = rr.bootstrap_ratio_two_level(by_phase[p], sums[stub][p], 1)
                out[label][f"{stub}|{p}"] = dict(mean_sigma2=ms2, mean_b=mb, R1=r1, R3=r3, boot_repeats=b1, boot_two_level=b2)
                print(f"{stub} | {p} | {ms2:.5f} | {mb:.4f} | {r1:.3f} | {r3:.3f} | [{b1[0]:.3f}, {b1[1]:.3f}] | "
                      f"[{b2[0]:.3f}, {b2[1]:.3f}]")
        m = rr.choose_m(by_phase, sums)
        r1s = rr.all_ratios(by_phase, sums, 1)
        out[label]["m_choice"] = m
        out[label]["pass_m1"] = rr.passes(r1s)
        out[label]["pass_m3"] = rr.passes(rr.all_ratios(by_phase, sums, 3))
        callsm = {stub: rr.calls(groups[stub]["all"], m) for stub in groups}
        out[label]["calls_at_m"] = callsm
        tag = "the A78/A81 decision" if label == "A" else "same rule applied to A + B (finding only)"
        print(f"{label}: m = 1 passes {out[label]['pass_m1']}; m = 3 passes {out[label]['pass_m3']}; {tag}: m = {m}; "
              f"sum min(m, k) over C61's runs: {callsm}")
        mat = [vals[sid] for sid in sits]
        n_min = min(len(v) for v in mat)
        icc, ci = rr.icc_1_1([v[:n_min] for v in mat])
        out[label]["icc"] = dict(icc=icc, ci95=ci, n_situations=len(mat), repeats_used=n_min)
        print(f"ICC(1,1) {label}: {icc:.3f} [95% CI {ci[0]:.3f}, {ci[1]:.3f}] ({len(mat)} situations x {n_min} repeats)")
    out.update(sd_A_pp=dict(median=float(np.median(sdA)), max=float(max(sdA))), decisions=n_dec,
               invalid_first=invalid_first, fallbacks=fallbacks)
    json.dump(out, open(os.path.join(os.path.dirname(path) if path else step_dir("3c"), "scores.json"), "w"), indent=1)
    print("\n" + json.dumps(d["stats"], indent=1))
    return out


# ---------------------------------------------------------------- offline checks
class _FakeLLM:
    """Offline stand-in for openai.OpenAI: thread-safe; reply chosen by a function of the prompt."""

    def __init__(self, reply_fn, delay=0.01):
        import threading
        import httpx2 as httpx
        self.httpx, self.reply_fn, self.delay = httpx, reply_fn, delay
        self.chat = self.completions = self.with_raw_response = self
        self.lock, self.n, self.sent = threading.Lock(), 0, []

    def create(self, **kw):
        with self.lock:
            self.n += 1
            n = self.n
            self.sent.append(kw)
        time.sleep(self.delay)
        content, finish = self.reply_fn(kw["messages"][0]["content"], n)
        body = {"id": f"fake{n}", "object": "chat.completion", "created": 0, "model": "qwen3.8-flash",
                "choices": [{"index": 0, "finish_reason": finish, "message": {"role": "assistant", "content": content}}],
                "usage": {"prompt_tokens": 300, "completion_tokens": 13, "total_tokens": 313}}
        headers = self.httpx.Headers({"x-request-id": f"fake{n}"})

        class Raw:
            status_code = 200

            def __init__(self):
                self.headers = headers

            def parse(_self):
                from openai.types.chat import ChatCompletion
                return ChatCompletion.model_validate(body)
        return Raw()


GOOD_RULE = '''```python
import math

def decide(p):
    risk = 1 - math.exp(-p.deaths_7day_mean)
    home = 0.1 * risk * p.occupation_flex
    prec = 0.6 * risk
    return {"stay_home": home, "precautions": prec, "normal": 1 - home - prec}
```'''
BAD_RULE = '''```python
def decide(p):
    return {"stay_home": p.deaths_28day_mean, "precautions": 0.0, "normal": 1.0}
```'''


def offline():
    import tempfile
    import qwen_client as qc
    global PILOT
    with tempfile.TemporaryDirectory() as tmp:
        saved = PILOT
        PILOT = tmp
        try:
            # 3a scoring path on fake replies: older more cautious, D125 > D0, Trise > Tfall -> all pass
            def a62_reply(prompt, n):
                old = "70s" in prompt
                many = "125 people" in prompt
                rise = "before that, 5 died" in prompt
                a = 10 + (10 if old else 0) + (10 if many else 0) + (5 if rise else 0)
                return f"A={a}, B=50, C={50 - a}", "stop"
            fake = _FakeLLM(a62_reply)
            os.makedirs(step_dir("3a"))
            run_3a(client_factory=lambda: fake)
            rows, crit = score_3a(quiet=True)
            assert crit["all_pass"] and crit["decisions"] == 42 and fake.n == 42
            kw = fake.sent[0]
            assert kw["temperature"] == 0.7 and kw["extra_body"] == {"enable_thinking": False, "top_k": 20}
            # 3b: rule 2 fails A53 once (reads a v1 field), rule 4 truncated once -> 7 requests, all frozen
            def arm3_reply(prompt, n):
                assert "p.deaths_7day_mean (float" in prompt
                return {2: (BAD_RULE, "stop"), 4: ("```python\ndef decide(p):\n", "length")}.get(n, (GOOD_RULE, "stop"))
            fake3 = _FakeLLM(arm3_reply)
            draft = os.path.join(V2, "arm3_instruction_v2.txt")      # same bytes as the frozen copy (hash checked)
            done, pending, alog = run_3b(client_factory=lambda: fake3, stage=os.path.join(tmp, "b"),
                                         rule_dir=os.path.join(tmp, "rules"), log=lambda *a: None, instr_path=draft)
            assert not pending and fake3.n == 7 and len(alog) == 7
            assert sum(not e["ok"] for e in alog) == 2 and fake3.sent[0]["max_tokens"] == 8192
            assert any("non-Perception attribute" in str(e["checks"]) for e in alog)
            assert any("length" in str(e["checks"]) for e in alog)
            assert len(json.load(open(os.path.join(tmp, "rules", "manifest.json")))["rules"]) == 5
            # 3b cap: every attempt bad -> stops at 15 requests with rules pending, nothing frozen
            fake4 = _FakeLLM(lambda p, n: (BAD_RULE, "stop"))
            done, pending, alog = run_3b(client_factory=lambda: fake4, stage=os.path.join(tmp, "c"),
                                         rule_dir=os.path.join(tmp, "rules_c"), log=lambda *a: None, instr_path=draft)
            assert pending == [1, 2, 3, 4, 5] and fake4.n == 15 and not os.path.exists(os.path.join(tmp, "rules_c"))
            # 3c: fake answers with situation-specific noise; order shuffled; scoring runs end to end
            def rep_reply(prompt, n):
                mu = 5 + int(sha(prompt)[:4], 16) % 35
                a = int(np.clip(mu + n % 7 - 3, 0, 90))
                return f"A={a}, B={90 - a}, C=10", "stop"
            fake5 = _FakeLLM(rep_reply)
            os.makedirs(step_dir("3c"))
            run_3c(client_factory=lambda: fake5)
            d = json.load(open(os.path.join(step_dir("3c"), "run.json")))
            assert fake5.n == 400 and d["order"] == [t[0] for t in tasks_3c(load_situations(REP_FILE, REP_SHA))]
            assert d["order"][:3] != sorted(d["order"])[:3]
            out = score_3c()
            assert out["decisions"] == 400 and out["fallbacks"] == 0 and out["A"]["icc"]["repeats_used"] == 20
        finally:
            PILOT = saved
    print("\noffline step-3 check OK: 3a run + scoring (42 fake decisions, A79 settings); 3b regeneration after an "
          "A53 failure and a 'length' finish (7 requests, 5 rules frozen in a temp dir), cap stop at 15 with nothing "
          "frozen; 3c shuffled 400-decision run and full scoring")


if __name__ == "__main__":
    modes = {"--offline": offline, "--plan3a": lambda: plan("3a", len(tasks_3a(load_situations(A62_FILE, A62_SHA)))),
             "--run3a": run_3a, "--score3a": score_3a, "--freeze-v2": freeze_v2, "--run3b": run_3b,
             "--plan3a-rescore": lambda: plan("3a_rescore", len(tasks_3a(load_situations(A62_FILE, A62_SHA), REPEATS_3A_RESCORE))),
             "--run3a-rescore": run_3a_rescore, "--score3a-rescore": score_3a_rescore,
             "--freeze-v2-c63": lambda: freeze_v2(c63=True),
             "--plan3c": lambda: plan("3c", len(tasks_3c(load_situations(REP_FILE, REP_SHA)))),
             "--run3c": run_3c, "--score3c": score_3c}
    if "--plan3b" in sys.argv:
        print(f"step 3b: planned {K_RULES} generations (more only after a failed A53 check or a 'length' finish), up to "
              f"{CONC} in parallel, hard cap {CAP['3b']} requests in results/pilot/step3b/requests.jsonl; max_tokens "
              f"{ARM3_MAX_TOKENS}. Rough cost at pay-as-you-go prices: ~1,000 input + ~1,000 output tokens per call -> "
              f"~${(1000 * 0.15 + 1000 * 0.47) / 1e6:.5f}/call, ${K_RULES * (1000 * 0.15 + 1000 * 0.47) / 1e6:.4f} for 5, "
              f"${CAP['3b'] * (1000 * 0.15 + 1000 * 0.47) / 1e6:.4f} at the cap (assumed sizes, not measured)")
    for flag, fn in modes.items():
        if flag in sys.argv:
            fn()

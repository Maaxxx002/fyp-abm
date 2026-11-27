"""
Arm-2 LLM client for qwen3.8-flash via Alibaba's OpenAI-compatible endpoint (register A72).

Request settings (A72, A79): model qwen3.8-flash; temperature 0.7, top_p 0.8, presence_penalty 1.5
as top-level SDK arguments; extra_body={"enable_thinking": False, "top_k": 20} (top_k is not an
OpenAI standard parameter, so Alibaba's reference puts it in extra_body); max_tokens 1024 (A65's
implementation cap, so a reply cannot be cut off); no system prompt, the rendered prompt is the
single user message. The settings are recorded with every request.

Reply handling: A64 parsing; A61 retries (up to 2 more attempts after an invalid reply, then the
agent keeps its current action -- the caller applies that fallback). Transport errors (429, 5xx,
timeouts, connection errors): the SDK's own retries are off; the client waits RETRY_WAIT_S and
retries up to 2 times, logging each attempt.

Ledger (C59): every HTTP request is written to a JSONL ledger, one line per request, appended,
flushed and fsynced BEFORE the request is sent, under a lock (safe under concurrent requests).
The cap counts the lines already in the ledger, so a restart cannot exceed a step's total, and a
request interrupted in flight is still counted. Each request's outcome (tokens, seconds, status,
reply) is appended to the sibling file <ledger>.responses.jsonl when it completes.

SECURITY: the key and base URL are read from ENV_FILE at run time only. They are passed to the
SDK and never printed, logged, returned or written anywhere.
"""
import hashlib
import json
import os
import re
import threading
import time

ENV_FILE = os.environ.get("QWEN_ENV_FILE", r"C:\Users\Admin\Documents\QWENAPI\.env")
MODEL = "qwen3.8-flash"
MAX_TOKENS = 1024
SAMPLING = dict(temperature=0.7, top_p=0.8, presence_penalty=1.5)     # A79, top-level SDK arguments
EXTRA_BODY = {"enable_thinking": False, "top_k": 20}                   # A72, A79
SETTINGS = dict(model=MODEL, max_tokens=MAX_TOKENS, **SAMPLING, extra_body=EXTRA_BODY)
RETRY_WAIT_S = 60          # Alibaba rate-limit page: a 429 "usually recovers automatically within one minute"
TRANSPORT_RETRIES = 2
REPLY_RE = re.compile(r"^\s*A\s*=\s*(\d+)\s*,\s*B\s*=\s*(\d+)\s*,\s*C\s*=\s*(\d+)\s*$")
HIDDEN_HEADERS = ("set-cookie", "authorization", "cookie")


def parse(text):
    """A64: "A=a, B=b, C=c", whole numbers >= 0, valid if 98 <= a + b + c <= 102; rescaled."""
    m = REPLY_RE.match(text or "")
    if not m:
        return None
    a, b, c = (int(x) for x in m.groups())
    tot = a + b + c
    if not 98 <= tot <= 102:
        return None
    return dict(stay_home=a / tot, precautions=b / tot, normal=c / tot, raw=[a, b, c], sum=tot)


def _read_env(path):
    env = {}
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip().removeprefix("export ").strip()] = v.strip().strip('"').strip("'")
    return env


def make_client(env_file=ENV_FILE):
    from openai import OpenAI
    env = _read_env(env_file)
    return OpenAI(api_key=env["DASHSCOPE_API_KEY"], base_url=env["QWEN_BASE_URL"], max_retries=0,
                  timeout=120)


class RequestCapReached(RuntimeError):
    pass


class Ledger:
    """Append-only JSONL, one line per HTTP request, written before the request is sent."""

    def __init__(self, path):
        self.path = path
        self.responses_path = (path[:-6] if path.endswith(".jsonl") else path) + ".responses.jsonl"
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self.lock = threading.Lock()
        self.n = 0
        if os.path.exists(path):
            data = open(path, "rb").read()
            self.n = sum(1 for line in data.split(b"\n") if line.strip())   # a torn last line counts too
            if data and not data.endswith(b"\n"):
                with open(path, "ab") as f:
                    f.write(b"\n")

    def _append(self, path, obj):
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(obj) + "\n")
            f.flush()
            os.fsync(f.fileno())

    def reserve(self, cap, entry):
        with self.lock:
            if self.n >= cap:
                raise RequestCapReached(f"request cap {cap} reached ({self.n} requests in {self.path})")
            self.n += 1
            entry = dict(i=self.n, **entry)
            self._append(self.path, entry)
            return self.n

    def record(self, rec):
        with self.lock:
            self._append(self.responses_path, rec)


class QwenArm2:
    def __init__(self, client, max_requests, ledger_path, sleep=time.sleep, max_tokens=MAX_TOKENS):
        self.client, self.max_requests, self.sleep = client, max_requests, sleep
        self.max_tokens = max_tokens                       # arm 3 uses 8192 (C59 step 3b)
        self.settings = dict(SETTINGS, max_tokens=max_tokens)
        self.ledger = Ledger(ledger_path)
        self.requests = []          # this session's request records, in completion order

    @property
    def n_requests(self):
        """Requests in the ledger, including earlier sessions."""
        return self.ledger.n

    def _request(self, prompt, key):
        import openai
        i = self.ledger.reserve(self.max_requests, dict(
            t=time.time(), key=key, prompt_sha256=hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            settings=self.settings))
        rec = dict(i=i, key=key, settings=self.settings, t_start=time.time())
        t0 = time.perf_counter()
        try:
            raw = self.client.chat.completions.with_raw_response.create(
                model=MODEL, messages=[{"role": "user", "content": prompt}], max_tokens=self.max_tokens,
                **SAMPLING, extra_body=EXTRA_BODY)
            r = raw.parse()
            rec["seconds"] = time.perf_counter() - t0
            rec["http_status"] = raw.status_code
            rec["headers"] = {k: v for k, v in raw.headers.items() if k.lower() not in HIDDEN_HEADERS}
            ch = r.choices[0]
            rec["text"] = ch.message.content
            rec["finish_reason"] = ch.finish_reason
            rc = getattr(ch.message, "reasoning_content", None)
            if rc is None and getattr(ch.message, "model_extra", None):
                rc = ch.message.model_extra.get("reasoning_content")
            rec["reasoning_text_chars"] = len(rc) if rc else 0
            rec["usage"] = r.usage.model_dump() if r.usage is not None else None
            rec["model"] = r.model
            rec["response_id"] = r.id
            rec["error"] = None
        except (openai.APIStatusError, openai.APIConnectionError) as e:   # APITimeoutError included
            rec["seconds"] = time.perf_counter() - t0
            rec["http_status"] = getattr(e, "status_code", None)
            body = getattr(e, "body", None)
            err = body.get("error", body) if isinstance(body, dict) else None
            rec["error"] = dict(type=type(e).__name__,
                                code=err.get("code") if isinstance(err, dict) else None,
                                message=(err.get("message") if isinstance(err, dict) else None))
            resp = getattr(e, "response", None)
            if resp is not None:
                rec["headers"] = {k: v for k, v in resp.headers.items() if k.lower() not in HIDDEN_HEADERS}
            rec["text"] = None
        rec["t_end"] = time.time()
        self.requests.append(rec)
        self.ledger.record(rec)
        return rec

    def _attempt(self, prompt, key):
        """One reply attempt, with up to TRANSPORT_RETRIES retries on transport errors."""
        for k in range(TRANSPORT_RETRIES + 1):
            rec = self._request(prompt, key)
            if rec["error"] is None:
                return rec
            status = rec["http_status"]
            retryable = status is None or status == 429 or status >= 500
            if not retryable or k == TRANSPORT_RETRIES:
                return rec
            self.sleep(RETRY_WAIT_S)
        return rec

    def ask(self, prompt, key=None):
        """One decision: up to 1 + 2 attempts on invalid replies (A61)."""
        attempts = []
        for _ in range(3):
            a = self._attempt(prompt, key)
            a["parsed"] = parse(a["text"]) if a["error"] is None else None
            attempts.append(a)
            if a["parsed"] is not None or a["error"] is not None:
                break
        final = attempts[-1]["parsed"]
        return dict(attempts=[a["i"] for a in attempts], valid_first=attempts[0]["parsed"] is not None,
                    retries=len(attempts) - 1, final=final, fallback=final is None,
                    transport_error=attempts[-1]["error"])

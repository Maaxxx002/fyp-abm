"""
Arm-2 LLM client for qwen3.8-flash via Alibaba's OpenAI-compatible endpoint (register A72).

Request settings: model qwen3.8-flash, thinking OFF via extra_body={"enable_thinking": False};
temperature, top_p and every other sampling parameter are NOT sent, so the API defaults apply;
max_tokens 1024 (A65's implementation cap, so a reply cannot be cut off); no system prompt, the
rendered prompt is the single user message.

Reply handling: A64 parsing; A61 retries (up to 2 more attempts after an invalid reply, then the
agent keeps its current action -- the caller applies that fallback). Transport errors (429, 5xx,
timeouts, connection errors): the SDK's own retries are off; the client waits RETRY_WAIT_S and
retries up to 2 times, logging each attempt. Every HTTP request counts toward `max_requests`.

SECURITY: the key and base URL are read from ENV_FILE at run time only. They are passed to the
SDK and never printed, logged, returned or written anywhere.
"""
import os
import re
import time

ENV_FILE = os.environ.get("QWEN_ENV_FILE", r"C:\Users\Admin\Documents\QWENAPI\.env")
MODEL = "qwen3.8-flash"
EXTRA_BODY = {"enable_thinking": False}
MAX_TOKENS = 1024
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


class QwenArm2:
    def __init__(self, client, max_requests, sleep=time.sleep):
        self.client, self.max_requests, self.sleep = client, max_requests, sleep
        self.n_requests = 0
        self.requests = []          # one record per HTTP request, in order

    def _request(self, prompt):
        if self.n_requests >= self.max_requests:
            raise RequestCapReached(f"request cap {self.max_requests} reached")
        import openai
        self.n_requests += 1
        rec = dict(i=self.n_requests, t_start=time.time())
        t0 = time.perf_counter()
        try:
            raw = self.client.chat.completions.with_raw_response.create(
                model=MODEL, messages=[{"role": "user", "content": prompt}], max_tokens=MAX_TOKENS,
                extra_body=EXTRA_BODY)
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
        self.requests.append(rec)
        return rec

    def _attempt(self, prompt):
        """One reply attempt, with up to TRANSPORT_RETRIES retries on transport errors."""
        for k in range(TRANSPORT_RETRIES + 1):
            rec = self._request(prompt)
            if rec["error"] is None:
                return rec
            status = rec["http_status"]
            retryable = status is None or status == 429 or status >= 500
            if not retryable or k == TRANSPORT_RETRIES:
                return rec
            self.sleep(RETRY_WAIT_S)
        return rec

    def ask(self, prompt):
        """One decision: up to 1 + 2 attempts on invalid replies (A61)."""
        attempts = []
        for _ in range(3):
            a = self._attempt(prompt)
            a["parsed"] = parse(a["text"]) if a["error"] is None else None
            attempts.append(a)
            if a["parsed"] is not None or a["error"] is not None:
                break
        final = attempts[-1]["parsed"]
        return dict(attempts=[a["i"] for a in attempts], valid_first=attempts[0]["parsed"] is not None,
                    retries=len(attempts) - 1, final=final, fallback=final is None,
                    transport_error=attempts[-1]["error"])

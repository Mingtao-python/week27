"""Small OpenAI-compatible HTTP adapter. Credentials stay in environment variables."""

import json
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

LABELS = {"Billing", "Technical", "Account", "Other"}
ROUTING_ALIASES = {"default", "fast", "pro", "auto", "random"}

def parse_response(content):
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        label = content.strip()
        return {"label": label} if label in LABELS else None
    return parsed if isinstance(parsed, dict) else None

class ModelClient:
    def __init__(self, api_key, model, base_url, temperature=0, max_tokens=64,
                 timeout=60, delay=1.1):
        if not model or model.lower() in ROUTING_ALIASES:
            raise ValueError("Use a fixed model ID, not a routing alias.")
        address = urlparse(base_url)
        if not address.hostname or address.username or address.password or address.query or address.fragment:
            raise ValueError("The endpoint must not contain credentials, a query or a fragment.")
        if address.scheme != "https" and not (
            address.scheme == "http" and address.hostname in ("localhost", "127.0.0.1", "::1")
        ):
            raise ValueError("Use HTTPS for remote endpoints.")
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.delay = delay
        self.last_request = None

    def call(self, instructions, input_prompt):
        if self.last_request is not None:
            time.sleep(max(0, self.delay - (time.monotonic() - self.last_request)))
        messages = [{"role": "user", "content": f"{instructions}\n\nSupport ticket:\n{input_prompt}"}]
        payload = {"model": self.model, "messages": messages,
                   "temperature": self.temperature, "max_tokens": self.max_tokens}
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = Request(self.base_url + "/chat/completions",
                          data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        self.last_request = time.monotonic()
        start = time.perf_counter()
        try:
            with urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            # Do not log response bodies, headers or credentials.
            raise RuntimeError(f"LLM request failed: HTTP {error.code}") from None
        except (URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError):
            raise RuntimeError("LLM request failed: connection, timeout or invalid API response") from None
        try:
            choice = data["choices"][0]
            content = choice["message"]["content"]
            returned_model = data["model"]
            if not isinstance(content, str) or not isinstance(returned_model, str) or not returned_model:
                raise ValueError()
        except (KeyError, IndexError, TypeError, ValueError):
            raise RuntimeError("LLM response must include text content and a model ID") from None
        usage = data.get("usage") or {}
        return {"raw_output": content, "parsed_output": parse_response(content),
                "token_count": usage.get("total_tokens"), "usage": usage,
                "response_model": returned_model, "response_id": data.get("id"),
                "finish_reason": choice.get("finish_reason"),
                "system_fingerprint": data.get("system_fingerprint"),
                "latency_ms": (time.perf_counter() - start) * 1000,
                "request": payload}

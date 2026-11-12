"""Opt-in local QA server: count outbound provider requests before sending them.

Normal app images do not invoke this module. It never records headers, prompts,
answers or response bodies. Each retry consumes one slot, including timeouts.
"""
import hashlib
import json
import os
from pathlib import Path
import threading
import time


class BudgetExceeded(RuntimeError):
    pass


class CallLedger:
    def __init__(self, path, prior_calls, *, maximum_total=59, key=None, run="acceptance"):
        if type(maximum_total) is not int or not 1 <= maximum_total <= 80:
            raise ValueError("The request cap must be an integer no greater than 80")
        if type(prior_calls) is not int or not 0 <= prior_calls <= maximum_total:
            raise ValueError("A verified previous request count within the budget is required")
        self.path, self.lock = Path(path), threading.Lock()
        self.maximum_total, self.run = maximum_total, run
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.state = json.loads(self.path.read_text()) if self.path.exists() else {
            "prior_calls": prior_calls, "maximum_total": maximum_total, "calls": []}
        if self.state["prior_calls"] != prior_calls or self.state["maximum_total"] != maximum_total:
            raise ValueError("Existing ledger budget does not match; preserve and reconcile it")
        if key is not None:
            identity = hashlib.sha256(key.encode()).hexdigest()
            if self.state.get("key_fingerprint", identity) != identity:
                raise ValueError("The configured key does not match this ledger")
            self.state.update(key_fingerprint=identity, key_suffix=key[-4:])
        if prior_calls + len(self.state["calls"]) > maximum_total:
            raise ValueError("Existing ledger exceeds its request budget")
        self._save()

    def _save(self):
        temporary = self.path.with_suffix('.tmp')
        temporary.write_text(json.dumps(self.state, indent=2), encoding='utf-8')
        temporary.replace(self.path)

    def reserve(self, body):
        with self.lock:
            if self.state["prior_calls"] + len(self.state["calls"]) >= self.maximum_total:
                raise BudgetExceeded("Real-provider request budget exhausted")
            index = len(self.state["calls"])
            try:
                payload = json.loads(body)
                feature = payload.get("response_format", {}).get("json_schema", {}).get("name", "chat_completion")
                feature = feature if feature in {"practice_questions", "evaluation", "essay_grade", "gap_explanation"} else "chat_completion"
            except (ValueError, TypeError, AttributeError):
                feature = "chat_completion"
            self.state["calls"].append({"number": self.state["prior_calls"] + index + 1,
                "test": self.run, "feature": feature, "purpose": "Validate generation/grading and browser integration",
                "request_hash": hashlib.sha256(body).hexdigest(), "status": "started",
                "approximate_input_tokens": (len(body) + 3) // 4, "token_method": "UTF-8 bytes / 4 estimate"})
            self._save()  # Persist before network I/O, so a crash cannot hide a request.
            return index

    def finish(self, index, status, duration_ms, response=None):
        with self.lock:
            entry = self.state["calls"][index]
            entry.update(status=status, duration_ms=round(duration_ms))
            if isinstance(response, dict):
                # Whitelist provider metadata. Never persist provider error text.
                if isinstance(status, int) and status >= 400:
                    error = response.get("error") or {}
                    message = str(error.get("message", "") if isinstance(error, dict) else "").lower()
                    category = ("unsupported_parameters" if "no endpoints" in message and "parameter" in message else
                                "reasoning_required" if "reasoning is mandatory" in message else
                                "route_unavailable" if "no endpoints" in message else
                                "model_unavailable" if "model" in message and any(word in message for word in ("not found", "not a valid", "does not exist")) else
                                "credentials_rejected" if status in (401, 403) else "request_rejected")
                    entry["failure_category"] = category
                usage = response.get("usage") or {}
                if not isinstance(usage, dict):
                    usage = {}
                entry["usage"] = {key: usage[key] for key in (
                    "prompt_tokens", "completion_tokens", "total_tokens", "cost") if key in usage}
                if type(usage.get("prompt_tokens")) is int:
                    entry["approximate_input_tokens"] = usage["prompt_tokens"]
                if type(usage.get("completion_tokens")) is int:
                    entry["approximate_output_tokens"] = usage["completion_tokens"]
                else:
                    choices = response.get("choices") or []
                    content = choices[0].get("message", {}).get("content", "") if choices else ""
                    if isinstance(content, str):
                        entry["approximate_output_tokens"] = (len(content.encode()) + 3) // 4
                if type(usage.get("prompt_tokens")) is int and type(usage.get("completion_tokens")) is int:
                    entry["token_method"] = "provider-reported usage"
            self._save()


def install_meter(ledger, hostname):
    """Keep the application's host-specific request formatting and real retries."""
    import httpx
    original = httpx.HTTPTransport.handle_request

    def counted(transport, request):
        if request.url.host != hostname or not request.url.path.endswith('/chat/completions'):
            return original(transport, request)
        try:
            index = ledger.reserve(request.read())
        except BudgetExceeded:
            raise httpx.ConnectError("Real-provider QA budget exhausted", request=request) from None
        started = time.monotonic()
        try:
            response = original(transport, request)
            content = response.read()
        except Exception as exc:
            ledger.finish(index, type(exc).__name__, (time.monotonic() - started) * 1000)
            raise
        try:
            metadata = json.loads(content)
        except (ValueError, UnicodeError):
            metadata = None
        ledger.finish(index, response.status_code, (time.monotonic() - started) * 1000, metadata)
        return response

    httpx.HTTPTransport.handle_request = counted


if __name__ == '__main__':
    from urllib.parse import urlsplit
    import sys
    sys.path.insert(0, '/srv/DBCAS/backend')
    from app.config import get_settings
    import uvicorn
    settings = get_settings()
    if not (settings.llm_api_key.strip() and settings.llm_base_url and settings.llm_model):
        raise RuntimeError("A configured real provider is required")
    raw_prior = os.environ.get('DBCAS_REAL_PRIOR_CALLS', '')
    if not raw_prior.isdecimal():
        raise RuntimeError("Reconcile previous real requests before starting this QA server")
    cap = int(os.environ.get('DBCAS_REAL_MAX_CALLS', '80'))
    ledger = CallLedger('/qa/results/ledger.json', int(raw_prior), maximum_total=cap,
                        key=settings.llm_api_key, run=os.environ.get('DBCAS_REAL_RUN', 'acceptance'))
    install_meter(ledger, urlsplit(settings.llm_base_url).hostname)
    uvicorn.run('app.main:app', host='0.0.0.0', port=8000, workers=1)

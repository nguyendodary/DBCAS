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
    def __init__(self, path, prior_calls):
        if type(prior_calls) is not int or not 0 <= prior_calls <= 59:
            raise ValueError("A verified previous request count between 0 and 59 is required")
        self.path, self.lock = Path(path), threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.state = json.loads(self.path.read_text()) if self.path.exists() else {
            "prior_calls": prior_calls, "maximum_total": 59, "calls": []}
        if self.state["prior_calls"] != prior_calls or self.state["maximum_total"] != 59:
            raise ValueError("Existing ledger budget does not match; preserve and reconcile it")
        self._save()

    def _save(self):
        temporary = self.path.with_suffix('.tmp')
        temporary.write_text(json.dumps(self.state, indent=2), encoding='utf-8')
        temporary.replace(self.path)

    def reserve(self, body):
        with self.lock:
            if self.state["prior_calls"] + len(self.state["calls"]) >= 59:
                raise BudgetExceeded("Real-provider total must remain below 60")
            index = len(self.state["calls"])
            self.state["calls"].append({"number": self.state["prior_calls"] + index + 1,
                "request_hash": hashlib.sha256(body).hexdigest(), "status": "started"})
            self._save()  # Persist before network I/O, so a crash cannot hide a request.
            return index

    def finish(self, index, status, duration_ms, response=None):
        with self.lock:
            entry = self.state["calls"][index]
            entry.update(status=status, duration_ms=round(duration_ms))
            if isinstance(response, dict):
                # Whitelist provider metadata. Never persist provider error text.
                entry["model"] = response.get("model")
                entry["provider"] = response.get("provider")
                usage = response.get("usage") or {}
                if not isinstance(usage, dict):
                    usage = {}
                entry["usage"] = {key: usage[key] for key in (
                    "prompt_tokens", "completion_tokens", "total_tokens", "cost") if key in usage}
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
    ledger = CallLedger('/qa/results/ledger.json', int(raw_prior))
    install_meter(ledger, urlsplit(settings.llm_base_url).hostname)
    uvicorn.run('app.main:app', host='0.0.0.0', port=8000, workers=1)

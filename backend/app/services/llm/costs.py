"""Record every provider attempt and estimate token charges when priced."""
from datetime import datetime, timezone
from decimal import Decimal
from urllib.parse import urlsplit

from sqlalchemy.orm import Session

from ...models import OperatingCost


def make_cost_observer(bind, settings, *, clock=None):
    input_rate = Decimal(str(settings.llm_input_usd_per_million))
    output_rate = Decimal(str(settings.llm_output_usd_per_million))
    cache_hit_rate = Decimal(str(settings.llm_cache_hit_usd_per_million))
    peak_multiplier = Decimal(str(settings.llm_peak_multiplier))
    deepseek = urlsplit(settings.llm_base_url).hostname == "api.deepseek.com"

    def token_count(value):
        return value if type(value) is int and value >= 0 else None

    def record(request, outcome, http_status, payload):
        usage = payload.get("usage", {}) if isinstance(payload, dict) else {}
        if not isinstance(usage, dict):
            usage = {}
        prompt = token_count(usage.get("prompt_tokens"))
        completion = token_count(usage.get("completion_tokens"))
        amount = None
        if deepseek and request.model == "deepseek-flash":
            hit = token_count(usage.get("prompt_cache_hit_tokens"))
            miss = token_count(usage.get("prompt_cache_miss_tokens"))
            if (prompt is not None and completion is not None and hit is not None
                    and miss is not None and hit + miss == prompt
                    and input_rate > 0 and output_rate > 0 and cache_hit_rate > 0):
                now = clock() if clock else datetime.now(timezone.utc)
                utc = now.astimezone(timezone.utc)
                # Published weekday peak windows are 01–04 and 06–10 UTC.
                # Chinese public holidays and future rate changes can alter
                # the actual invoice: this is a token-based estimate.
                peak = utc.weekday() < 5 and (1 <= utc.hour < 4 or 6 <= utc.hour < 10)
                factor = peak_multiplier if peak else Decimal(1)
                amount = (Decimal(hit) * cache_hit_rate + Decimal(miss) * input_rate
                          + Decimal(completion) * output_rate) * factor / Decimal(1_000_000)
        elif prompt is not None and completion is not None and (input_rate or output_rate):
            amount = (Decimal(prompt) * input_rate + Decimal(completion) * output_rate) / Decimal(1_000_000)
        # Own transaction: grading may roll back, but the external call happened.
        with Session(bind=bind) as db:
            db.add(OperatingCost(kind="ai", task_type=request.task_type, model=request.model,
                                 prompt_tokens=prompt, completion_tokens=completion,
                                 amount_usd=amount, outcome=outcome, http_status=http_status))
            db.commit()

    return record

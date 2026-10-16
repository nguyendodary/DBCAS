"""python -m app.worker [--allow-provider-calls] [--once].

The API sweeps expiry and SQL jobs automatically. This optional bounded worker
also grades/retries essays only when its operator explicitly enables provider
calls. Tests inject the real service with mocked HTTP transport instead.
"""
import argparse
import logging
import threading

from .config import get_settings
from .db import get_session_factory
from .services.assessment_lifecycle import sweep_expired
from .services.grading_jobs import process_one
from .services.llm import build_llm_service
from .services.sandbox_runner import SandboxRunner


def maintenance_tick(*, allow_provider_calls=False):
    settings = get_settings()
    with get_session_factory()() as db:
        sweep_expired(db)
        runner = SandboxRunner(settings)
        for _ in range(10):
            llm = build_llm_service(settings, db) if allow_provider_calls else None
            if not process_one(db, runner, llm, include_essay=allow_provider_calls):
                break


def maintenance_loop(stop, *, allow_provider_calls=False):
    while not stop.is_set():
        try:
            maintenance_tick(allow_provider_calls=allow_provider_calls)
        except Exception as exc:
            # No answer, prompt, DSN or provider key is logged.
            logging.getLogger("dbcas.worker").error("Maintenance tick failed: %s", type(exc).__name__)
        stop.wait(get_settings().session_sweep_seconds)


def main():
    parser = argparse.ArgumentParser(description="DBCAS expiry and grading worker")
    parser.add_argument("--allow-provider-calls", action="store_true", help="Explicitly enable configured external essay grading/retry calls")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    if args.once:
        maintenance_tick(allow_provider_calls=args.allow_provider_calls)
    else:
        maintenance_loop(threading.Event(), allow_provider_calls=args.allow_provider_calls)


if __name__ == "__main__":
    main()

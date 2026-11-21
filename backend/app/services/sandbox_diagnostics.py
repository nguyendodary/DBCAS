"""Privacy-safe, in-process diagnostics for ephemeral SQL capacity rejections.

This module only enriches a log record. It never participates in admission,
changes a limit, or records SQL text, credentials or learner identifiers.
"""
import json
import os
import threading
import time
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass


PURPOSES = ("user_sql_run", "grading_submit", "grading_maintenance")


@dataclass(frozen=True)
class _Holder:
    purpose: str
    started: float


def operation(runner, purpose):
    """Mark a caller's purpose when the runner supports diagnostics."""
    helper = getattr(runner, "operation_context", None)
    return helper(purpose) if helper is not None else nullcontext()


class SlotDiagnostics:
    """Tracks slot holders so a busy rejection can explain what held them."""

    def __init__(self, slot_count):
        self.slot_count = slot_count
        self._lock = threading.Lock()
        self._holders = {}
        self._local = threading.local()

    @contextmanager
    def operation_context(self, purpose):
        if purpose not in PURPOSES:
            raise ValueError("Unknown sandbox operation purpose")
        previous = getattr(self._local, "purpose", None)
        self._local.purpose = purpose
        try:
            yield
        finally:
            self._local.purpose = previous

    @property
    def purpose(self):
        return getattr(self._local, "purpose", "unmarked")

    def acquired(self):
        with self._lock:
            self._holders[threading.get_ident()] = _Holder(self.purpose, time.monotonic())

    def released(self):
        with self._lock:
            self._holders.pop(threading.get_ident(), None)

    def rejection(self, waited_seconds):
        now = time.monotonic()
        with self._lock:
            holders = [
                {"purpose": holder.purpose, "held_ms": round((now - holder.started) * 1000, 1)}
                for holder in self._holders.values()
            ]
        return {
            "event": "sandbox_busy",
            "worker_pid": os.getpid(),
            "slot_count": self.slot_count,
            "available_slots": max(0, self.slot_count - len(holders)),
            "wait_ms": round(waited_seconds * 1000, 1),
            "operation": self.purpose,
            "active_holders": holders,
        }


def log_rejection(logger, payload):
    """Emit the structured payload in both message and prefixed extra fields."""
    logger.warning(
        "sandbox_busy rejection %s",
        json.dumps(payload, sort_keys=True),
        extra={
            "sd_worker_pid": payload["worker_pid"],
            "sd_slot_count": payload["slot_count"],
            "sd_available_slots": payload["available_slots"],
            "sd_wait_ms": payload["wait_ms"],
            "sd_operation": payload["operation"],
            "sd_active_holders": payload["active_holders"],
        },
    )

"""Process-shared admission and separate grading capacity for PR-B2.

The #71 analysis showed two process-local slots per Uvicorn worker and a 5 s
local acquire timeout, with grading sharing the same slots. The broker must not
simply move that semaphore behind an RPC: admission is shared by every caller
of the broker service instance, grading has its own pool, and a bounded queue
rejects explicitly instead of waiting forever.
"""
import threading

from .errors import BrokerError


class BrokerAdmission:
    def __init__(self, queue_size, grading_size, timeout_seconds):
        self.queue_size = queue_size
        self.timeout_seconds = timeout_seconds
        self._slots = threading.BoundedSemaphore(queue_size)
        self._grading = threading.BoundedSemaphore(grading_size)
        self._local = threading.local()

    @property
    def purpose(self):
        return getattr(self._local, "purpose", "unmarked")

    def _set_purpose(self, purpose):
        previous = getattr(self._local, "purpose", None)
        self._local.purpose = purpose
        return previous

    def _restore(self, previous):
        self._local.purpose = previous

    def acquire(self, *, grading=False):
        previous = self._set_purpose("grading" if grading else "user_sql_run")
        gate = self._grading if grading else self._slots
        if not gate.acquire(timeout=self.timeout_seconds):
            self._restore(previous)
            raise BrokerError("broker_busy", "Broker admission queue is full")
        return previous

    def release(self, previous, *, grading=False):
        (self._grading if grading else self._slots).release()
        self._restore(previous)

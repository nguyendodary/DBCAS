"""Login attempt throttling (NFR security — brute-force resistance).

An in-process sliding-window failure counter keyed by
``(normalized_email, client_ip)``. Deliberate choices:

- Only ``invalid_credentials`` failures count — a *wrong password or
  unknown email*. Successful logins reset the key's window, and
  disabled-account responses do not count (the credential pair was
  valid). The 429 check runs before credential verification, so a
  saturated window rejects even a correct password: the point is to cap
  attempts, not to be cleverer than the attacker.
- Neither response path reveals account existence: unknown email and
  wrong password already share ``invalid_credentials``, and the throttle
  applies identically to both.
- In-process state is intentional at this deployment's single-instance
  course scale — a restart just resets the counters, which only makes
  the limiter more permissive, never more strict. If the app ever runs
  multi-instance, swap this for a shared store (e.g. Redis INCR+EXPIRE)
  behind the same interface.
- Nothing here sees or stores passwords — only the normalized email key.

Keys are pruned lazily on access plus a sweep when the map grows, so the
map stays bounded under credential-stuffing traffic that varies emails.
"""

import math
import time
from typing import Callable, Optional

from ..config import Settings
from ..errors import AppError


class LoginThrottle:
    def __init__(self, now: Optional[Callable[[], float]] = None):
        self._now = now or time.monotonic
        # key -> sorted list of failure timestamps inside the window
        self._failures: dict[tuple[str, str], list[float]] = {}

    def key(self, email: str, client_ip: Optional[str]) -> tuple[str, str]:
        return (email.strip().lower(), client_ip or "-")

    def check(self, key: tuple[str, str], settings: Settings) -> None:
        """429 when the key has exhausted its attempts in the window."""
        failures = self._window(key, settings)
        if len(failures) < settings.login_rate_limit_attempts:
            return
        retry_after = max(
            1,
            math.ceil(
                settings.login_rate_limit_window_seconds
                - (self._now() - failures[0])
            ),
        )
        raise AppError(
            429,
            "login_rate_limited",
            f"Too many failed sign-in attempts — try again in "
            f"{retry_after} seconds",
            headers={"Retry-After": str(retry_after)},
        )

    def record_failure(self, key: tuple[str, str], settings: Settings) -> None:
        # read does not create entries; a record creates exactly one
        kept = self._window(key, settings)
        if key not in self._failures:
            self._failures[key] = kept
        self._failures[key].append(self._now())
        # bounded memory under attacker-varied keys: sweep occasionally
        if len(self._failures) > 10_000:
            self._sweep(settings)

    def record_success(self, key: tuple[str, str]) -> None:
        """A successful login resets the key's failure window — legitimate
        users are never punished for earlier typos."""
        self._failures.pop(key, None)

    def _window(
        self, key: tuple[str, str], settings: Settings
    ) -> list[float]:
        """The key's failures inside the sliding window (pruned in place).
        Read-only: never creates an entry for a key with no failures."""
        cutoff = self._now() - settings.login_rate_limit_window_seconds
        kept = [t for t in self._failures.get(key, []) if t > cutoff]
        if kept:
            self._failures[key] = kept
        else:
            self._failures.pop(key, None)
        return kept

    def _sweep(self, settings: Settings) -> None:
        cutoff = self._now() - settings.login_rate_limit_window_seconds
        self._failures = {
            k: [t for t in ts if t > cutoff]
            for k, ts in self._failures.items()
        }
        for k in [k for k, ts in self._failures.items() if not ts]:
            del self._failures[k]

    def reset(self) -> None:
        """Test hook — drop all state."""
        self._failures.clear()


_default = LoginThrottle()


def get_login_throttle() -> LoginThrottle:
    """Dependency provider — override in tests like the other services."""
    return _default

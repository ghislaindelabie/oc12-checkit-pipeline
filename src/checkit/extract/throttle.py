"""Per-key request pacing, shared by every fetching component.

One global throttle keyed by source name (or domain for politeness pacing):
two components hitting the same API in one process share the same gate.
Intervals are set per source at the call site, sourced from each provider's
STATED limit where one exists (see docs/rate-limits.md for provenance).
"""

import logging
import time

logger = logging.getLogger(__name__)


class _RealClock:
    monotonic = staticmethod(time.monotonic)
    sleep = staticmethod(time.sleep)


class Throttle:
    def __init__(self, clock=None):
        self._clock = clock or _RealClock()
        self._last: dict[str, float] = {}

    def wait(self, key: str, min_interval: float) -> None:
        if min_interval <= 0:
            return
        last = self._last.get(key)
        now = self._clock.monotonic()
        if last is not None:
            remaining = min_interval - (now - last)
            if remaining > 0:
                logger.debug("throttle %s: waiting %.2fs", key, remaining)
                self._clock.sleep(remaining)
        self._last[key] = self._clock.monotonic()


# process-wide shared instance — all extractors pace through the same gate
THROTTLE = Throttle()

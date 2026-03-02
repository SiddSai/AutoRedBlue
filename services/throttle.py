# AI generated rate-limiter for API requests


import os
import time
import threading


_lock = threading.Lock()
_last_call_ts = 0.0


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except Exception:
        return default


def throttle(min_interval_s: float | None = None) -> None:
    global _last_call_ts

    if min_interval_s is None:
        min_interval_s = _env_float("LLM_MIN_REQUEST_INTERVAL_S", 1.0)

    if min_interval_s <= 0:
        return

    with _lock:
        now = time.time()
        wait_s = (_last_call_ts + float(min_interval_s)) - now
        if wait_s > 0:
            time.sleep(wait_s)
        _last_call_ts = time.time()


def get_langchain_rate_limiter(requests_per_second: float | None = None):
    if requests_per_second is None:
        requests_per_second = _env_float("LLM_REQUESTS_PER_SECOND", 0.5)

    if requests_per_second <= 0:
        return None

    try:
        from langchain_core.rate_limiters import InMemoryRateLimiter

        return InMemoryRateLimiter(requests_per_second=float(requests_per_second))
    except Exception:
        return None

# rate-limiting for LLM API requests
from langchain_core.rate_limiters import InMemoryRateLimiter
# 'tenacity' is a very handy library for managing exponential backoff and other retry wrappers
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from openai import RateLimitError

LLM_REQUESTS_PER_SECOND = 0.5
MIN_EXPONENTIAL = 1
MAX_EXPONENTIAL = 60
MAX_ATTEMPTS = 6

# standard langchain limiter
def get_langchain_rate_limiter(requests_per_second: float | None = None):

    if not requests_per_second:
        requests_per_second = LLM_REQUESTS_PER_SECOND

    return InMemoryRateLimiter(
        requests_per_second=float(requests_per_second)
    )

# exponential backoff on model requests
@retry(
    retry=retry_if_exception_type(RateLimitError),
    wait=wait_exponential(min=MIN_EXPONENTIAL, max=MAX_EXPONENTIAL),
    stop=stop_after_attempt(MAX_ATTEMPTS)
)
def throttled_model_call(model, *args, **kwargs):
    return model.invoke(*args, **kwargs)

import logging

import requests
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

USER_AGENT = "checkit-pipeline/0.1 (non-commercial research training project)"
DEFAULT_TIMEOUT = 20.0

_session = requests.Session()
_session.headers["User-Agent"] = USER_AGENT


def _should_retry(exc: BaseException) -> bool:
    # Retrying a 4xx hammers servers for a deterministic answer.
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        return exc.response.status_code >= 500
    return isinstance(exc, requests.RequestException)


@retry(
    retry=retry_if_exception(_should_retry),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, max=10),
    reraise=True,
)
def get(url: str, params: dict | None = None, timeout: float = DEFAULT_TIMEOUT) -> requests.Response:
    response = _session.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    return response

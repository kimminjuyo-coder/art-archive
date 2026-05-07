from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

RETRY_STATUS = (408, 429, 500, 502, 503, 504)
USER_AGENT = "art-archive/0.1 (+https://github.com/<owner>/art-archive)"
DEFAULT_TIMEOUT = 15  # 초. 어댑터가 .get(url, timeout=DEFAULT_TIMEOUT)로 명시 전달


def build_session() -> Session:
    retry = Retry(
        total=3,
        backoff_factor=2,  # 2s -> 4s -> 8s
        status_forcelist=RETRY_STATUS,
        allowed_methods=frozenset(["GET", "HEAD"]),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    s = Session()
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    s.headers.update({"User-Agent": USER_AGENT})
    # NOTE: requests.Session does not honor an instance-level timeout attribute.
    # Callers must pass `timeout=DEFAULT_TIMEOUT` per request.
    return s

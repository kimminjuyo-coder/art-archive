import pytest
import requests
from src.utils.http import build_session, RETRY_STATUS, DEFAULT_TIMEOUT


def test_session_has_retry_on_5xx():
    s = build_session()
    adapter = s.get_adapter("https://example.com/")
    retry = adapter.max_retries
    assert retry.total == 3
    assert 502 in retry.status_forcelist
    assert 429 in retry.status_forcelist


def test_session_has_user_agent():
    s = build_session()
    assert "art-archive" in s.headers.get("User-Agent", "")


def test_4xx_not_retried():
    s = build_session()
    adapter = s.get_adapter("https://example.com/")
    retry = adapter.max_retries
    assert 404 not in retry.status_forcelist
    assert 403 not in retry.status_forcelist


def test_default_timeout_constant_exported():
    from src.utils.http import DEFAULT_TIMEOUT
    assert DEFAULT_TIMEOUT == 15

from datetime import date
from src.core.models import Exhibition
from src.core.crawler import Crawler, RunResult
from tests.fakes import FakeNotionClient


class FakeAdapter:
    name = "artnet"
    source_label = "아트넷"

    def __init__(self, urls: list[str], details: dict[str, Exhibition], errors: set[str] | None = None):
        self._urls = urls
        self._details = details
        self._errors = errors or set()

    def list_from_top(self):
        for u in self._urls:
            yield u

    def parse_detail(self, url: str) -> Exhibition:
        if url in self._errors:
            raise ValueError(f"parse failed: {url}")
        return self._details[url]


def _ex(url: str, title="t", artists=None) -> Exhibition:
    return Exhibition(
        title=title, exhibition_type="미상", venue="V", year=2026,
        start_date=None, end_date=None,
        artists_kr=artists or ["김"], artists_en=[],
        source_site="아트넷", source_url=url,
    )


def test_full_backfill_inserts_all_new():
    urls = [f"u{i}" for i in range(5)]
    details = {u: _ex(u) for u in urls}
    adapter = FakeAdapter(urls, details)
    notion = FakeNotionClient()
    crawler = Crawler(adapter, notion, sleep_seconds=0)
    result = crawler.run(mode="backfill")
    assert result.inserted == 5
    assert result.skipped_dup == 0
    assert result.errors == 0
    assert len(notion.created_pages) == 5


def test_daily_stops_after_K_consecutive_seen():
    seen = {f"u{i}" for i in range(5)}
    urls = [f"u{i}" for i in range(5)] + [f"new{i}" for i in range(2)]
    details = {u: _ex(u) for u in urls}
    adapter = FakeAdapter(urls, details)
    notion = FakeNotionClient(seed_urls=seen)
    crawler = Crawler(adapter, notion, sleep_seconds=0, daily_seen_threshold=5)
    result = crawler.run(mode="daily")
    assert result.skipped_dup == 5
    assert result.inserted == 0


def test_daily_continues_when_seen_streak_is_broken():
    notion = FakeNotionClient(seed_urls={"u0", "u2", "u3", "u4", "u5", "u6"})
    urls = ["u0", "u1", "u2", "u3", "u4", "u5", "u6", "u7"]
    details = {u: _ex(u) for u in urls}
    adapter = FakeAdapter(urls, details)
    crawler = Crawler(adapter, notion, sleep_seconds=0, daily_seen_threshold=5)
    result = crawler.run(mode="daily")
    assert result.inserted == 1
    assert "u1" in notion.fetch_all_source_urls()


def test_parse_error_continues_then_stops_at_threshold():
    urls = [f"u{i}" for i in range(15)]
    details = {f"u{i}": _ex(f"u{i}") for i in range(15)}
    errors = {f"u{i}" for i in range(10)}
    adapter = FakeAdapter(urls, details, errors=errors)
    notion = FakeNotionClient()
    crawler = Crawler(adapter, notion, sleep_seconds=0, parse_error_threshold=10)
    result = crawler.run(mode="backfill")
    assert result.errors == 10
    assert result.inserted == 0
    assert result.aborted is True


def test_isolated_parse_error_does_not_stop():
    urls = [f"u{i}" for i in range(5)]
    details = {f"u{i}": _ex(f"u{i}") for i in range(5)}
    errors = {"u2"}
    adapter = FakeAdapter(urls, details, errors=errors)
    notion = FakeNotionClient()
    crawler = Crawler(adapter, notion, sleep_seconds=0, parse_error_threshold=10)
    result = crawler.run(mode="backfill")
    assert result.errors == 1
    assert result.inserted == 4
    assert result.aborted is False


def test_classifier_applied_in_run():
    ex = _ex("u0", title="단체전 X", artists=["김", "이"])
    adapter = FakeAdapter(["u0"], {"u0": ex})
    notion = FakeNotionClient()
    Crawler(adapter, notion, sleep_seconds=0).run(mode="backfill")
    assert notion.created_pages[0].exhibition_type == "단체전"

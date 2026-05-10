from datetime import date
from pathlib import Path
import pytest
from bs4 import BeautifulSoup
from src.adapters.artnet import (
    ArtnetAdapter,
    LIST_URLS,
    _parse_artists,
    _parse_period,
)

FIX = Path(__file__).parent / "fixtures" / "artnet"


def _read(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8")


def _first_card(html: str):
    soup = BeautifulSoup(html, "html.parser")
    return soup.select_one(".gallery .gallery-item")


# --- helper unit tests ---

def test_parse_period_korean_format():
    s, e = _parse_period("2026년 05월 13일~ 2026년 05월 29일")
    assert s == date(2026, 5, 13)
    assert e == date(2026, 5, 29)


def test_parse_period_returns_none_when_invalid():
    assert _parse_period("") == (None, None)
    assert _parse_period("미정") == (None, None)


def test_parse_artists_single():
    kr, en = _parse_artists("신수항")
    assert kr == ["신수항"]
    assert en == []


def test_parse_artists_multiple():
    kr, en = _parse_artists("박진종, 편승화, 이유진")
    assert kr == ["박진종", "편승화", "이유진"]
    assert en == []


def test_parse_artists_with_english():
    kr, en = _parse_artists("백남준(Paik Namjune)")
    assert kr == ["백남준"]
    assert en == ["Paik Namjune"]


def test_parse_artists_truncated_ellipsis_dropped():
    kr, en = _parse_artists("강금주, 강민경, 고석원, …")
    assert kr == ["강금주", "강민경", "고석원"]
    assert en == []


def test_parse_artists_empty():
    kr, en = _parse_artists("")
    assert kr == [] and en == []


# --- card parsing tests ---

def test_parse_card_solo_first():
    a = ArtnetAdapter()
    card = _first_card(_read("list_solo.html"))
    ex = a._parse_card(card)
    assert ex.title == "<건조한 배설 A Dry Expulsion> 신수항展"
    assert ex.source_url == "https://artnet.kr/p/solo-exhibitions/1339"
    assert ex.source_site == "아트넷"
    assert ex.venue == "창작공간 두구"
    assert ex.start_date == date(2026, 5, 13)
    assert ex.end_date == date(2026, 5, 29)
    assert ex.year == 2026
    assert ex.artists_kr == ["신수항"]
    assert ex.artists_en == []


def test_parse_card_group_with_english_artist():
    a = ArtnetAdapter()
    soup = BeautifulSoup(_read("list_group.html"), "html.parser")
    cards = soup.select(".gallery .gallery-item")
    ex = a._parse_card(cards[1])
    assert ex.artists_kr == ["백남준"]
    assert ex.artists_en == ["Paik Namjune"]
    assert ex.venue == "이화여대 ECC"


def test_parse_card_group_truncated_artists():
    a = ArtnetAdapter()
    soup = BeautifulSoup(_read("list_group.html"), "html.parser")
    cards = soup.select(".gallery .gallery-item")
    ex = a._parse_card(cards[2])
    assert ex.artists_kr == [
        "강금주", "강민경", "고석원", "곽태임", "김재남",
        "김정희", "김희진", "문현경", "박동채", "박인숙",
    ]
    assert ex.artists_en == []


def test_parse_card_group_collective_name():
    a = ArtnetAdapter()
    soup = BeautifulSoup(_read("list_group.html"), "html.parser")
    cards = soup.select(".gallery .gallery-item")
    ex = a._parse_card(cards[3])
    assert ex.artists_kr == ["51artists"]
    assert ex.artists_en == []


# --- session-driven crawl tests ---

class _StubResponse:
    def __init__(self, text, status=200):
        self.text = text
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class _StubSession:
    def __init__(self, page_map):
        self._map = page_map
        self.calls: list[str] = []

    def get(self, url, **kw):
        self.calls.append(url)
        if url in self._map:
            return _StubResponse(self._map[url])
        return _StubResponse("", status=404)


def test_list_from_top_iterates_solo_then_group():
    session = _StubSession({
        LIST_URLS[0]: _read("list_solo.html"),
        "https://artnet.kr/p/solo-exhibitions&page=2": _read("list_solo_p2.html"),
        LIST_URLS[1]: _read("list_group.html"),
    })
    adapter = ArtnetAdapter(session=session, max_list_pages=10)
    urls = list(adapter.list_from_top())
    assert urls == [
        "https://artnet.kr/p/solo-exhibitions/1339",
        "https://artnet.kr/p/solo-exhibitions/1338",
        "https://artnet.kr/p/solo-exhibitions/1337",
        "https://artnet.kr/p/solo-exhibitions/1300",
        "https://artnet.kr/p/group-exhibitions/2200",
        "https://artnet.kr/p/group-exhibitions/2201",
        "https://artnet.kr/p/group-exhibitions/2202",
        "https://artnet.kr/p/group-exhibitions/2203",
    ]


def test_list_from_top_stops_when_no_pg_next():
    session = _StubSession({LIST_URLS[0]: _read("list_solo_p2.html")})
    adapter = ArtnetAdapter(session=session, max_list_pages=10)
    urls = list(adapter.list_from_top())
    # solo p2 has no pg_next; group endpoint returns 404 → stops
    assert urls == ["https://artnet.kr/p/solo-exhibitions/1300"]


def test_list_from_top_stops_on_empty_gallery():
    session = _StubSession({
        LIST_URLS[0]: _read("list_empty.html"),
        LIST_URLS[1]: _read("list_empty.html"),
    })
    adapter = ArtnetAdapter(session=session, max_list_pages=10)
    assert list(adapter.list_from_top()) == []


def test_parse_detail_returns_cached_exhibition():
    session = _StubSession({LIST_URLS[0]: _read("list_solo.html")})
    adapter = ArtnetAdapter(session=session, max_list_pages=1)
    # exhaust enough of list_from_top to populate cache for a known URL
    gen = adapter.list_from_top()
    first_url = next(gen)
    ex = adapter.parse_detail(first_url)
    assert ex.source_url == first_url
    assert ex.title.startswith("<건조한 배설")


def test_parse_detail_raises_when_url_not_listed():
    adapter = ArtnetAdapter(session=_StubSession({}), max_list_pages=1)
    with pytest.raises(RuntimeError):
        adapter.parse_detail("https://artnet.kr/p/solo-exhibitions/9999")

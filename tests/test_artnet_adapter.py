from datetime import date
from pathlib import Path
import pytest
from src.adapters.artnet import ArtnetAdapter, BASE_URL

FIX = Path(__file__).parent / "fixtures" / "artnet"


def _read(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8")


def test_parse_solo():
    a = ArtnetAdapter()
    ex = a._parse_html("https://artnet.kr/exh/100", _read("detail_solo.html"))
    assert ex.title == "홍길동 개인전"
    assert ex.venue == "갤러리 ABC"
    assert ex.start_date == date(2026, 5, 1)
    assert ex.end_date == date(2026, 5, 30)
    assert ex.year == 2026
    assert ex.artists_kr == ["홍길동"]
    assert ex.artists_en == ["Hong Gildong"]
    assert ex.source_url == "https://artnet.kr/exh/100"
    assert ex.source_site == "아트넷"


def test_parse_group():
    a = ArtnetAdapter()
    ex = a._parse_html("https://artnet.kr/exh/101", _read("detail_group.html"))
    assert ex.title == "2026 단체전 X"
    assert ex.artists_kr == ["김작가", "이작가", "박작가"]
    # 박작가는 영문 없음 → en 리스트 길이가 한글과 다를 수 있음
    assert ex.artists_en == ["Kim", "Lee"]


def test_parse_no_dates():
    a = ArtnetAdapter()
    ex = a._parse_html("https://artnet.kr/exh/102", _read("detail_no_dates.html"))
    assert ex.start_date is None
    assert ex.end_date is None
    assert ex.year is None  # 날짜·전시명 모두 연도 추출 불가
    assert ex.artists_kr == ["김작가"]

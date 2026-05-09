from datetime import date
from src.core.models import Exhibition


def test_exhibition_minimal_construction():
    ex = Exhibition(
        title="○○ 개인전",
        exhibition_type="미상",
        venue="갤러리 A",
        year=2026,
        start_date=None,
        end_date=None,
        artists_kr=[],
        artists_en=[],
        source_site="아트넷",
        source_url="https://artnet.kr/exh/12345",
    )
    assert ex.title == "○○ 개인전"
    assert ex.exhibition_type == "미상"


def test_exhibition_with_dates_and_artists():
    ex = Exhibition(
        title="단체전 X",
        exhibition_type="단체전",
        venue="갤러리 B",
        year=2026,
        start_date=date(2026, 5, 1),
        end_date=date(2026, 5, 30),
        artists_kr=["김작가", "이작가"],
        artists_en=["Kim", "Lee"],
        source_site="아트넷",
        source_url="https://artnet.kr/exh/22222",
    )
    assert len(ex.artists_kr) == 2
    assert ex.start_date.year == 2026

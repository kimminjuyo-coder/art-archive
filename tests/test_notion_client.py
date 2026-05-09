from datetime import date
from src.core.models import Exhibition
from src.core.notion_client import build_page_properties, EXHIBITION_TYPE_OPTIONS


def test_build_properties_basic():
    ex = Exhibition(
        title="홍길동 개인전",
        exhibition_type="개인전",
        venue="갤러리 A",
        year=2026,
        start_date=date(2026, 5, 1),
        end_date=date(2026, 5, 30),
        artists_kr=["홍길동"],
        artists_en=["Hong Gildong"],
        source_site="아트넷",
        source_url="https://artnet.kr/exh/100",
    )
    props = build_page_properties(ex)
    assert props["전시명"]["title"][0]["text"]["content"] == "홍길동 개인전"
    assert props["개인/단체"]["select"]["name"] == "개인전"
    assert props["전시 장소"]["rich_text"][0]["text"]["content"] == "갤러리 A"
    assert props["개최 연도"]["number"] == 2026
    assert props["전시 시작일"]["date"]["start"] == "2026-05-01"
    assert props["전시 종료일"]["date"]["start"] == "2026-05-30"
    assert props["참여 작가명_한글"]["rich_text"][0]["text"]["content"] == "홍길동"
    assert props["참여 작가명_영문"]["rich_text"][0]["text"]["content"] == "Hong Gildong"
    assert props["출처 사이트"]["select"]["name"] == "아트넷"
    assert props["출처 URL"]["url"] == "https://artnet.kr/exh/100"
    assert props["CV 확보 여부"]["select"]["name"] == "❌ 미확보"
    # 수집 시각은 ISO 형식
    assert "수집 시각" in props


def test_build_properties_with_none_dates():
    ex = Exhibition(
        title="X",
        exhibition_type="미상",
        venue="",
        year=None,
        start_date=None,
        end_date=None,
        artists_kr=[],
        artists_en=[],
        source_site="아트넷",
        source_url="https://artnet.kr/exh/200",
    )
    props = build_page_properties(ex)
    assert "전시 시작일" not in props or props["전시 시작일"]["date"] is None
    assert "전시 종료일" not in props or props["전시 종료일"]["date"] is None
    assert props["개최 연도"]["number"] is None


def test_options_constant():
    assert "개인전" in EXHIBITION_TYPE_OPTIONS
    assert "미상" in EXHIBITION_TYPE_OPTIONS

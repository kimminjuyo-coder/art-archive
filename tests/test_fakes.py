from datetime import date
from src.core.models import Exhibition
from tests.fakes import FakeNotionClient


def test_fake_starts_empty():
    fake = FakeNotionClient()
    assert fake.fetch_all_source_urls() == set()
    assert fake.created_pages == []


def test_fake_create_records_url():
    fake = FakeNotionClient()
    ex = Exhibition(
        title="A", exhibition_type="개인전", venue="V", year=2026,
        start_date=None, end_date=None,
        artists_kr=["김"], artists_en=[],
        source_site="아트넷", source_url="https://artnet.kr/exh/1",
    )
    fake.create_exhibition(ex)
    assert "https://artnet.kr/exh/1" in fake.fetch_all_source_urls()
    assert len(fake.created_pages) == 1


def test_fake_seeded_urls():
    fake = FakeNotionClient(seed_urls={"https://artnet.kr/exh/9"})
    assert fake.fetch_all_source_urls() == {"https://artnet.kr/exh/9"}

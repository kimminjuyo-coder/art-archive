from __future__ import annotations
from datetime import datetime, timezone
from typing import Iterable, Protocol
from src.core.models import Exhibition

EXHIBITION_TYPE_OPTIONS = ["개인전", "단체전", "기획전", "미상"]
SOURCE_SITE_OPTIONS = ["아트넷", "아트맵", "아트허브", "네오룩"]
CV_OPTIONS = ["✅ 완전 확보", "🔶 부분 확보", "❌ 미확보"]


def _rich_text(text: str) -> list[dict]:
    if not text:
        return []
    return [{"type": "text", "text": {"content": text}}]


def _date_prop(d) -> dict:
    if d is None:
        return {"date": None}
    return {"date": {"start": d.isoformat()}}


def build_page_properties(ex: Exhibition) -> dict:
    artists_kr_str = ", ".join(ex.artists_kr)
    artists_en_str = ", ".join(ex.artists_en)
    now_iso = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    return {
        "전시명": {"title": [{"type": "text", "text": {"content": ex.title}}]},
        "개인/단체": {"select": {"name": ex.exhibition_type}},
        "전시 장소": {"rich_text": _rich_text(ex.venue)},
        "개최 연도": {"number": ex.year},
        "전시 시작일": _date_prop(ex.start_date),
        "전시 종료일": _date_prop(ex.end_date),
        "참여 작가명_한글": {"rich_text": _rich_text(artists_kr_str)},
        "참여 작가명_영문": {"rich_text": _rich_text(artists_en_str)},
        "출처 사이트": {"select": {"name": ex.source_site}},
        "출처 URL": {"url": ex.source_url or None},
        "CV 확보 여부": {"select": {"name": "❌ 미확보"}},
        "수집 시각": {"date": {"start": now_iso}},
    }


class NotionClientProtocol(Protocol):
    def fetch_all_source_urls(self) -> set[str]: ...
    def create_exhibition(self, ex: Exhibition) -> None: ...


class NotionClient:
    """실제 Notion API 래퍼. notion-client(공식 SDK) 사용."""

    def __init__(self, token: str, database_id: str):
        from notion_client import Client
        self._client = Client(auth=token)
        self._db = database_id

    def fetch_all_source_urls(self) -> set[str]:
        urls: set[str] = set()
        cursor: str | None = None
        while True:
            kwargs = {"database_id": self._db, "page_size": 100}
            if cursor:
                kwargs["start_cursor"] = cursor
            res = self._client.databases.query(**kwargs)
            for row in res.get("results", []):
                prop = row["properties"].get("출처 URL", {})
                url = prop.get("url")
                if url:
                    urls.add(url)
            if not res.get("has_more"):
                break
            cursor = res.get("next_cursor")
        return urls

    def create_exhibition(self, ex: Exhibition) -> None:
        self._client.pages.create(
            parent={"database_id": self._db},
            properties=build_page_properties(ex),
        )

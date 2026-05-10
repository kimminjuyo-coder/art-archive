from __future__ import annotations
import re
from datetime import date
from typing import Iterator, Optional
from bs4 import BeautifulSoup
from src.adapters.base import SiteAdapter
from src.core.models import Exhibition
from src.utils.http import build_session, DEFAULT_TIMEOUT

LIST_URLS = [
    "https://artnet.kr/p/solo-exhibitions",
    "https://artnet.kr/p/group-exhibitions",
]

_ELLIPSIS_TOKENS = {"…", "...", "..."}

_DATE_RANGE_KR_RE = re.compile(
    r"(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일"
    r"\s*[~∼\-–]\s*"
    r"(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일"
)
_YEAR_IN_TITLE_RE = re.compile(r"(20\d{2})")
_ARTIST_EN_RE = re.compile(r"^(.+?)\s*\(([^)]+)\)\s*$")


def _parse_period(text: str) -> tuple[Optional[date], Optional[date]]:
    if not text:
        return None, None
    m = _DATE_RANGE_KR_RE.search(text)
    if not m:
        return None, None
    sy, sm, sd, ey, em, ed = (int(x) for x in m.groups())
    try:
        return date(sy, sm, sd), date(ey, em, ed)
    except ValueError:
        return None, None


def _extract_year_from_title(title: str) -> Optional[int]:
    if not title:
        return None
    m = _YEAR_IN_TITLE_RE.search(title)
    return int(m.group(1)) if m else None


def _parse_artists(text: str) -> tuple[list[str], list[str]]:
    if not text:
        return [], []
    artists_kr: list[str] = []
    artists_en: list[str] = []
    for raw in text.split(","):
        part = raw.strip()
        if not part or part in _ELLIPSIS_TOKENS:
            continue
        m = _ARTIST_EN_RE.match(part)
        if m:
            artists_kr.append(m.group(1).strip())
            artists_en.append(m.group(2).strip())
        else:
            artists_kr.append(part)
    return artists_kr, artists_en


class ArtnetAdapter(SiteAdapter):
    name = "artnet"
    source_label = "아트넷"

    def __init__(self, session=None, max_list_pages: int = 200):
        self._session = session or build_session()
        self._max_list_pages = max_list_pages
        self._cache: dict[str, Exhibition] = {}

    def list_from_top(self) -> Iterator[str]:
        for start_url in LIST_URLS:
            yield from self._iter_endpoint(start_url)

    def _iter_endpoint(self, start_url: str) -> Iterator[str]:
        url = start_url
        for _ in range(self._max_list_pages):
            resp = self._session.get(url, timeout=DEFAULT_TIMEOUT)
            if resp.status_code == 404:
                return
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.select(".gallery .gallery-item")
            if not cards:
                return
            for card in cards:
                ex = self._parse_card(card)
                if ex is None:
                    continue
                self._cache[ex.source_url] = ex
                yield ex.source_url
            next_a = soup.select_one("nav.pg_wrap a.pg_next")
            if next_a is None:
                return
            href = (next_a.get("href") or "").strip()
            if not href:
                return
            url = href

    def parse_detail(self, url: str) -> Exhibition:
        try:
            return self._cache[url]
        except KeyError:
            raise RuntimeError(
                f"no cached exhibition for {url}; list_from_top must run first"
            )

    def _parse_card(self, card) -> Optional[Exhibition]:
        link = card.select_one("h2 a[href]")
        if link is None:
            return None
        source_url = (link.get("href") or "").strip()
        if not source_url:
            return None
        title = link.get_text(strip=True)

        artists_text = ""
        period_text = ""
        venue_text = ""
        for li in card.select(".post-detail li"):
            icon = li.select_one("i")
            classes = set(icon.get("class") or []) if icon else set()
            content = li.get_text(strip=True)
            if "icon-magic-wand" in classes:
                artists_text = content
            elif "icon-calender" in classes:
                period_text = content
            elif "icon-location-pin" in classes:
                venue_text = content

        artists_kr, artists_en = _parse_artists(artists_text)
        start_date, end_date = _parse_period(period_text)
        year = start_date.year if start_date else _extract_year_from_title(title)

        return Exhibition(
            title=title,
            exhibition_type="미상",
            venue=venue_text,
            year=year,
            start_date=start_date,
            end_date=end_date,
            artists_kr=artists_kr,
            artists_en=artists_en,
            source_site="아트넷",
            source_url=source_url,
        )

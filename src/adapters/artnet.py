from __future__ import annotations
import re
from datetime import date
from typing import Iterator, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from src.adapters.base import SiteAdapter
from src.core.models import Exhibition
from src.utils.http import build_session

BASE_URL = "https://artnet.kr"
LIST_URL_TEMPLATE = "https://artnet.kr/exhibitions?page={page}"

_DATE_RANGE_RE = re.compile(r"(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})\s*[-~–]\s*(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})")
_YEAR_IN_TITLE_RE = re.compile(r"(20\d{2})")


def _parse_period(text: str) -> tuple[Optional[date], Optional[date]]:
    if not text:
        return None, None
    m = _DATE_RANGE_RE.search(text)
    if not m:
        return None, None
    sy, sm, sd, ey, em, ed = (int(x) for x in m.groups())
    try:
        return date(sy, sm, sd), date(ey, em, ed)
    except ValueError:
        return None, None


class ArtnetAdapter(SiteAdapter):
    name = "artnet"
    source_label = "아트넷"

    def __init__(self, session=None, max_list_pages: int = 200):
        self._session = session or build_session()
        self._max_list_pages = max_list_pages  # 안전장치

    # --- 내부 파서 (단위 테스트용) ---
    def _parse_html(self, url: str, html: str) -> Exhibition:
        soup = BeautifulSoup(html, "html.parser")
        title_el = soup.select_one(".exh-title")
        title = title_el.get_text(strip=True) if title_el else ""

        venue_el = soup.select_one(".exh-meta .venue")
        venue = venue_el.get_text(strip=True) if venue_el else ""

        period_el = soup.select_one(".exh-meta .period")
        period_txt = period_el.get_text(strip=True) if period_el else ""
        start_date, end_date = _parse_period(period_txt)

        if start_date:
            year = start_date.year
        else:
            ym = _YEAR_IN_TITLE_RE.search(title)
            year = int(ym.group(1)) if ym else None

        artists_kr: list[str] = []
        artists_en: list[str] = []
        for li in soup.select(".artists li"):
            kr_el = li.select_one(".kr")
            en_el = li.select_one(".en")
            if kr_el:
                kr_txt = kr_el.get_text(strip=True)
                if kr_txt:
                    artists_kr.append(kr_txt)
            if en_el:
                en_txt = en_el.get_text(strip=True)
                if en_txt:
                    artists_en.append(en_txt)

        return Exhibition(
            title=title,
            exhibition_type="미상",  # 코어가 분류
            venue=venue,
            year=year,
            start_date=start_date,
            end_date=end_date,
            artists_kr=artists_kr,
            artists_en=artists_en,
            source_site="아트넷",
            source_url=url,
        )

    # --- SiteAdapter 구현 ---
    def parse_detail(self, url: str) -> Exhibition:
        resp = self._session.get(url)
        resp.raise_for_status()
        return self._parse_html(url, resp.text)

    def list_from_top(self) -> Iterator[str]:
        for page in range(1, self._max_list_pages + 1):
            url = LIST_URL_TEMPLATE.format(page=page)
            resp = self._session.get(url)
            if resp.status_code == 404:
                return
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            anchors = soup.select(".exh-list .exh-item a.exh-link")
            if not anchors:
                return  # 마지막 페이지 도달
            for a in anchors:
                href = a.get("href")
                if href:
                    yield urljoin(BASE_URL, href)
            if not soup.select_one("a.next-page"):
                return

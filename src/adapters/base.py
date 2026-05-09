from abc import ABC, abstractmethod
from typing import Iterator
from src.core.models import Exhibition


class SiteAdapter(ABC):
    name: str = ""           # 식별자: "artnet"
    source_label: str = ""   # 노션 SELECT 옵션값: "아트넷"

    @abstractmethod
    def list_from_top(self) -> Iterator[str]:
        """사이트 목록을 위에서부터 훑으며 상세 페이지 URL을 yield."""

    @abstractmethod
    def parse_detail(self, url: str) -> Exhibition:
        """상세 페이지 → Exhibition. exhibition_type 판별은 코어가 함."""

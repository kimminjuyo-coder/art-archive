from dataclasses import dataclass, field
from datetime import date
from typing import Literal, Optional

ExhibitionType = Literal["개인전", "단체전", "기획전", "미상"]


@dataclass
class Exhibition:
    title: str
    exhibition_type: ExhibitionType
    venue: str
    year: Optional[int]
    start_date: Optional[date]
    end_date: Optional[date]
    artists_kr: list[str] = field(default_factory=list)
    artists_en: list[str] = field(default_factory=list)
    source_site: str = ""
    source_url: str = ""

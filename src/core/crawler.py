from typing import Literal

ExhibitionType = Literal["개인전", "단체전", "기획전", "미상"]
SOLO_KEYWORD = "개인전"


def classify_exhibition_type(title: str, artists_kr: list[str]) -> ExhibitionType:
    """개인/단체 판별 (스펙 §4):
    1) 전시명에 '개인전' 포함 → 개인전
    2) 작가 ≥ 2명 → 단체전
    3) 작가 == 1명 → 개인전
    4) 작가 == 0명 → 미상
    """
    if SOLO_KEYWORD in (title or ""):
        return "개인전"
    n = len(artists_kr or [])
    if n >= 2:
        return "단체전"
    if n == 1:
        return "개인전"
    return "미상"

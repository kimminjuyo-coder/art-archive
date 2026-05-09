from src.core.crawler import classify_exhibition_type


def test_keyword_solo_overrides_artist_count():
    # 전시명에 "개인전" 포함 → 작가 수 무관하게 개인전
    assert classify_exhibition_type("홍길동 개인전", ["홍길동", "이작가", "박작가"]) == "개인전"


def test_two_or_more_artists_is_group():
    assert classify_exhibition_type("○○○展", ["김", "이"]) == "단체전"
    assert classify_exhibition_type("Big Show", ["A", "B", "C"]) == "단체전"


def test_one_artist_is_solo():
    assert classify_exhibition_type("작가전", ["김"]) == "개인전"


def test_no_artists_is_unknown():
    assert classify_exhibition_type("미정 전시", []) == "미상"


def test_keyword_even_with_zero_artists():
    # 키워드 우선 — 작가 0명이어도 키워드가 있으면 개인전
    assert classify_exhibition_type("○○ 개인전", []) == "개인전"

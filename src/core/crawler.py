import time
from dataclasses import dataclass
from typing import Literal

from src.core.models import Exhibition
from src.utils.logging import get_logger

logger = get_logger(__name__)

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


@dataclass
class RunResult:
    inserted: int = 0
    skipped_dup: int = 0
    errors: int = 0
    aborted: bool = False
    duration_sec: float = 0.0


class Crawler:
    def __init__(
        self,
        adapter,
        notion,
        sleep_seconds: float = 1.0,
        daily_seen_threshold: int = 5,
        parse_error_threshold: int = 10,
    ):
        self.adapter = adapter
        self.notion = notion
        self.sleep_seconds = sleep_seconds
        self.daily_seen_threshold = daily_seen_threshold
        self.parse_error_threshold = parse_error_threshold

    def run(self, mode: str) -> RunResult:
        assert mode in ("backfill", "daily")
        started = time.monotonic()
        logger.info("run_start", extra={"event": "run_start", "mode": mode, "adapter": self.adapter.name})

        seen_urls = self.notion.fetch_all_source_urls()
        result = RunResult()
        seen_streak = 0
        consecutive_errors = 0

        for url in self.adapter.list_from_top():
            if url in seen_urls:
                result.skipped_dup += 1
                seen_streak += 1
                if mode == "daily" and seen_streak >= self.daily_seen_threshold:
                    logger.info(
                        "daily_stop_threshold_reached",
                        extra={"event": "daily_stop", "threshold": self.daily_seen_threshold},
                    )
                    break
                continue

            seen_streak = 0
            try:
                ex = self.adapter.parse_detail(url)
            except Exception as e:
                result.errors += 1
                consecutive_errors += 1
                logger.warning(
                    "parse_error",
                    extra={"event": "parse_error", "url": url, "reason": str(e)},
                )
                if consecutive_errors >= self.parse_error_threshold:
                    logger.error(
                        "parse_error_threshold",
                        extra={"event": "abort", "threshold": self.parse_error_threshold},
                    )
                    result.aborted = True
                    break
                continue

            consecutive_errors = 0
            ex.exhibition_type = classify_exhibition_type(ex.title, ex.artists_kr)
            ex.source_site = self.adapter.source_label

            try:
                self.notion.create_exhibition(ex)
                seen_urls.add(url)
                result.inserted += 1
                logger.info(
                    "exhibition_inserted",
                    extra={"event": "exhibition_inserted", "url": url, "title": ex.title},
                )
            except Exception as e:
                result.errors += 1
                logger.warning(
                    "notion_insert_error",
                    extra={"event": "notion_insert_error", "url": url, "reason": str(e)},
                )

            if self.sleep_seconds > 0:
                time.sleep(self.sleep_seconds)

        result.duration_sec = round(time.monotonic() - started, 2)
        logger.info(
            "run_end",
            extra={
                "event": "run_end", "mode": mode, "adapter": self.adapter.name,
                "inserted": result.inserted, "skipped_dup": result.skipped_dup,
                "errors": result.errors, "aborted": result.aborted,
                "duration_sec": result.duration_sec,
            },
        )
        return result

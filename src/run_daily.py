from __future__ import annotations
import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from src.core.crawler import Crawler
from src.core.notion_client import NotionClient
from src.core.state import load_state, save_state
from src.utils.logging import get_logger

STATE_FILE = Path("state/state.json")
logger = get_logger(__name__)


def build_adapter(name: str):
    if name == "artnet":
        from src.adapters.artnet import ArtnetAdapter
        return ArtnetAdapter()
    raise ValueError(f"unknown adapter: {name}")


def build_notion_client() -> NotionClient:
    load_dotenv()
    token = os.environ["NOTION_TOKEN"]
    db_id = os.environ["NOTION_DB_ID"]
    return NotionClient(token=token, database_id=db_id)


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    adapter = build_adapter(args.adapter)
    if args.dry_run:
        # 노션 호출 없는 출력만
        for i, url in enumerate(adapter.list_from_top()):
            print(url)
            if i >= 9:
                break
        return 0

    notion = build_notion_client()
    crawler = Crawler(adapter, notion)
    result = crawler.run(mode="daily")

    state = load_state(STATE_FILE)
    state[adapter.name] = {
        "last_run_at": _now_iso(),
        "last_mode": "daily",
        "inserted": result.inserted,
        "skipped_dup": result.skipped_dup,
        "errors": result.errors,
    }
    save_state(STATE_FILE, state)

    # 자동 실패 판정 (스펙 §8)
    zero_activity = (result.inserted == 0 and result.skipped_dup == 0)
    too_many_errors = result.errors >= 10
    if result.aborted or zero_activity or too_many_errors:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

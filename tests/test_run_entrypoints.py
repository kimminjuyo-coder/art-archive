import json
from pathlib import Path
from datetime import date
from src.core.models import Exhibition
import src.run_daily as run_daily_mod
from tests.fakes import FakeNotionClient


class _StaticAdapter:
    name = "artnet"
    source_label = "아트넷"
    def list_from_top(self):
        yield "https://artnet.kr/exh/1"
    def parse_detail(self, url):
        return Exhibition(
            title="t", exhibition_type="미상", venue="V", year=2026,
            start_date=None, end_date=None,
            artists_kr=["김"], artists_en=[],
            source_site="아트넷", source_url=url,
        )


def test_run_daily_writes_state(tmp_path: Path, monkeypatch):
    state_file = tmp_path / "state.json"
    notion = FakeNotionClient()

    monkeypatch.setattr(run_daily_mod, "build_adapter", lambda name: _StaticAdapter())
    monkeypatch.setattr(run_daily_mod, "build_notion_client", lambda: notion)
    monkeypatch.setattr(run_daily_mod, "STATE_FILE", state_file)

    code = run_daily_mod.main(["--adapter", "artnet"])
    assert code == 0
    saved = json.loads(state_file.read_text(encoding="utf-8"))
    assert "artnet" in saved
    assert saved["artnet"]["inserted"] == 1
    assert saved["artnet"]["last_mode"] == "daily"
    assert "last_run_at" in saved["artnet"]


def test_run_daily_returns_exit_1_on_zero_activity(tmp_path: Path, monkeypatch):
    state_file = tmp_path / "state.json"
    class _EmptyAdapter:
        name = "artnet"; source_label = "아트넷"
        def list_from_top(self): return iter([])
        def parse_detail(self, url): raise NotImplementedError
    notion = FakeNotionClient()
    monkeypatch.setattr(run_daily_mod, "build_adapter", lambda name: _EmptyAdapter())
    monkeypatch.setattr(run_daily_mod, "build_notion_client", lambda: notion)
    monkeypatch.setattr(run_daily_mod, "STATE_FILE", state_file)
    code = run_daily_mod.main(["--adapter", "artnet"])
    # inserted=0, skipped=0 → 알림 신호로 exit 1
    assert code == 1


import src.run_backfill as run_backfill_mod


def test_run_backfill_writes_state(tmp_path: Path, monkeypatch):
    state_file = tmp_path / "state.json"
    notion = FakeNotionClient()
    monkeypatch.setattr(run_backfill_mod, "build_adapter", lambda name: _StaticAdapter())
    monkeypatch.setattr(run_backfill_mod, "build_notion_client", lambda: notion)
    monkeypatch.setattr(run_backfill_mod, "STATE_FILE", state_file)
    code = run_backfill_mod.main(["--adapter", "artnet"])
    assert code == 0
    saved = json.loads(state_file.read_text(encoding="utf-8"))
    assert saved["artnet"]["last_mode"] == "backfill"
    assert saved["artnet"]["inserted"] == 1

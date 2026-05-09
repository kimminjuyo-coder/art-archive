import json
from pathlib import Path
from src.core.state import load_state, save_state


def test_load_state_returns_empty_dict_when_missing(tmp_path: Path):
    state_file = tmp_path / "state.json"
    assert load_state(state_file) == {}


def test_save_then_load_roundtrip(tmp_path: Path):
    state_file = tmp_path / "state.json"
    payload = {"artnet": {"last_run_at": "2026-05-04T03:00:00+09:00", "inserted": 12}}
    save_state(state_file, payload)
    loaded = load_state(state_file)
    assert loaded == payload


def test_save_state_creates_parent_dir(tmp_path: Path):
    state_file = tmp_path / "nested" / "state.json"
    save_state(state_file, {"a": 1})
    assert state_file.exists()

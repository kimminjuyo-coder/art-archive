import json
import logging
from src.utils.logging import get_logger, mask_secrets


def test_mask_secrets_redacts_notion_token():
    msg = "token=secret_AbCdEf1234567890AbCdEf1234567890AbCdEf12 done"
    out = mask_secrets(msg)
    assert "secret_AbCdEf" not in out
    assert "***" in out


def test_logger_emits_json_line(capsys):
    # Use unique logger name to ensure clean state
    logger = get_logger("test.emits_json")
    logger.info("hello", extra={"event": "run_start", "adapter": "artnet"})
    captured = capsys.readouterr().err  # stderr by default
    line = captured.strip().splitlines()[-1]
    obj = json.loads(line)
    assert obj["event"] == "run_start"
    assert obj["adapter"] == "artnet"
    assert obj["level"] == "INFO"
    assert "ts" in obj


def test_logger_masks_token_in_message(capsys):
    # Use unique logger name to ensure clean state
    logger = get_logger("test.masks_token")
    logger.info("using token=secret_AbCdEf1234567890AbCdEf1234567890AbCdEf12")
    captured = capsys.readouterr().err
    assert "secret_AbCdEf" not in captured
    assert "***" in captured

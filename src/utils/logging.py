import json
import logging
import re
import sys
from datetime import datetime, timezone

# 노션 Integration 토큰 패턴: secret_ 로 시작, 영숫자 32자 이상
_TOKEN_PATTERN = re.compile(r"\bsecret_[A-Za-z0-9]{32,}\b")


def mask_secrets(text: str) -> str:
    return _TOKEN_PATTERN.sub("***", text)


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
            "level": record.levelname,
            "msg": mask_secrets(record.getMessage()),
        }
        # extra 필드 병합 (기본 LogRecord 속성 제외)
        reserved = set(logging.LogRecord("", 0, "", 0, None, None, None).__dict__.keys())
        reserved.update({"message", "asctime"})
        for k, v in record.__dict__.items():
            if k not in reserved:
                payload[k] = v
        return json.dumps(payload, ensure_ascii=False)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(_JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger

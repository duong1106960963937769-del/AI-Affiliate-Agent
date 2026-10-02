"""Logging ra thư mục logs/ (app.log, api.log, scanner.log, error.log) và che thông tin nhạy cảm."""
import logging
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path

SENSITIVE = "access_token|refresh_token|api_key|apikey|secret|client_secret|password|passwd|cookie|set-cookie|authorization|token"
# key=value, key: value, "key": "value"
_KV = re.compile(rf"""(?P<k>["']?(?:{SENSITIVE})["']?\s*[=:]\s*)(?P<q>["']?)(?P<v>[^\s"',;&}}]+)""", re.I)
_BEARER = re.compile(r"(Bearer\s+)[A-Za-z0-9._\-~+/=]+", re.I)


def redact(text: str) -> str:
    text = _BEARER.sub(r"\1********", text)
    return _KV.sub(lambda m: f"{m.group('k')}{m.group('q')}********", text)


class RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return redact(super().format(record))  # gồm cả traceback


FMT = RedactingFormatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
LOG_FILES = ("app", "api", "scanner", "error")


def _file_handler(path: Path, level: int) -> logging.Handler:
    h = RotatingFileHandler(path, maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    h.setLevel(level)
    h.setFormatter(FMT)
    h._aff_path = str(path)  # type: ignore[attr-defined]
    return h


def setup_logging(log_dir: str) -> Path:
    d = Path(log_dir)
    d.mkdir(parents=True, exist_ok=True)
    error_path = d / "error.log"
    for name in ("app", "api", "scanner"):
        lg = logging.getLogger(name)
        for h in list(lg.handlers):  # gọi lại nhiều lần (test) không nhân đôi handler
            lg.removeHandler(h)
            h.close()
        lg.setLevel(logging.INFO)
        lg.propagate = False
        lg.addHandler(_file_handler(d / f"{name}.log", logging.INFO))
        lg.addHandler(_file_handler(error_path, logging.ERROR))
    return d


def tail_log(log_dir: str, name: str, lines: int = 200) -> list[str]:
    if name not in LOG_FILES:
        raise ValueError("Tên log không hợp lệ")
    p = Path(log_dir) / f"{name}.log"
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8", errors="replace") as f:
        return [redact(l.rstrip("\n")) for l in f.readlines()[-lines:]]

"""Plain-English run log. Every builder step writes here: logs/run.log"""
from datetime import datetime
from pathlib import Path

LOG_FILE = Path(__file__).resolve().parent.parent / "logs" / "run.log"


def log(message, level="INFO"):
    LOG_FILE.parent.mkdir(exist_ok=True)
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S}  {level:<5}  {message}"
    print(line)
    with LOG_FILE.open("a") as f:
        f.write(line + "\n")


def error(message):
    log(message, "ERROR")

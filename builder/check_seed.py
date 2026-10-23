"""Read the starting list and log what's in it."""
import csv
from pathlib import Path
from log import log

SEED = Path(__file__).resolve().parent.parent / "data" / "seed" / "oca_2026.csv"

log("Run started: check starting list")
rows = list(csv.DictReader(SEED.open()))
kept = [r for r in rows if r["status"] == "keep"]
for r in rows:
    if r["status"] == "left_off":
        log(f"Left off: {r['name']} - {r['leave_off_reason']}")
log(f"{len(rows)} Toronto-area co-ops in the PDF: {len(kept)} kept "
    f"({sum(r['chain'] == 'yes' for r in kept)} are chains to expand), {len(rows) - len(kept)} left off")
log("Run finished")

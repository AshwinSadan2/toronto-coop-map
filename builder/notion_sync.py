"""Add the checked co-op list to Notion: one database row per location.

Safe by design:
  - Only ADDS co-ops that aren't in Notion yet. Existing rows (and your hand edits) are never touched.
  - Shows a preview first and writes nothing until you type "yes".

The database "Co-op list" lives inside the one Notion page shared with the connection.
It is created on the first run (also shown in the preview).

Run:  .venv/bin/python builder/notion_sync.py            (preview, then asks "yes")
      .venv/bin/python builder/notion_sync.py --preview  (preview only, never writes)
"""
import csv
import json
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

from export_site import NEIGHBOURHOODS, find_neighbourhood
from log import error, log

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "data" / "build" / "coops_checked.csv"
API = "https://api.notion.com/v1"
DB_TITLE = "Co-op list"

CATEGORIES = ["Grocery & Food", "Banking", "Insurance", "Home & Hardware", "Childcare", "Arts & Culture",
              "Shops", "Health & Wellness", "Getting Around", "Places to Stay"]

# Columns of the Notion database. "Show on site" is the owner's switch for hiding a co-op.
SCHEMA = {
    "Name": {"title": {}},
    "Category": {"select": {"options": [{"name": c} for c in CATEGORIES]}},
    "Show on site": {"checkbox": {}},
    "Address": {"rich_text": {}},
    "Neighbourhood": {"rich_text": {}},
    "Phone": {"phone_number": {}},
    "Website": {"url": {}},
    "Hours": {"rich_text": {}},
    "Card note": {"rich_text": {}},
    "Why it's listed": {"rich_text": {}},
    "Source": {"rich_text": {}},
    "Chain branch": {"checkbox": {}},
    "Legal name": {"rich_text": {}},
    "Google name": {"rich_text": {}},
    "Google match": {"select": {"options": [{"name": "good"}, {"name": "approved"}, {"name": "check"}]}},
    "Google Maps link": {"url": {}},
    "Google place ID": {"rich_text": {}},
    "Latitude": {"number": {}},
    "Longitude": {"number": {}},
    "Last checked": {"date": {}},
    "Review notes": {"rich_text": {}},
}


def call(method, path, body=None):
    """One Notion request, waiting and retrying if Notion says we're going too fast."""
    for attempt in range(5):
        r = requests.request(method, f"{API}{path}", json=body, timeout=30, headers={
            "Authorization": f"Bearer {os.environ['NOTION_API_KEY']}",
            "Notion-Version": "2026-03-11",
        })
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(float(r.headers.get("Retry-After", 2 ** attempt)))
            continue
        if not r.ok:
            raise RuntimeError(f"Notion said {r.status_code} on {method} {path}: {r.json().get('message')}")
        time.sleep(0.35)  # Notion allows about 3 requests a second
        return r.json()
    raise RuntimeError(f"Notion kept refusing {method} {path}")


def text(value):
    return {"rich_text": [{"text": {"content": value[:2000]}}] if value else []}


def find_home_page():
    pages, cursor = [], None
    while True:
        body = {"filter": {"property": "object", "value": "page"}, "page_size": 100,
                **({"start_cursor": cursor} if cursor else {})}
        res = call("POST", "/search", body)
        pages += [p for p in res["results"] if p["parent"]["type"] == "workspace"]
        if not res["has_more"]:
            break
        cursor = res["next_cursor"]
    if len(pages) != 1:
        raise RuntimeError(f"Expected the connection to see exactly 1 top-level page, it sees {len(pages)}")
    return pages[0]["id"]


def find_data_source(page_id):
    """The 'Co-op list' database inside the home page, or None if it doesn't exist yet."""
    for block in call("GET", f"/blocks/{page_id}/children?page_size=100")["results"]:
        if block["type"] == "child_database" and block["child_database"]["title"] == DB_TITLE:
            return call("GET", f"/databases/{block['id']}")["data_sources"][0]["id"]
    return None


def existing_keys(data_source_id):
    """Google place ID (or name + address) of every row already in Notion."""
    keys, cursor = set(), None
    while True:
        body = {"page_size": 100, **({"start_cursor": cursor} if cursor else {})}
        res = call("POST", f"/data_sources/{data_source_id}/query", body)
        for page in res["results"]:
            p = page["properties"]
            place_id = "".join(t["plain_text"] for t in p["Google place ID"]["rich_text"])
            name = "".join(t["plain_text"] for t in p["Name"]["title"])
            address = "".join(t["plain_text"] for t in p["Address"]["rich_text"])
            keys.add(place_id or f"{name}|{address}".lower())
        if not res["has_more"]:
            return keys
        cursor = res["next_cursor"]


def row_key(r, address):
    return r["google_place_id"] or f"{r['name']}|{address}".lower()


def match_label(match):
    """Short label for the Google match column; the full sentence goes into Review notes."""
    for label in ("check", "good (approved", "good"):
        if match.startswith(label):
            return {"good (approved": "approved"}.get(label, label)
    return None


def row_properties(r, address, hood):
    label = match_label(r["match"])
    notes = " / ".join(n for n in [r["match"] if label == "check" else "", r["notes"]] if n)
    return {
        "Name": {"title": [{"text": {"content": r["name"]}}]},
        "Category": {"select": {"name": r["category"]}},
        "Show on site": {"checkbox": True},
        "Address": text(address),
        "Neighbourhood": text(hood),
        "Phone": {"phone_number": r["phone"] or None},
        "Website": {"url": r["website"] or None},
        "Hours": text("\n".join(h for h in r["hours"].split(" | ") if h)),
        "Card note": text(r["card_note"]),
        "Why it's listed": text(r["reason"]),
        "Source": text(r["source"]),
        "Chain branch": {"checkbox": r["chain"] == "yes"},
        "Legal name": text(r["legal_name"]),
        "Google name": text(r["google_name"]),
        "Google match": {"select": {"name": label} if label else None},
        "Google Maps link": {"url": r["google_maps_url"] or None},
        "Google place ID": text(r["google_place_id"]),
        "Latitude": {"number": float(r["lat"])},
        "Longitude": {"number": float(r["lng"])},
        "Last checked": {"date": {"start": r["last_checked"]} if r["last_checked"] else None},
        "Review notes": text(notes),
    }


def main():
    preview_only = "--preview" in sys.argv
    load_dotenv(ROOT / ".env")
    log("Run started: add co-ops to Notion" + (" (preview only)" if preview_only else ""))

    page_id = find_home_page()
    data_source_id = find_data_source(page_id)
    have = existing_keys(data_source_id) if data_source_id else set()

    areas = [(f["properties"]["AREA_NAME"], f["geometry"]["coordinates"])
             for f in json.loads(NEIGHBOURHOODS.read_text())["features"]]
    new_rows, already = [], 0
    for r in csv.DictReader(SOURCE.open()):
        if not r["lat"]:
            log(f"Skipped {r['name']}: no map position", "WARN")
            continue
        address = r["google_address"].replace(", Canada", "") if r["google_address"] else f"{r['address']}, Toronto, ON"
        if row_key(r, address) in have:
            already += 1
            continue
        hood = find_neighbourhood(areas, float(r["lat"]), float(r["lng"]))
        new_rows.append((r, row_properties(r, address, hood)))

    # ---- preview ----
    print()
    if not data_source_id:
        print(f'Will create a database "{DB_TITLE}" in your Notion page.')
    print(f"Adding {len(new_rows)} co-ops, 0 changes ({already} already in Notion, left untouched).")
    by_cat = {}
    for r, _ in new_rows:
        by_cat[r["category"]] = by_cat.get(r["category"], 0) + 1
    for cat in sorted(by_cat, key=lambda c: -by_cat[c]):
        print(f"  {by_cat[cat]:>4}  {cat}")
    print()
    log(f"Preview: adding {len(new_rows)}, {already} already in Notion")

    if not new_rows and data_source_id:
        log("Nothing to add. Run finished")
        return
    if preview_only:
        log("Preview only, nothing written. Run finished")
        return
    if input('Type "yes" to write this to Notion: ').strip().lower() != "yes":
        log("Not approved, nothing written. Run finished")
        return

    # ---- write ----
    if not data_source_id:
        db = call("POST", "/databases", {
            "parent": {"type": "page_id", "page_id": page_id},
            "title": [{"text": {"content": DB_TITLE}}],
            "initial_data_source": {"properties": SCHEMA},
        })
        data_source_id = db["data_sources"][0]["id"]
        log(f'Notion write: created database "{DB_TITLE}"')
    added = 0
    for r, props in new_rows:
        try:
            call("POST", "/pages", {"parent": {"type": "data_source_id", "data_source_id": data_source_id},
                                    "properties": props})
            added += 1
            log(f"Notion write: added {r['name']}")
        except RuntimeError as e:
            error(f"Couldn't add {r['name']} to Notion: {e}")
    log(f"Result: {added} of {len(new_rows)} co-ops added to Notion")
    log("Run finished")


if __name__ == "__main__":
    main()

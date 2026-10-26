"""Publish: copy the Notion co-op list into the website's data file (site/data/coops.json).

Only rows with "Show on site" ticked are published. Stops and asks before publishing
if the number of co-ops drops by more than 10% compared with what's on the site now.

Run:  .venv/bin/python builder/publish.py
Then put it online:  commit and push (Vercel rebuilds the site from GitHub).
"""
import json
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from export_site import DISTRICTS, NEIGHBOURHOODS, OUT, POPULAR_NAMES, find_neighbourhood
from log import log
from notion_sync import call, find_data_source, find_home_page

ROOT = Path(__file__).resolve().parent.parent
MAX_DROP = 0.10


def plain(prop):
    kind = prop["type"]
    if kind in ("title", "rich_text"):
        return "".join(t["plain_text"] for t in prop[kind]).strip()
    if kind == "select":
        return prop["select"]["name"] if prop["select"] else ""
    if kind == "date":
        return prop["date"]["start"] if prop["date"] else ""
    return prop[kind]  # checkbox, number, url, phone_number


def notion_rows(data_source_id):
    rows, cursor = [], None
    while True:
        body = {"page_size": 100, **({"start_cursor": cursor} if cursor else {})}
        res = call("POST", f"/data_sources/{data_source_id}/query", body)
        rows += [(page["id"], {k: plain(v) for k, v in page["properties"].items()}) for page in res["results"]]
        if not res["has_more"]:
            return rows
        cursor = res["next_cursor"]


def main():
    load_dotenv(ROOT / ".env")
    log("Run started: publish Notion list to the website")
    data_source_id = find_data_source(find_home_page())
    if not data_source_id:
        raise RuntimeError("No 'Co-op list' database in Notion yet. Run builder/notion_sync.py first")

    areas = [(f["properties"]["AREA_NAME"], f["geometry"]["coordinates"])
             for f in json.loads(NEIGHBOURHOODS.read_text())["features"]]
    popular_for = {}
    for popular, officials in POPULAR_NAMES.items():
        for o in officials:
            popular_for.setdefault(o, []).append(popular)

    coops, hidden = [], 0
    for page_id, r in notion_rows(data_source_id):
        if not r["Show on site"]:
            hidden += 1
            log(f"Hidden (Show on site unticked): {r['Name']}")
            continue
        if not r["Name"] or r["Latitude"] is None or r["Longitude"] is None:
            log(f"Skipped a row with no name or map position ({r['Name'] or 'no name'})", "WARN")
            continue
        lat, lng = round(r["Latitude"], 6), round(r["Longitude"], 6)
        hood = r["Neighbourhood"] or find_neighbourhood(areas, lat, lng)
        district = next((d for d in DISTRICTS if f", {d}, ON" in r["Address"]), "")
        directions = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}"
        if r["Google place ID"]:
            directions += f"&destination_place_id={r['Google place ID']}"
        coops.append({
            "id": r["Google place ID"] or page_id,
            "name": r["Name"],
            "category": r["Category"],
            "note": r["Card note"],
            "address": r["Address"],
            "neighbourhood": hood,
            "searchAreas": [hood, *popular_for.get(hood, []), district],
            "lat": lat, "lng": lng,
            "phone": r["Phone"] or "",
            "hours": [h for h in r["Hours"].splitlines() if h.strip()],
            "website": r["Website"] or "",
            "directions": directions,
            "lastChecked": r["Last checked"],
        })

    old = len(json.loads(OUT.read_text())["coops"]) if OUT.exists() else 0
    log(f"Publish: {old} co-ops on the site now, {len(coops)} in Notion to publish ({hidden} hidden)")
    if old and len(coops) < old * (1 - MAX_DROP):
        print(f"\nWarning: the co-op count would drop from {old} to {len(coops)} "
              f"(more than {MAX_DROP:.0%}). Something may be wrong in Notion.")
        if input('Type "yes" to publish anyway: ').strip().lower() != "yes":
            log("Publish stopped: count dropped too much, not approved. Nothing changed")
            sys.exit(1)
        log("Big drop approved by owner")

    coops.sort(key=lambda c: c["name"].lower())
    OUT.write_text(json.dumps({"updated": date.today().isoformat(), "coops": coops}, ensure_ascii=False, indent=1))
    log(f"Result: published {len(coops)} co-ops to {OUT.relative_to(ROOT)} (was {old})")
    log("Run finished")


if __name__ == "__main__":
    main()

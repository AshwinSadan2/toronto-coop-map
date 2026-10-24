"""Turn the checked co-op list into the website's data file: site/data/coops.json

Adds each co-op's City of Toronto neighbourhood (plus popular names like "Leslieville"),
and leaves out internal review notes. Temporary source until the Notion publish step exists.

Run:  .venv/bin/python builder/export_site.py
"""
import csv
import json
from datetime import date
from pathlib import Path

from log import log

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "data" / "build" / "coops_checked.csv"
NEIGHBOURHOODS = ROOT / "data" / "local" / "neighbourhoods.geojson"  # City of Toronto open data, 158 areas
OUT = ROOT / "site" / "data" / "coops.json"

# Popular names people search for -> official City of Toronto neighbourhoods they fall in
POPULAR_NAMES = {
    "Leslieville": ["South Riverdale"], "Riverside": ["South Riverdale"],
    "Greektown": ["Danforth", "Playter Estates-Danforth"], "The Danforth": ["Danforth", "Playter Estates-Danforth"],
    "Kensington Market": ["Kensington-Chinatown"], "Chinatown": ["Kensington-Chinatown"],
    "The Annex": ["Annex"], "Koreatown": ["Palmerston-Little Italy"], "Little Italy": ["Palmerston-Little Italy"],
    "Liberty Village": ["Fort York-Liberty Village"], "Bloor West Village": ["Runnymede-Bloor West Village"],
    "High Park": ["High Park North", "High Park-Swansea"], "The Junction": ["Junction Area"],
    "Parkdale": ["South Parkdale"], "Corso Italia": ["Corso Italia-Davenport"],
    "Cabbagetown": ["Cabbagetown-South St.James Town"], "St. James Town": ["North St.James Town"],
    "Church and Wellesley": ["Church-Wellesley"], "The Village": ["Church-Wellesley"],
    "Financial District": ["Yonge-Bay Corridor"], "Entertainment District": ["Wellington Place"],
    "St. Lawrence": ["St Lawrence-East Bayfront-The Islands"],
    "Distillery District": ["St Lawrence-East Bayfront-The Islands"],
    "Downtown": ["Yonge-Bay Corridor", "Downtown Yonge East", "Wellington Place", "Harbourfront-CityPlace",
                 "St Lawrence-East Bayfront-The Islands", "Kensington-Chinatown", "University", "Moss Park",
                 "Bay-Cloverhill"],
    "Leaside": ["Leaside-Bennington"], "Davisville": ["South Eglinton-Davisville"],
    "Midtown": ["Yonge-Eglinton", "South Eglinton-Davisville", "Yonge-St.Clair"],
    "The Beach": ["The Beaches"], "Beaches": ["The Beaches"], "Roncy": ["Roncesvalles"],
    "Queen West": ["West Queen West", "Trinity-Bellwoods"], "Willowdale": ["East Willowdale", "Willowdale West"],
    "Don Mills": ["Banbury-Don Mills"], "Swansea": ["High Park-Swansea"], "Mimico": ["Mimico-Queensway"],
}
DISTRICTS = ["Scarborough", "North York", "Etobicoke", "East York", "York"]


def point_in_ring(lng, lat, ring):
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > lat) != (yj > lat) and lng < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def find_neighbourhood(areas, lat, lng):
    for name, polygons in areas:
        if any(point_in_ring(lng, lat, poly[0]) for poly in polygons):
            return name
    return ""


def main():
    log("Run started: export website data")
    areas = [(f["properties"]["AREA_NAME"], f["geometry"]["coordinates"])
             for f in json.loads(NEIGHBOURHOODS.read_text())["features"]]
    popular_for = {}
    for popular, officials in POPULAR_NAMES.items():
        for o in officials:
            popular_for.setdefault(o, []).append(popular)

    coops = []
    for r in csv.DictReader(SOURCE.open()):
        if not r["lat"]:
            log(f"Skipped {r['name']}: no map position", "WARN")
            continue
        lat, lng = round(float(r["lat"]), 6), round(float(r["lng"]), 6)
        hood = find_neighbourhood(areas, lat, lng)
        if not hood:
            log(f"{r['name']} is outside every Toronto neighbourhood ({r['google_address'] or r['address']})", "WARN")
        address = r["google_address"].replace(", Canada", "") if r["google_address"] else f"{r['address']}, Toronto, ON"
        district = next((d for d in DISTRICTS if f", {d}, ON" in address), "")
        directions = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}"
        if r["google_place_id"]:
            directions += f"&destination_place_id={r['google_place_id']}"
        coops.append({
            "id": r["google_place_id"] or f"cmc-{r['cmc_id']}" or r["name"],
            "name": r["name"],
            "category": r["category"],
            "note": r.get("card_note", ""),
            "address": address,
            "neighbourhood": hood,
            "searchAreas": [hood, *popular_for.get(hood, []), district],
            "lat": lat, "lng": lng,
            "phone": r["phone"],
            "hours": [h for h in r["hours"].split(" | ") if h],
            "website": r["website"],
            "directions": directions,
            "lastChecked": r["last_checked"],
        })
        log(f"Exported: {r['name']} ({hood or 'no neighbourhood'})")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"updated": date.today().isoformat(), "coops": coops}, ensure_ascii=False, indent=1))
    log(f"Result: {len(coops)} co-ops written to {OUT.relative_to(ROOT)}")
    log("Run finished")


if __name__ == "__main__":
    main()

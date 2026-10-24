"""Milestone 3: check every location on Google (OpenStreetMap as backup) and find chain branches.

For each kept location: confirm it exists, is open, and get hours, phone, website.
For each chain (Home Hardware, Carpet One, Co-operators, ClimateCare): find every Toronto branch.

Reads:   data/build/coops.csv, data/build/left_off.csv   (from pull_sources.py)
Writes:  data/build/coops_checked.csv     one row per location, with Google details
         data/build/left_off_checked.csv  left_off.csv + anything dropped here, with the reason

Google answers are saved in data/cache/google/ so re-runs don't pay twice.
Hard stop at MAX_CALLS paid Google requests per run.

Run:  .venv/bin/python builder/lookup_google.py
"""
import csv
import hashlib
import json
import math
import re
import sys
import time
from datetime import date
from pathlib import Path

import requests
from dotenv import dotenv_values

from log import error, log

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "data" / "build"
CACHE = ROOT / "data" / "cache" / "google"
OSM_CACHE = ROOT / "data" / "cache" / "osm"

MAX_CALLS = 400
SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
FIELDS = ("places.id,places.displayName,places.formattedAddress,places.location,places.businessStatus,"
          "places.regularOpeningHours.weekdayDescriptions,places.nationalPhoneNumber,places.websiteUri,"
          "places.googleMapsUri,places.primaryTypeDisplayName")

TORONTO_CITIES = ("Toronto, ON", "North York, ON", "Scarborough, ON", "Etobicoke, ON", "East York, ON", "York, ON")
# Toronto split into 4 boxes, so each chain search stays under Google's 60-results-per-search cap
TORONTO_BOXES = [((43.58, -79.64), (43.72, -79.38)), ((43.58, -79.38), (43.72, -79.11)),
                 ((43.72, -79.64), (43.86, -79.38)), ((43.72, -79.38), (43.86, -79.11))]

# Chain name in our list -> (what to search for, words a real branch's name must contain, note for the card)
CHAINS = {
    "Home Hardware": ("Home Hardware", ["home hardware", "home building centre"],
                      "Locally owned store; Home Hardware is a co-op owned by its dealers"),
    "Carpet One": ("Carpet One Floor & Home", ["carpet one"],
                   "Locally owned store; Carpet One is a co-op owned by its member stores"),
    "Co-operators": ("Co-operators insurance", ["co-operators", "cooperators"],
                     "Independent agent selling Co-operators insurance (a co-op insurer)"),
    "ClimateCare": ("ClimateCare heating and cooling", ["climatecare", "climate care"],
                    "Local contractor; ClimateCare is a co-op of independent contractors"),
}

GENERIC_WORDS = {"credit", "union", "coop", "co", "op", "operative", "cooperative", "inc", "the", "toronto",
                 "branch", "limited", "ltd", "of", "and", "services", "financial", "savings", "school",
                 "nursery", "centre", "center", "day", "care", "playschool", "office", "service", "group",
                 "insurance"}

OUT_FIELDS = ["name", "category", "address", "postal_code", "lat", "lng", "website", "phone", "hours",
              "google_name", "google_address", "google_maps_url", "google_place_id", "business_status",
              "match", "source", "reason", "chain", "card_note", "notes", "legal_name", "cmc_id", "last_checked"]
LEFT_FIELDS = ["name", "category", "address", "postal_code", "lat", "lng", "website", "source", "reason",
               "chain", "needs", "notes", "legal_name", "cmc_id"]

calls = 0


class OutOfCalls(Exception):
    pass


# ---------- Google ----------

def google_search(key, body):
    """One Text Search request. Uses the saved answer if we've asked this exact question before."""
    global calls
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / (hashlib.sha1(json.dumps(body, sort_keys=True).encode()).hexdigest() + ".json")
    if path.exists():
        return json.loads(path.read_text())
    if calls >= MAX_CALLS:
        raise OutOfCalls()
    for attempt in (1, 2):
        calls += 1
        try:
            r = requests.post(SEARCH_URL, json=body, timeout=30,
                              headers={"X-Goog-Api-Key": key, "X-Goog-FieldMask": FIELDS + ",nextPageToken"})
        except requests.RequestException as e:
            error(f"Couldn't reach Google (try {attempt}): {e}")
            time.sleep(3)
            continue
        log(f"Google request #{calls}: '{body.get('textQuery')}' -> status {r.status_code}, "
            f"{len(r.json().get('places', [])) if r.ok else 0} results")
        if r.ok:
            path.write_text(r.text)
            time.sleep(0.15)
            return r.json()
        msg = r.json().get("error", {}).get("message", "")[:200].replace(key, "[key]")
        error(f"Google said no (status {r.status_code}): {msg}")
        if r.status_code in (400, 401, 403):
            raise SystemExit("Stopping: Google rejected the key or request. See logs/run.log.")
        time.sleep(3)
    return {}


def distance_m(lat1, lng1, lat2, lng2):
    x = math.radians(lng2 - lng1) * math.cos(math.radians((lat1 + lat2) / 2))
    y = math.radians(lat2 - lat1)
    return 6371000 * math.hypot(x, y)


def words(name):
    n = name.lower().replace("co-op", "coop").replace("co-operative", "coop")
    return {w for w in re.findall(r"[a-z0-9']+", n) if w not in GENERIC_WORDS and len(w) > 1}


def in_toronto(address):
    return any(c in address for c in TORONTO_CITIES)


def pick_match(row, places, accept_any=False):
    """Choose the Google result that is really this co-op. Returns (place, match_label) or (None, why)."""
    our_words = words(row["name"]) | words(row.get("legal_name") or "")
    has_pos = bool(row.get("lat"))
    best = None
    for p in places:
        g_name = p.get("displayName", {}).get("text", "")
        if re.match(r"^\d", g_name):
            continue  # Google returned a bare street address, not a business
        name_ok = bool(our_words & words(g_name))
        dist = None
        if has_pos and p.get("location"):
            dist = distance_m(float(row["lat"]), float(row["lng"]), p["location"]["latitude"], p["location"]["longitude"])
        near = dist is not None and dist < 250
        if name_ok and (near or not has_pos):
            return p, "good"
        if name_ok and dist is not None and dist < 3000 and not best:
            best = (p, f"check: Google has it {int(dist)} m from the listed address (moved?)")
        if near and not name_ok and accept_any and not best:
            best = (p, "good (approved in review)")
    if best:
        return best
    return None, "no Google result matched the name and address"


# ---------- OpenStreetMap backup ----------

def osm_lookup(row):
    OSM_CACHE.mkdir(parents=True, exist_ok=True)
    q = f"{row['name']}, Toronto"
    path = OSM_CACHE / (hashlib.sha1(q.encode()).hexdigest() + ".json")
    if path.exists():
        return json.loads(path.read_text())
    try:
        r = requests.get("https://nominatim.openstreetmap.org/search", timeout=30,
                         params={"q": q, "format": "jsonv2", "limit": 1, "countrycodes": "ca"},
                         headers={"User-Agent": "toronto-coop-map/1.0 (personal portfolio project)"})
        time.sleep(1.1)  # OpenStreetMap allows 1 request per second
        log(f"OpenStreetMap lookup '{q}' -> status {r.status_code}, {len(r.json()) if r.ok else 0} results")
        result = r.json() if r.ok else []
    except requests.RequestException as e:
        error(f"Couldn't reach OpenStreetMap: {e}")
        return []
    path.write_text(json.dumps(result))
    return result


# ---------- building rows ----------

def with_google(row, p, match):
    loc = p.get("location", {})
    out = dict(row)
    out.update(
        google_name=p.get("displayName", {}).get("text", ""),
        google_address=p.get("formattedAddress", ""),
        google_maps_url=p.get("googleMapsUri", ""),
        google_place_id=p.get("id", ""),
        business_status=p.get("businessStatus", ""),
        phone=p.get("nationalPhoneNumber", ""),
        hours=" | ".join(p.get("regularOpeningHours", {}).get("weekdayDescriptions", [])),
        website=row.get("website") or p.get("websiteUri", ""),
        match=match,
        last_checked=date.today().isoformat(),
    )
    if match == "good" or not row.get("lat"):
        out["lat"], out["lng"] = loc.get("latitude", row.get("lat")), loc.get("longitude", row.get("lng"))
    if not out.get("address"):
        out["address"] = p.get("formattedAddress", "").split(", Toronto")[0]
    return out


def check_location(key, row, overrides):
    query = f"{row['name']}, {row['address']}, Toronto, ON" if row.get("address") else f"{row['name']}, Toronto, ON"
    body = {"textQuery": query, "pageSize": 5}
    if row.get("lat"):
        body["locationBias"] = {"circle": {"center": {"latitude": float(row["lat"]), "longitude": float(row["lng"])},
                                           "radius": 500.0}}
    places = google_search(key, body).get("places", [])
    p, match = pick_match(row, places, accept_any=row["name"] in overrides)
    if p:
        return with_google(row, p, match), None
    log(f"No Google match for {row['name']} ({match}); trying OpenStreetMap", "WARN")
    osm = osm_lookup(row)
    if osm:
        o = osm[0]
        out = dict(row, match="OpenStreetMap only (not on Google)", last_checked=date.today().isoformat())
        if not out.get("lat"):
            out["lat"], out["lng"] = o["lat"], o["lon"]
        return out, None
    return None, "Not found on Google or OpenStreetMap"


def find_chain_branches(key, row):
    query, must, card_note = CHAINS[row["name"]]
    found = {}
    for (lo_lat, lo_lng), (hi_lat, hi_lng) in TORONTO_BOXES:
        body = {"textQuery": query, "pageSize": 20, "locationRestriction": {"rectangle": {
            "low": {"latitude": lo_lat, "longitude": lo_lng}, "high": {"latitude": hi_lat, "longitude": hi_lng}}}}
        for _page in range(3):
            res = google_search(key, body)
            for p in res.get("places", []):
                g_name = p.get("displayName", {}).get("text", "")
                if any(m in g_name.lower() for m in must) and in_toronto(p.get("formattedAddress", "")):
                    found[p["id"]] = p
            if not res.get("nextPageToken"):
                break
            body = {**body, "pageToken": res["nextPageToken"]}
    # Agents sharing one office stay as separate rows; the website groups them into one pin.
    branches = []
    for p in found.values():
        street = p.get("formattedAddress", "").split(",")[0]
        if not re.match(r"^\d", street):
            log(f"Skipped {p['displayName']['text']}: no street address (not a walk-in branch)")
            continue
        b = dict(row, name=p["displayName"]["text"], address="", lat="", lng="", website="", source="Google (chain branch)",
                 notes="", card_note=card_note)
        branches.append(with_google(b, p, "good"))
    log(f"{row['name']}: found {len(branches)} Toronto branches on Google")
    return branches


# ---------- main ----------

def main():
    key = (dotenv_values(ROOT / ".env").get("GOOGLE_PLACES_API_KEY") or "").strip()
    if not key:
        error("No GOOGLE_PLACES_API_KEY in .env")
        sys.exit(1)
    log(f"Run started: Google check (milestone 3), max {MAX_CALLS} paid requests")
    rows = list(csv.DictReader((BUILD / "coops.csv").open()))
    left_off = list(csv.DictReader((BUILD / "left_off.csv").open()))
    checked, seen_ids = [], {}
    overrides = {r["name"]: r for r in csv.DictReader((ROOT / "data" / "seed" / "review_overrides.csv").open())}

    try:
        for row in rows:
            if row["chain"] == "yes" and row["name"] in CHAINS:
                for b in find_chain_branches(key, row):
                    if b["google_place_id"] not in seen_ids:
                        seen_ids[b["google_place_id"]] = b["name"]
                        checked.append(b)
                continue
            out, why = check_location(key, row, overrides)
            if out and row["name"] in overrides and overrides[row["name"]]["note"]:
                out["notes"] = ((out.get("notes") or "") + "; " + overrides[row["name"]]["note"]).strip("; ")
            if not out:
                left_off.append({**row, "reason": why})
                log(f"Left off: {row['name']} - {why}")
                continue
            pid = out.get("google_place_id")
            if out.get("business_status") == "CLOSED_PERMANENTLY":
                left_off.append({**row, "reason": "Permanently closed (Google)"})
                log(f"Left off: {row['name']} - permanently closed")
                continue
            if pid and pid in seen_ids:
                log(f"Duplicate: {row['name']} is the same Google place as {seen_ids[pid]}; keeping one pin", "WARN")
                continue
            if pid:
                seen_ids[pid] = out["name"]
            if out.get("business_status") == "CLOSED_TEMPORARILY":
                out["notes"] = ((out.get("notes") or "") + "; temporarily closed on Google").strip("; ")
            checked.append(out)
            log(f"Checked: {out['name']} -> {out.get('google_name') or '(OSM)'} [{out['match']}]")
    except OutOfCalls:
        error(f"Stopped early: hit the {MAX_CALLS}-request safety limit. Re-run to continue (saved answers are free).")

    checked.sort(key=lambda r: (r["category"], r["name"]))
    for path, data, fields in ((BUILD / "coops_checked.csv", checked, OUT_FIELDS),
                               (BUILD / "left_off_checked.csv", left_off, LEFT_FIELDS)):
        with path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            w.writerows(data)
    to_check = sum(1 for r in checked if r["match"] != "good")
    log(f"Result: {len(checked)} locations ({to_check} flagged for review), {len(left_off)} left off. "
        f"Paid Google requests this run: {calls}")
    log("Run finished")


if __name__ == "__main__":
    main()

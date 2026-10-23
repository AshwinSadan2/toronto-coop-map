"""Milestone 2: combine all sources into one list of Toronto co-op locations.

Sources:
  1. OCA PDF        -> data/seed/oca_2026.csv (hand-checked)
  2. CMC national map (crm.canada.coop) -> every co-op in Canada with address + map position
  3. Canadian Worker Co-op Federation member table (public Airtable view)

Writes:
  data/build/coops.csv     one row per location we keep
  data/build/left_off.csv  everything we left off, with the reason

Run:  .venv/bin/python builder/pull_sources.py [--refresh]
      --refresh re-downloads the sources instead of using the saved copies.
"""
import csv
import json
import re
import sys
from pathlib import Path

import requests

from log import error, log

ROOT = Path(__file__).resolve().parent.parent
LOCAL = ROOT / "data" / "local"
BUILD = ROOT / "data" / "build"
SEED = ROOT / "data" / "seed"

TORONTO_CITIES = {"toronto", "north york", "scarborough", "etobicoke", "york", "east york"}
BROWSER = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/130 Safari/537.36"

CMC_URL = "https://crm.canada.coop/en/civicrm/ajax/api4/SearchDisplay/run"
CMC_PARAMS = {"return": "page:1", "savedSearch": "CMC_Coop_Map", "display": "CMC_Coop_Map",
              "afform": "afsearchCoOperationAcrossCanada", "filters": {}}
CWCF_BASE = "apppKPSbingFkdA06"
CWCF_VIEW = "shr6PROGWEd2uNpKt"

# PDF categories -> the categories shown on the site
SITE_CATEGORY = {"Financial & Insurance": "Insurance", "Retail": "Shops", "Food & Grocery": "Grocery & Food",
                 "Healthcare": "Health & Wellness", "Accommodations": "Places to Stay"}
PDF_CATEGORY = {"Home Hardware": "Home & Hardware", "Carpet One": "Home & Hardware",
                "ClimateCare": "Home & Hardware", "Co-op Cabs": "Getting Around"}

OUT_FIELDS = ["name", "category", "address", "postal_code", "lat", "lng", "website",
              "source", "reason", "chain", "needs", "notes", "legal_name", "cmc_id"]


# ---------- downloading ----------

def fetch_cmc(refresh):
    path = LOCAL / "cmc_all.json"
    if refresh or not path.exists():
        log(f"Downloading national co-op map from {CMC_URL}")
        r = requests.post(CMC_URL, data={"params": json.dumps(CMC_PARAMS)},
                          headers={"User-Agent": BROWSER, "X-Requested-With": "XMLHttpRequest"}, timeout=120)
        log(f"National co-op map responded: status {r.status_code}, {len(r.content) // 1024} KB")
        r.raise_for_status()
        path.write_bytes(r.content)
    else:
        log(f"Using saved copy of national co-op map ({path.name})")
    return [v["data"] for v in json.loads(path.read_text())["values"]]


def fetch_cwcf(refresh):
    path = LOCAL / "cwcf_a.json"
    if refresh or not path.exists():
        embed = f"https://airtable.com/embed/{CWCF_BASE}/{CWCF_VIEW}"
        log(f"Downloading Worker Co-op Federation table from {embed}")
        s = requests.Session()
        s.headers["User-Agent"] = BROWSER
        page = s.get(embed, timeout=60)
        log(f"Worker Co-op page responded: status {page.status_code}")
        url = json.loads(re.search(r'urlWithParams:\s*("[^"]+")', page.text).group(1))
        r = s.get("https://airtable.com" + url, timeout=60, headers={
            "x-airtable-application-id": CWCF_BASE, "x-requested-with": "XMLHttpRequest",
            "x-time-zone": "America/Toronto", "x-user-locale": "en"})
        log(f"Worker Co-op table responded: status {r.status_code}")
        r.raise_for_status()
        path.write_bytes(r.content)
    else:
        log(f"Using saved copy of Worker Co-op table ({path.name})")
    table = json.loads(path.read_text())["data"]["table"]
    names = {c["id"]: c["name"].strip() for c in table["columns"]}
    return [{names[k]: v for k, v in row["cellValuesByColumnId"].items()} for row in table["rows"]]


# ---------- helpers ----------

def norm(name):
    """Loose name for matching duplicates across sources."""
    n = name.lower().replace("co-operative", "coop").replace("cooperative", "coop").replace("co-op", "coop").replace("bicycle", "bike")
    n = re.sub(r"\b(inc|incorporated|ltd|limited|corp|corporation|the|worker|of|and)\b", " ", n)
    return re.sub(r"[^a-z0-9]", "", n)


def clean_name(legal):
    n = re.sub(r",?\s+(Inc\.?|Incorporated|Limited|Ltd\.?|Corporation|Corp\.?)(?=\s|$|-)", "", legal)
    n = n.replace(" - Toronto - ", " - ").replace("(The) ", "")
    return re.sub(r"\s+", " ", n).strip(" -")


def cmc_categories(d):
    return re.findall(r"<div>([^<]*)</div>", d.get("overview") or "")


def default_leave_off(d):
    cats = " ".join(cmc_categories(d))
    if d.get("icon") == "fa-house" or "Co-op Housing" in cats or "Accommodation" in cats:
        return "Housing co-op (out of scope for now)"
    if not (d.get("street_address") or "").strip() or "placeholder" in (d.get("street_address") or ""):
        return "No address listed"
    return "Niche (not a walk-in business for everyday shoppers)"


def write(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=OUT_FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


# ---------- main ----------

def main():
    refresh = "--refresh" in sys.argv
    log("Run started: combine sources (milestone 2)")
    LOCAL.mkdir(parents=True, exist_ok=True)

    pdf = list(csv.DictReader((SEED / "oca_2026.csv").open()))
    decisions = {r["cmc_id"]: r for r in csv.DictReader((SEED / "cmc_decisions.csv").open())}
    log(f"Source 1 (PDF): {len(pdf)} Toronto-area co-ops")

    try:
        cmc_all = fetch_cmc(refresh)
    except Exception as e:
        error(f"Couldn't get the national co-op map: {e}")
        raise
    cmc = [d for d in cmc_all if (d.get("city") or "").strip().lower() in TORONTO_CITIES]
    log(f"Source 2 (national map): {len(cmc)} Toronto co-ops out of {len(cmc_all)} in Canada")

    kept, left_off, used_pdf = [], [], set()

    for d in cmc:
        legal = d["display_name"].strip()
        dec = decisions.get(str(d["id"]))
        row = {"legal_name": legal, "cmc_id": d["id"], "source": "CMC map",
               "address": (d.get("street_address") or "").strip(), "postal_code": d.get("postal_code") or "",
               "lat": d.get("geo_code_1") or "", "lng": d.get("geo_code_2") or "",
               "website": (d.get("website") or [""])[0] or ""}
        if dec and dec["decision"] == "keep":
            pdf_row = next((p for p in pdf if p["name"] == dec["pdf_name"]), None)
            is_chain = pdf_row is not None and pdf_row["chain"] == "yes"
            name = dec.get("display_name") or (pdf_row["name"] if pdf_row and not is_chain else clean_name(legal))
            if pdf_row:
                used_pdf.add(pdf_row["name"])
                row["source"] = "PDF + CMC map"
                row["website"] = row["website"] or pdf_row["website"]
            row.update(name=name, category=dec["category"], reason=dec["reason"],
                       chain="yes" if is_chain else "no", notes=dec["notes"],
                       needs="" if row["lat"] else "map position")
            kept.append(row)
            log(f"Kept: {name} ({row['address']}) - {dec['reason']}")
        else:
            reason = dec["reason"] if dec else default_leave_off(d)
            row.update(name=clean_name(legal), reason=reason)
            left_off.append(row)
            log(f"Left off: {row['name']} - {reason}")

    # Hand-entered locations (from the co-ops' own websites)
    for m in csv.DictReader((SEED / "manual_additions.csv").open()):
        if m["pdf_name"]:
            used_pdf.add(m["pdf_name"])
        kept.append({**m, "source": "Co-op website", "chain": "no", "needs": "map position",
                     "notes": (m["notes"] + "; " if m["notes"] else "") + "found at " + m["found_at"]})
        log(f"Kept (hand-entered): {m['name']} ({m['address']})")

    # PDF co-ops the map didn't cover
    for p in pdf:
        if p["name"] in used_pdf:
            if p["chain"] == "no":
                continue
            if p["name"] in ("Credit Unions", "Desjardins"):
                log(f"PDF entry '{p['name']}' covered by branches from the national map")
                continue
        if p["status"] == "keep":
            category = PDF_CATEGORY.get(p["name"]) or SITE_CATEGORY.get(p["category"], p["category"])
            row = {"name": p["name"], "category": category, "website": p["website"], "source": "PDF",
                   "reason": p["reason"], "chain": p["chain"], "notes": p["notes"],
                   "needs": "list of Toronto branches" if p["chain"] == "yes" else "address + map position"}
            kept.append(row)
            log(f"Kept from PDF only (needs {row['needs']}): {p['name']}")
        else:
            left_off.append({"name": p["name"], "website": p["website"], "source": "PDF",
                             "reason": p["leave_off_reason"]})

    # Source 3: Worker Co-op Federation - check for anything new
    try:
        cwcf = fetch_cwcf(refresh)
        toronto = [r for r in cwcf if "toronto" in str(r.get("City", "")).lower()]
        known = {norm(r[k]) for r in kept + left_off for k in ("name", "legal_name") if r.get(k)}
        def is_known(name):
            n = norm(name)
            return any(n in k or k in n for k in known)
        new = [r for r in toronto if not is_known(r["Name of Organization/Co-op"])]
        log(f"Source 3 (Worker Co-op Federation): {len(toronto)} Toronto co-ops, {len(new)} not already in our list")
        for r in new:
            log(f"New from Worker Co-op Federation, needs review: {r['Name of Organization/Co-op'].strip()}", "WARN")
    except Exception as e:
        error(f"Couldn't get the Worker Co-op Federation table (skipping it this run): {e}")

    kept.sort(key=lambda r: (r["category"], r["name"]))
    write(BUILD / "coops.csv", kept)
    write(BUILD / "left_off.csv", left_off)
    with_pin = sum(1 for r in kept if r.get("lat"))
    log(f"Result: {len(kept)} locations kept ({with_pin} already have a map position), {len(left_off)} left off")
    log("Run finished")


if __name__ == "__main__":
    main()

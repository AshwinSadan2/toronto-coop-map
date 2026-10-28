# Toronto Co-op Map — build rules

**At the start of every session, read `handoff.md` first.** History: `sessions/`, choices made: `decisions.md`.

The spec is `plan.md` (diagram: `diagram.html`). The design interview is finished; its instructions are kept in `docs/` for reference only.

## Folders
- `sources/` — original source files (the OCA PDF)
- `data/seed/` — hand-checked lists (committed): PDF list, keep/leave-off decision per national-map co-op, hand-entered locations
- `data/build/` — combined output: `coops.csv` (kept) and `left_off.csv` (with reasons)
- `data/local/` — downloaded source copies (not committed)
- `builder/` — Python scripts that build the list (run with `.venv/bin/python`)
- `logs/run.log` — plain-English log of every run (not committed)
- `site/` — the public website (static: index.html, styles.css, app.js, data/coops.json)

## Rules from the plan
- Toronto only. Everyday-shopper co-ops only; every left-off co-op keeps a reason.
- Every builder step logs to `logs/run.log` via `builder/log.py`.
- Never overwrite existing Notion rows; preview + "yes" before any Notion write.
- Google is used only at build time, never on the public site.
- Publish stops if the co-op count drops more than ~10%.
- Keys live in `.env` (never committed, never printed).
- Notion is the source of truth now. Update the site with `builder/publish.py`, never `export_site.py` (that rebuilds from the CSV and would wipe Notion edits).
- Mistake: Claude's chat Notion connector is in the **Northern Loop** workspace; the project's own connection ("Co Op Map") is in **Ashwin's Notion**. Never create project pages with the chat connector; make them through the script's key.

## Milestones
1. [x] Project setup + starting list from the PDF
2. [x] Add co-ops from extra sources + chain branches (`builder/pull_sources.py`)
3. [x] Google check: hours, phone, open/closed, chain branches (`builder/lookup_google.py` -> `data/build/coops_checked.csv`). Approve odd matches in `data/seed/review_overrides.csv`
4. [x] Notion database + preview/approve write (`builder/notion_sync.py`; `--preview` writes nothing). Database "Co-op list" inside the one page the connection "Co Op Map" can see (workspace: Ashwin's Notion). Untick "Show on site" to hide a co-op
5. [x] Website in `site/` (map, search, filters, street-sign cards). Data: `builder/publish.py` (Notion -> `site/data/coops.json`). Preview: `cd site && python3 -m http.server 8765`
6. [~] Publish step done (`builder/publish.py`). Hosting not yet: Vercel (free Hobby, team `ashwinsadananthan-1850`) needs the user to connect GitHub under Login Connections; then create project from repo `AshwinSadan2/toronto-coop-map`, root directory `site`

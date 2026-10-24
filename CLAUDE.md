# Toronto Co-op Map — build rules

The spec is `plan.md` (diagram: `diagram.html`). The design interview is finished; its instructions are kept in `docs/` for reference only.

## Folders
- `sources/` — original source files (the OCA PDF)
- `data/seed/` — hand-checked lists (committed): PDF list, keep/leave-off decision per national-map co-op, hand-entered locations
- `data/build/` — combined output: `coops.csv` (kept) and `left_off.csv` (with reasons)
- `data/local/` — downloaded source copies (not committed)
- `builder/` — Python scripts that build the list (run with `.venv/bin/python`)
- `logs/run.log` — plain-English log of every run (not committed)
- `site/` — the public website (to come)

## Rules from the plan
- Toronto only. Everyday-shopper co-ops only; every left-off co-op keeps a reason.
- Every builder step logs to `logs/run.log` via `builder/log.py`.
- Never overwrite existing Notion rows; preview + "yes" before any Notion write.
- Google is used only at build time, never on the public site.
- Publish stops if the co-op count drops more than ~10%.
- Keys live in `.env` (never committed, never printed).

## Milestones
1. [x] Project setup + starting list from the PDF
2. [x] Add co-ops from extra sources + chain branches (`builder/pull_sources.py`)
3. [x] Google check: hours, phone, open/closed, chain branches (`builder/lookup_google.py` -> `data/build/coops_checked.csv`). Approve odd matches in `data/seed/review_overrides.csv`
4. [ ] Notion database + preview/approve write
5. [ ] Website (map, search, cards)
6. [ ] Publish step + free hosting link

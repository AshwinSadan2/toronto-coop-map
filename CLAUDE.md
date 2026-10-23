# Toronto Co-op Map — build rules

The spec is `plan.md` (diagram: `diagram.html`). The design interview is finished; its instructions are kept in `docs/` for reference only.

## Folders
- `sources/` — original source files (the OCA PDF)
- `data/seed/` — hand-checked starting lists (committed)
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
2. [ ] Add co-ops from extra sources + expand chains into branches
3. [ ] Look up addresses/hours (Google, OpenStreetMap fallback)
4. [ ] Notion database + preview/approve write
5. [ ] Website (map, search, cards)
6. [ ] Publish step + free hosting link

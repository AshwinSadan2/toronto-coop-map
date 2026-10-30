# Handoff

## Where we are
The co-op list (131 Toronto locations) is in Notion and on the website, which runs locally (`cd site && python3 -m http.server 8765`).
The site is live at https://toronto-coop-map.vercel.app (Vercel account `ash-4456`). Update it with `builder/publish.py`, then `sh builder/deploy.sh`.

## Last session did
- 2026-10-26: wrote all 131 co-ops into the Notion "Co-op list" database (`builder/notion_sync.py`).
- 2026-10-26: built `builder/publish.py`; output matches the old site data exactly.
- 2026-10-26: deleted the stray Notion page in the Northern Loop workspace.
- 2026-10-28: Come As You Are moved to 464 College St in Notion (pin + neighbourhood).
- 2026-10-28: deployed the site from the Mac with a Vercel token (account `ash-4456`); all 131 co-ops live.

## Next session does
1. Go through the open questions below with the user, fix them in Notion, publish, then deploy.

## Waiting on
- **User decisions:**
  - Finnish Credit Union vs "OP Credit Union".
  - Show the 15 childcare co-ops or not (plan.md says 19; check the real number).
  - Google's storage terms for hours and phone numbers.

*Last updated: 2026-10-28*

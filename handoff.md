# Handoff

## Where we are
The co-op list (131 Toronto locations) is in Notion and on the website, which runs locally (`cd site && python3 -m http.server 8765`).
The publish step (Notion → website) works. The only thing left is putting the site online with Vercel.

## Last session did
- 2026-10-26: wrote all 131 co-ops into the Notion "Co-op list" database (`builder/notion_sync.py`).
- 2026-10-26: built `builder/publish.py`; output matches the old site data exactly.
- 2026-10-26: deleted the stray Notion page in the Northern Loop workspace.
- 2026-10-27: Vercel project creation blocked: "You need to add a Login Connection to your GitHub account first."

## Next session does
1. Ask the user if GitHub is connected in Vercel (vercel.com/account/settings/authentication → Login Connections → GitHub).
2. Create the Vercel project: repo `AshwinSadan2/toronto-coop-map`, root `site`, team `team_ZuApN0d7AmJPNjJ9xReaOEti`. Share the public link.
3. Tick milestone 6 in CLAUDE.md.
4. Go through the open questions below with the user and fix them in Notion, then publish.

## Waiting on
- **User:** connect GitHub in Vercel.
- **User decisions:**
  - Come As You Are's new address (likely 464 College St).
  - Finnish Credit Union vs "OP Credit Union".
  - Show the 15 childcare co-ops or not.
  - Google's storage terms for hours and phone numbers.

*Last updated: 2026-10-27*

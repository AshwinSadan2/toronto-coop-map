# Handoff

## Where we are
The site is live at https://toronto-coop-map.vercel.app with all 131 Toronto co-ops (Vercel account `ash-4456`). Notion's "Co-op list" is the source of truth.
The GitHub repo is public. Only a few data questions are left.

## Last session did
- 2026-10-28: moved Come As You Are to 464 College St in Notion (pin + neighbourhood) and republished.
- 2026-10-28: put the site online from the Mac with a Vercel token.
- 2026-10-29: added a round "locate me" button on the map.
- 2026-10-30: fixed a "Blocked" deploy by uploading a git-free copy; saved it as `builder/deploy.sh` (not yet run as a script).
- 2026-11-06: made the repo public; the OCA PDF and `data/build/coops_checked.csv` are now local only.

## Next session does
1. Ask the user the three open questions below.
2. Fix the answers in Notion (through the project's key, never the chat connector).
3. Run `builder/publish.py`, then ask "deploy?" and run `sh builder/deploy.sh`. Check the public link.

## Waiting on
- **User decisions:**
  - Finnish Credit Union vs "OP Credit Union": which name on the site?
  - Show the 15 childcare co-ops or not?
  - Google's storage rules for hours and phone numbers.

*Last updated: 2026-11-06*

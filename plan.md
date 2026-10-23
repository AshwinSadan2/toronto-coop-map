# Toronto Co-op Map

> This spec is designed to be used as context for a new Claude Code session. Drop it in a project folder and begin building from here.

## Outcome
A public website where everyday shoppers can explore co-operative businesses in Toronto on a map. A visitor opens the site and sees a search bar and a map. If they share their location, the map zooms to co-ops near them; if not, it shows all of Toronto. They can search by type of business ("grocery"), neighbourhood ("Leslieville"), address, or a specific co-op's name ("Karma Co-op"). Clicking a pin opens a Google Maps-style card (name, category, address, hours, website, phone) with a "Get directions" link that opens Google Maps. Only co-ops an everyday person can walk into, buy from, or book are shown — niche business-to-business co-ops are left off. This is the owner's own project; "done" means a live, polished portfolio piece.

Behind the site sits a **one-time list builder** that assembles the co-op list, plus a **publish step** that pushes the reviewed list to the website.

## Success Signal
A live, polished link the owner is proud to share in their portfolio:
- **Must have:** Accurate (every pin is a real, currently open co-op with correct info)
- **Must have:** Looks good (clean design, not a default template)
- **Must have:** Complete (the full reviewed list, aiming for 50–100+ locations)
- **Nice to have:** Works on phones — desktop website comes first
- **Lowest priority:** Fast map load

## Inputs
- **Source 1 — base list:** *Choose Co-operative! 2026* PDF from the Ontario Co-operative Association — from `~/Documents/Toronto CooP Map/` — freshness: one-time. ~120 Ontario co-ops, ~29 in Toronto, ~10 everyday-shopper. Has name, category, description, city, and website links (embedded in the names). **No street addresses.**
- **Source 2 — extra co-ops:** Co-operatives & Mutuals Canada national co-op map (crm.canada.coop/map) — freshness: one-time. Likely the largest extra source; it's an interactive map, so pulling data out may take some work.
- **Source 3 — extra co-ops:** Canadian Worker Co-op Federation member profiles (canadianworker.coop) — freshness: one-time. Good for worker-owned cafés, bike shops, etc.
- **Source 4 — details:** Google place lookups, done **once** at build time — address, map position, hours, phone, website, "permanently closed" status. Stays within Google's free monthly allowance, with a $0 spending cap.
- **Source 5 — fallback details:** OpenStreetMap — fills gaps where Google has nothing.
- **Approach:** use the easiest sources first; stop once the list reaches 50–100+ locations.

**When data is missing or wrong:**
| Situation | Handling |
|---|---|
| Online-only (no physical location) | Leave off the map |
| Can't be found on Google / OpenStreetMap | Leave off the map |
| Permanently closed | Leave off the map |
| Missing hours or photos | Show anyway with what we have |

Every co-op left off goes into a **"left off" list** with its reason, so nothing disappears silently and the owner can rescue one by hand.

## Logic
- **Trigger:**
  - *List builder:* the owner runs it by hand (one time, re-runnable later).
  - *Publish:* the owner runs one "publish" command after editing in Notion.
  - *Website:* a visitor opens the page.
- **Decision points:**
  1. **Everyday or niche?** Everyday = a regular person can walk in, buy, or book (grocery, cafés, shops, bike repair, galleries, cinemas, taxis, credit unions/banks, insurance offices). Niche = sells mainly to other businesses (consultants, wholesalers, buying groups, farm suppliers, energy developers, staffing). The system labels each co-op with a one-line reason.
  2. **Is it a real, open, physical location?** If not → "left off" list.
  3. **Is it a duplicate?** Same co-op in two sources → one pin.
  4. **(Website) Did the visitor share their location?** Yes → zoom to nearby co-ops. No → show all of Toronto.
- **Rules:**
  - Toronto only.
  - **Every chain branch gets its own pin** (Home Hardware, credit unions, insurance offices, Carpet One, etc.).
  - No duplicate pins.
  - The list builder **never overwrites existing Notion rows** — it only adds new ones, so the owner's hand edits are safe.
  - Each row records what Google matched (name + address) next to the original name, and a "last checked" date.
  - Publish stops and asks if the co-op count drops by more than ~10% versus the live site.
- **Human-in-the-loop:**
  - **Before writing to Notion:** preview ("Adding 87 co-ops, 0 changes") → owner types "yes."
  - **After writing to Notion:** ~10-minute review of everyday/niche sorting and Google matches; owner fixes mistakes by hand.
  - **Before publishing a big drop:** if the count fell by more than ~10%, owner must approve before it goes live.

## Output
- **Produces:**
  - 🗺️ The website: OpenStreetMap-based map + search bar + Google Maps-style co-op cards + "Get directions" link to Google Maps.
  - 📋 The clean co-op list (one row per location) in Notion.
  - 🚫 The "left off" list with reasons.
- **Consumer:** everyday shoppers and portfolio viewers (website); the owner (Notion list and left-off list).
- **Storage:** a Notion database is the source of truth for the co-op list. The website uses a published copy, so it never depends on Notion being up.
- **Hosting:** a free public link (e.g. `toronto-coops.vercel.app`). A custom domain can come later.

## Version Control
- **Repo:** GitHub (private by default)
- **`.gitignore` must exclude:** `.env`, API keys, `logs/`, local data files, any secrets
- **Commit cadence:** at least one commit per working milestone; push regularly
- **Why:** one rollback-able safety net is worth more than any other guardrail in early builds
- **Bonus:** the free hosting link can connect to the GitHub repo, so publishing a new version can be as simple as pushing a commit.

## Logging (Phase 1 Guardrail)
- **Log location:** `logs/run.log` at project root
- **What gets logged:** run start/end; every co-op processed and which source it came from; what Google/OpenStreetMap returned; each everyday/niche decision and its reason; every co-op left off and why; every Notion write (with count); every publish (with old vs new count); every error with context (e.g. "Couldn't reach Google," "No match for Karma Co-op")
- **Format:** human-readable lines so a non-technical user can open the file and understand what happened
- **Why:** in version one, this is the single best tool for debugging when something goes wrong

## High-Stakes Actions & Approval Gates
- **Action:** Writing 50–100+ co-op rows into Notion (bulk operation)
  - **Why it's high-stakes:** a bad run could flood the database or overwrite hand-fixed rows
  - **Approval gate:** preview table showing exactly what will be added; owner types "yes" to proceed. The builder never overwrites existing rows.
- **Action:** Publishing the list to the live public website
  - **Why it's high-stakes:** it's public — a broken or empty list goes straight to the portfolio
  - **Approval gate:** automatic count check; if the count dropped by more than ~10%, publishing stops until the owner approves
- **Action:** Using a Google account that can bill for usage
  - **Why it's high-stakes:** charges can't be undone
  - **Approval gate:** Google is used only at build time (never on the public website); monthly spending cap set to $0

## System Edges
- **Edge 1 — Surprise Google bills / stolen key:** the public map uses OpenStreetMap (no key on the site); Google is used once at build time under a $0 cap.
- **Edge 2 — Wrong match** (e.g. "Karma Co-op" matches a yoga studio): each row shows what Google matched next to the original; caught in the 10-minute review.
- **Edge 3 — Re-running the builder wipes hand edits:** builder only adds new rows, never overwrites; preview + "yes" before any Notion write.
- **Edge 4 — Publishing a broken list:** publish stops and asks if the count drops by more than ~10%.
- **Edge 5 — Stale info:** each row has a "last checked" date; re-check every ~6 months.

## System Diagram
See `diagram.html` for the visual flow.

## Suggested Tech Stack (High-Level)
- **A PDF reader** to pull names, categories and website links from the base list
- **A small data-gathering script** to collect co-ops from the extra sources
- **A place lookup service** (Google, once) plus OpenStreetMap as fallback
- **An AI step** to sort everyday vs niche with a one-line reason
- **A Notion database** for the co-op list (needs its own Notion key in `.env` — Claude's chat connection to Notion won't work for a standalone script)
- **A "publish" script** that copies the reviewed Notion list into the website
- **A web map** built on OpenStreetMap, with a search bar and pop-up cards
- **Free website hosting** connected to GitHub (e.g. Vercel, already connected to this account)
- **Keys needed in `.env`:** Notion, Google (place lookups), and an AI provider for sorting

## Open Questions
- **Chains may dominate the map.** With every branch included, the count may go well past 100 and chain pins may bury local gems like Karma Co-op and The Big Carrot. Revisit after seeing the map; a "hide chains" filter is an easy fix.
- **Google storage rules.** Google limits how long some of its details (especially photos and ratings) can be stored in your own database. Check the current terms during the build; worst case, photos/ratings become a "See on Google Maps" link.
- **Co-operatives & Mutuals Canada map:** confirm the data can actually be pulled out; if not, fall back to the OCA member directory and Google Maps searches.
- **Search by neighbourhood:** decide whether neighbourhoods come from addresses automatically or are tagged by hand.
- **Housing co-ops:** left out for now (not shops); could become an optional map layer later.
- **Mobile:** nice-to-have for Phase 1; confirm how much phone polish is wanted before sharing the link.
- **Custom domain:** start on the free link; add a domain (~$15–20/year) later if wanted.

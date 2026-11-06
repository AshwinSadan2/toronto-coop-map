# Decisions

## 2026-10-23: One pin per office; every agent at a shared address is listed on its card
- Why: several Co-operators agents share one office. Merging them into one row hid four real agents.
- What we didn't pick: one row per address (hides people), or a pin per agent (pins stacked on top of each other).

## 2026-10-23: Keep chain branches (Co-operators, Home Hardware, Carpet One, ClimateCare) with a card note
- Why: they are locally owned members of a co-op. The note explains this to shoppers.
- What we didn't pick: leaving them off. That would drop about 50 useful everyday places.

## 2026-10-23: Use Google Places only while building the list, cached, capped at 400 calls
- Why: it stays inside the free tier, and the public site never depends on Google or a key.
- What we didn't pick: live Google lookups on the site (costs money and exposes a key).

## 2026-10-24: Map tiles from OpenStreetMap with a muted colour filter
- Why: free and needs no key.
- What we didn't pick: CARTO tiles, which now need an API key.

## 2026-10-26: Notion database lives in the "Ashwin's Notion" workspace; Northern Loop copy deleted
- Why: the project's connection "Co Op Map" belongs to Ashwin's Notion.
- What we didn't pick: keeping it in Northern Loop, which would have needed a second connection and key.

## 2026-10-26: Hide a co-op by unticking "Show on site" in Notion
- Why: keeps the row and its history; publish leaves it off the site.
- What we didn't pick: deleting rows (the builder would add them back on its next run).

## 2026-10-26: Host on Vercel (free plan), building from GitHub with `site/` as the root (replaced 2026-10-28, see below)
- Why: free, and updates go live automatically on each push.
- What we didn't pick: uploading files by hand (each update is manual), or GitHub Pages (works, but the plan chose Vercel).

## 2026-10-28: Come As You Are moved to Google's address (464 College St)
- Why: Google showed it 483 m from the old listing (254 Augusta Ave) and still open; the user confirmed.
- What we didn't pick: keeping the old address from the national co-op map, which looks out of date.

## 2026-10-28: Host on Vercel account `ash-4456`, deployed from the Mac with a token (`builder/deploy.sh`)
- Why: building from GitHub was blocked (no GitHub login connection in Vercel), and the token the user made belongs to `ash-4456`. Deploy uploads a git-free copy because Vercel blocks unknown commit authors.
- What we didn't pick: the `ashwinsadananthan-1850` account (would need a new token; recommended for one-place tidiness, user chose speed), or building from GitHub (pushes would auto-update, but the login connection wasn't set up).

## 2026-10-29: Add a round locate button in the map corner, keep "Near me"
- Why: people look for the crosshair on the map itself, like Google Maps.
- What we didn't pick: moving "Near me" out of the search bar (it's still useful next to search).

## 2026-11-06: Repo made public; OCA PDF and Google data file kept local only
- Why: portfolio piece. A history scan found no keys. The OCA booklet is not ours to share, and Google limits storing and re-sharing Places data (`data/build/coops_checked.csv`).
- What we didn't pick: rewriting history to remove older copies (low risk: the booklet is free and the same details are on the live site).

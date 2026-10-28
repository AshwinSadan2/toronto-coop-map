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

## 2026-10-26: Host on Vercel (free plan), building from GitHub with `site/` as the root
- Why: free, and updates go live automatically on each push.
- What we didn't pick: uploading files by hand (each update is manual), or GitHub Pages (works, but the plan chose Vercel).

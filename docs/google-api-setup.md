# Google API Key Setup (Places API)

Used once at build time to look up addresses, hours, phone numbers, open/closed status, and chain branches (Home Hardware, Carpet One, Co-operators, ClimateCare). The key **never goes on the public website**.

## 1. Turn on the Places API
1. Go to [console.cloud.google.com](https://console.cloud.google.com) and pick (or create) a project
2. **APIs & Services → Library**
3. Search **Places API (New)** → click **Enable**

## 2. Create the key
1. **APIs & Services → Credentials → + Create credentials → API key**
2. Click the new key to edit its settings

## 3. Restrict the key

| Setting | Choose | Why |
|---|---|---|
| **Application restrictions** | **None** | The key only runs from your Mac. "Websites", "iOS apps" and "Android apps" would block our script. "IP addresses" works but breaks when your home internet address changes. |
| **API restrictions** | **Restrict key** → tick only **Places API (New)** | If the key ever leaked, it could only do place lookups, not other paid Google services. |

Click **Save**.

> Don't see **Places API (New)** in the dropdown? Go back to step 1. It isn't enabled yet.

## 4. Cap the cost

| Safety net | Where | Set to | What it does |
|---|---|---|---|
| **Daily limit** | APIs & Services → Places API (New) → **Quotas** | ~**500** requests/day | **Actually stops** usage. One full run needs ~150–250 lookups. |
| **Budget alert** | Billing → **Budgets & alerts** | **$1** with email alerts | Only **emails you**. It doesn't stop spending. |

## 5. Add the key to the project
Open `.env` in the project folder (create it if it doesn't exist) and add one line:

```
GOOGLE_PLACES_API_KEY=your-key-here
```

- No spaces around `=`, no quotes
- `.env` is never uploaded to GitHub (it's in `.gitignore`)
- Don't paste the key into the chat. Claude checks that it's there without showing it.

## Checklist
- [ ] Places API (New) enabled
- [ ] Key created
- [ ] Application restrictions: **None**
- [ ] API restrictions: **Places API (New)** only
- [ ] Daily limit ~500
- [ ] $1 budget alert
- [ ] Key saved in `.env`

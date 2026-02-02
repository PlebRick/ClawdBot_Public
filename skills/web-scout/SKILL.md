# Web Scout — Authenticated Headless Browser Skill

## Description
General-purpose authenticated headless browser for browsing auth-gated web apps on demand — conversationally or via cron. Uses Rick's Chrome session cookies/tokens for authentication.

## Targets

| Target | Profile | Auth Method | Status |
|--------|---------|-------------|--------|
| IntoTheCryptoverse | `itc` | Firebase (IndexedDB injection) | ✅ Working |
| CNN Fear & Greed | `cnn-fg` | None | ✅ Working |
| Logos Web App | `logos` | Cookie injection | ✅ Working — Books search, Library search, Factbook |
| Gospel Truth (Finney) | `finney` | None | ✅ Working — 851 sermons, subject/scripture indexes |

## Usage

### CNN Fear & Greed (no auth)
```bash
node skills/web-scout/profiles/cnn-fg.js
```
Returns JSON with index value, label, and all 7 component indicators.

### ITC (Firebase auth)
```bash
# Navigate to a known page
node skills/web-scout/profiles/itc.js dashboard
node skills/web-scout/profiles/itc.js risk-levels
node skills/web-scout/profiles/itc.js btc-risk

# Known page shortcuts: dashboard, charts, risk, risk-levels, dominance,
# fear-greed, mvrv, mvrv-z, nupl, sopr, interest-rate, recession,
# inflation, log-regression, bull-market-support, pi-cycle, hash-ribbons,
# bubble-risk, btc-risk, sp500-risk, gold-risk, dxy-risk

# Or use any URL path: node profiles/itc.js /charts/correlation-coefficients
```

### Gospel Truth / Finney (no auth)
```bash
# Combined search (sermons + subjects)
node skills/web-scout/profiles/finney.js "revival" search

# Sermon index search
node skills/web-scout/profiles/finney.js "prayer" sermons

# Subject index search
node skills/web-scout/profiles/finney.js "holiness" subjects

# Scripture reference search
node skills/web-scout/profiles/finney.js "Romans" scripture

# Read a specific sermon page
node skills/web-scout/profiles/finney.js "https://www.gospeltruth.net/1868Lect_on_Rev_of_Rel/68revlec01.htm" read

# Known page shortcuts: home, works, sermons, subjects, scripture,
# life, timeline, glossary, letters, selected, oberlin, audio, others
# Subject shortcuts: god, jesus, holy-spirit, faith, holiness, prayer, wicked, true-false
```

### Logos (cookie auth)
```bash
# Search Rick's 7,500-book library
node skills/web-scout/profiles/logos.js "prevenient grace" books
node skills/web-scout/profiles/logos.js "Romans 8:28" bible
node skills/web-scout/profiles/logos.js "atonement" all

# Search kinds: all, books, bible, factbook, morph, media, maps

# Cookie extraction (run once, then when session expires)
DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/1000/bus" python3 skills/web-scout/scripts/extract-cookies.py logos
```

### Cookie/Token Refresh
When a session expires:
1. Clawd detects login redirect
2. Notifies Rick to re-login on Chrome
3. Rick confirms
4. Run: `./skills/web-scout/scripts/refresh-cookies.sh`
5. For ITC: re-extract Firebase tokens from Chrome IndexedDB

## Architecture
- **Engine:** Playwright (Node.js) with headless Chromium
- **Cookie auth (Logos):** AES-128-CBC decryption from Chrome's encrypted cookie store via GNOME Keyring
- **Firebase auth (ITC):** IndexedDB injection via `addInitScript` — refresh token persists, access token auto-refreshes
- **Rate limiting:** 2s minimum between page loads, exponential backoff on errors

## File Structure
```
skills/web-scout/
├── SKILL.md
├── lib/
│   ├── session.js          # Browser session manager
│   ├── navigate.js         # Navigation helpers with auth
│   └── detect-expiry.js    # Session expiry detection
├── profiles/
│   ├── cnn-fg.js           # CNN Fear & Greed extractor
│   ├── itc.js              # ITC profile (Firebase auth)
│   ├── logos.js            # Logos profile (cookie auth) — search, library, book access
│   └── finney.js           # Gospel Truth / Finney (no auth) — 851 sermons, indexes
├── scripts/
│   ├── extract-cookies.py  # Chrome cookie decryption
│   ├── extract-cookies.sh  # Shell wrapper
│   └── refresh-cookies.sh  # Re-extraction after re-login
├── cookies/                # gitignored, chmod 600
└── output/                 # Screenshots and exports
```

## Security
- Cookie/token files: chmod 600, gitignored
- No credentials in code — all read from secure files at runtime
- Firebase API key is public (client-side Firebase) — refresh token is the secret

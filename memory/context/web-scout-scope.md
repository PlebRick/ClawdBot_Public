# Web Scout — Skill Scoping Doc
*Created: 2026-01-30 | Author: Clawd | Category: B (read-only, no external writes)*


## Purpose
General-purpose authenticated headless browser skill. Allows Clawd to browse auth-gated web apps on demand — conversationally or via cron — using Rick's existing logged-in Chrome sessions for cookie auth.


## Targets


| Target | URL | Auth | Use Cases |
|--------|-----|------|-----------|
| IntoTheCryptoverse | app.intothecryptoverse.com | Firebase Auth (IndexedDB injection) | Macro data, recession risk, crypto cycle metrics, 118+ charts — ad hoc + weekly report |
| CNN Fear & Greed | fear-and-greed.cnn.com (or equivalent) | None | Index value + components — ad hoc + morning brief/weekly report |
| Logos Web App | app.logos.com | Cookie (account login) | Search/browse Rick's 7,500-book theological library on demand |
| Gospel Truth (Finney) | gospeltruth.net | None | 851 sermons/lectures, subject index, scripture index, Oberlin Evangelist archive |


## Architecture


### Why Playwright (Node.js)
- Ships with Clawdbot's Node runtime — no Python dependency
- Native cookie import via `browserContext.addCookies()`
- Headless Chromium included — no external browser dependency
- Better async/await API than Puppeteer
- Built-in screenshot, PDF, network interception
- Cross-browser support if needed later


### Components (as-built)


```
skills/web-scout/
├── SKILL.md              # Skill definition + usage docs
├── .gitignore            # Excludes cookies/*.json, node_modules/
├── package.json          # Playwright dependency
├── lib/
│   ├── session.js        # Playwright session manager (launch, cookie inject, rate limit, close)
│   ├── navigate.js       # Auth-aware navigation helpers (openProfile, navigateTo, extract, screenshot)
│   └── detect-expiry.js  # Session expiry detection (login redirect + DOM patterns per profile)
├── profiles/
│   ├── cnn-fg.js         # CNN Fear & Greed — index + 7 components, JSON output
│   ├── itc.js            # ITC — Firebase auth via addInitScript, 20+ page shortcuts, search, screenshots
│   ├── logos.js          # Logos — Books/Bible/Factbook search, library catalog, book reader
│   └── finney.js         # Gospel Truth — 851 sermons, subject/scripture index, full text reading
├── scripts/
│   ├── extract-cookies.py  # Chrome cookie decryption (v11 AES-128-CBC via GNOME Keyring)
│   ├── extract-cookies.sh  # Shell wrapper (sets DBUS_SESSION_BUS_ADDRESS)
│   └── refresh-cookies.sh  # Re-extraction after Rick re-logs in
├── cookies/              # gitignored, chmod 600
│   ├── .gitkeep
│   ├── itc-cookies.json       # ITC domain cookies (analytics only — auth is Firebase)
│   ├── itc-firebase.json      # Firebase refresh token + API key + UID
│   └── logos-cookies.json     # Logos auth + session cookies
└── output/               # Screenshots and exports (gitignored)
```


### Cookie & Auth Management (as-built)


**Two auth methods discovered during implementation:**


**1. Cookie Auth (Logos):**
- Chrome stores cookies in `~/.config/google-chrome/Default/Cookies` (SQLite3)
- Encryption: v11 AES-128-CBC, key from GNOME Keyring via D-Bus (`secretstorage` Python lib)
- Key is base64-encoded in keyring → decoded to 16-byte raw key (NOT PBKDF2-derived as initially assumed)
- Extraction: `scripts/extract-cookies.py` → Playwright-compatible JSON
- Storage: `cookies/logos-cookies.json` (chmod 600, gitignored)


**2. Firebase Auth (ITC):**
- ITC app (`app.intothecryptoverse.com`) uses Firebase Auth, NOT cookies
- Auth tokens stored in Chrome's IndexedDB (LevelDB on disk)
- Extracted via `strings` on LevelDB files → refresh token + API key + UID
- Injected into Playwright via `context.addInitScript()` before page load
- Firebase SDK auto-refreshes access token from refresh token
- Storage: `cookies/itc-firebase.json` (chmod 600, gitignored)


**3. No Auth (CNN F&G, Gospel Truth/Finney):**
- Direct headless navigation, no cookies or tokens needed


**Refresh flow:**
1. Clawd detects session expiry (login redirect URL pattern per profile)
2. Notifies Rick: "[site] session expired — please log in on Chrome and tell me when done"
3. Rick logs in, says "done"
4. For Logos: run `refresh-cookies.sh` to re-extract cookies
5. For ITC: re-extract Firebase tokens from IndexedDB (manual strings extraction or future script)
6. Resume operation


**Expiry detection (`lib/detect-expiry.js`):**
- Per-profile URL patterns (e.g., `/authentication/login` for ITC, `/login` for Logos)
- Per-profile DOM selectors for login forms
- Called after every navigation in `lib/navigate.js`


### How It Works (Conversational)


Rick: "Check ITC for the current recession probability"
1. Clawd invokes web-scout skill
2. Launches headless Playwright with ITC cookies
3. Navigates to ITC recession probability page (profile knows the URL)
4. Extracts data (DOM text, chart screenshot, or both)
5. Returns results to conversation
6. Closes browser context


Rick: "Search Logos for N.T. Wright's commentary on Romans 8"
1. Launches headless Playwright with Logos cookies
2. Navigates to app.logos.com
3. Uses search functionality
4. Extracts results (titles, snippets, book references)
5. Can navigate into a specific book if Rick asks
6. Returns content to conversation


### How It Works (Cron)


Existing cron scripts (morning brief, weekly report) call web-scout via:
- Shell exec: `node skills/web-scout/scripts/fetch-cnn-fg.js` → stdout JSON
- Or: Clawd invokes it internally during report generation


Output format: JSON for structured data, PNG for charts/screenshots.


```json
{
  "source": "cnn-fear-greed",
  "timestamp": "2026-01-30T10:00:00Z",
  "data": {
    "index": 72,
    "label": "Greed",
    "components": {
      "market_momentum": 78,
      "stock_price_strength": 65,
      "stock_price_breadth": 70,
      "put_call_ratio": 68,
      "market_volatility": 75,
      "safe_haven_demand": 71,
      "junk_bond_demand": 74
    }
  }
}
```


## Implementation Plan


### Phase 1: Foundation (CNN Fear & Greed) ✅ COMPLETE 2026-01-30
- [x] Install Playwright in skill directory
- [x] Build session manager (no auth needed for CNN)
- [x] Build CNN F&G profile — extract index + components (all 7)
- [x] Test via exec
- Pending: integrate with morning brief cron


### Phase 2: Cookie Infrastructure ✅ COMPLETE 2026-01-30
- [x] Build cookie extraction script for Linux Chrome (Python, v11 AES-128-CBC)
- [x] Test extraction for ITC domain — discovered Firebase auth, not cookies
- [x] Test extraction for Logos domain — cookie auth working
- [x] Build expiry detection (login redirect + DOM patterns)
- [x] Build refresh notification flow (shell scripts)


### Phase 3: IntoTheCryptoverse ✅ COMPLETE 2026-01-30
- [x] Build ITC profile with Firebase IndexedDB injection
- [x] Test authenticated navigation (dashboard, charts, macro)
- [x] Ad hoc browsing capability — 118+ charts, 20+ shortcuts
- [x] Site structure mapped: Crypto, Macro, TradFi, Tools, Content
- Pending: integrate with weekly market report cron


### Phase 4: Logos Web App ✅ COMPLETE 2026-01-30
- [x] Build Logos profile — Books search, Library search, book access
- [x] Test authenticated access to library (7,500+ books)
- [x] Books search returns source citations with page numbers
- [x] AI Synopsis extraction from search results
- [x] Multiple search kinds: all, books, bible, factbook, morph, media, maps


### Phase 5: Skill Packaging ✅ COMPLETE 2026-01-30
- [x] Write SKILL.md with full usage docs
- [ ] Register as Clawdbot skill (pending skill registry integration)
- [x] Document cookie refresh process for Rick


## Risks & Mitigations


| Risk | Impact | Mitigation | Status |
|------|--------|------------|--------|
| Cookie encryption on Linux hard to crack | Can't extract cookies | ~~Fallback: profile copy~~ Solved: v11 AES-128-CBC via GNOME Keyring | ✅ Resolved |
| ITC uses Firebase, not cookies | Cookie approach doesn't work | Discovered during Phase 2; pivoted to IndexedDB token extraction + `addInitScript` | ✅ Resolved |
| Sites detect headless browser | Blocked/captcha | `playwright-extra` with stealth plugin if needed; not triggered yet | Monitoring |
| Session expires during cron job | Missing data in report | Detect + notify Rick + graceful degradation (skip section, note "data unavailable") | Built |
| Site layout changes break extraction | Wrong data | Per-profile selectors are isolated; fix one profile without touching others | Accepted |
| Cookie/token files leaked via git | Security incident | `.gitignore` + chmod 600 + pre-commit hook (planned for git backup) | Mitigated |
| Logos SPA renders results asynchronously | Can't extract search results | Content-based div filtering instead of class selectors; 12s wait for render | ✅ Resolved |


## Rollback
- Skill is additive — doesn't modify any existing functionality
- Remove: delete `skills/web-scout/`, remove from skill registry
- Existing cron scripts fall back to current data sources (no ITC/CNN data, but everything else works)


## Supervisor Clarifications (2026-01-30)


### ITC: Search + Navigate
Two modes — search box for queries, direct navigation for known pages. Phase 3 starts with search box + known high-value pages (recession probability, BTC risk, cycle metrics). ClawdBot learns site structure over time — explores on request, remembers paths. No crawling, no pre-indexing.


### Logos: Library Search First
Phase 4 priority order:
1. Library search ("What books do I have on atonement?")
2. Passage lookup ("What do my books say about Romans 8:28?")
3. Topic/Factbook reference lookups
4. Bible search + other modes — added based on Rick's actual usage


### Cookie Fallback
- Primary: cookie extraction (no Chrome conflict)
- Fallback: copy profile to `/tmp/web-scout-profile/` (no Chrome conflict — it's a copy)
- Rick never closes Chrome


### Rate Limiting
- Minimum 2s delay between page loads (cron and repeated requests)
- Exponential backoff on errors: 2s → 4s → 8s → max 60s
- Conversational single requests: natural pacing, backoff on errors


### Skill Path
Confirmed: `~/clawd/skills/web-scout/`


### Supervisor Verdict
✅ APPROVED — Proceed with implementation. Phase 1 first (CNN F&G, no auth).


---


## Decision Log
- Playwright over Puppeteer: better API, built-in cookie support, ships with Chromium
- Skill over standalone scripts: four targets with same pattern = reusable tool
- Cookie extraction over Chrome relay: relay is unreliable on Linux (known issue, now resolved)
- On-demand over scheduled-only: Rick wants to browse ITC and Logos conversationally
- Firebase `addInitScript` over IndexedDB copy: Playwright can't read Chrome's IndexedDB format directly; injecting tokens via init script runs before page JS and lets Firebase SDK handle token refresh
- AES-128-CBC with raw base64-decoded key (not PBKDF2-derived): Chrome v11 on this system stores the key base64-encoded in GNOME Keyring; decoding gives the 16-byte AES key directly
- Gospel Truth added as 4th target (2026-01-30): no auth, static HTML, index-based search since site has no search input
- Logos search extraction via div content filtering (not DOM selectors): SPA renders results in dynamic panels; class names are unreliable, content matching is stable
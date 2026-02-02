# Morning Brief — Design Spec
*Finalized: 2026-01-27 | Merged from original spec + new integrations*

## Delivery
- **Scheduled:** 4:30 AM CST daily via Telegram DM + Web UI
- **On-demand:** "morning brief" or similar in any channel
- **Cron:** Clawdbot built-in cron system (isolated session)
- **Tone:** Direct, concise, no fluff. Conservative perspective.

## Section Order

1. ₿ **MARKETS** (top priority)
   - BTC — price, 24h change, market cap
   - TSLA — price, pre-market if available
   - ES Futures (S&P 500 E-mini) — overnight action
   - Gold Futures — price, direction
   - Fear & Greed — BTC (alternative.me) + SPY/traditional (CNN) ✅ [web-scout skill ready]
   - 18-Year Real Estate Cycle triggers: homebuilder stocks (XHB, DHI, LEN, KBH), housing data
   - Recession Indicators: yield curve, Sahm Rule, LEI, unemployment claims, ISM
   - Philosophy: go beyond mainstream — look for contrarian/data-driven signals

2. 📖 **SCRIPTURE**
   - Revised Common Lectionary — daily readings
   - Full verses in ESV (English Standard Version)
   - Source: lectionary.library.vanderbilt.edu or similar RCL source

3. 🗓️ **SCHEDULE** — Google Calendar events for today

4. ✅ **TASKS** — Google Tasks due today or overdue, grouped by list

5. 📧 **EMAIL** — Unread count + flagged/important subject lines (NO body text)

6. 📰 **NEWS & SOCIAL**
   - World headlines — top 3-5 stories, conservative perspective
   - Elon Musk (@elonmusk) — recent X posts/activity ✅
   - Trump (@realDonaldTrump) — recent posts/statements ✅
   - Mark Driscoll (@PastorMark) — recent posts/content ✅
   - Lyn Alden (@LynAldenContact) — recent posts/analysis ✅
   - Southern Illinois local news — Nashville IL area

7. 🎥 **YOUTUBE WATCHLIST**
   - Trading Fraternity — latest video + key points summary
   - Amit Investing — stock market analysis
   - Into The Cryptoverse — crypto macro (Benjamin Cowen)
   - More channels TBD

8. 🌤️ **WEATHER** — Nashville, IL 62263
   - Current conditions + daily forecast
   - Severe weather alerts if any

9. 📝 **CLAWD NOTES** — Carryover from daily logs, open reminders, pending TODOs

## Data Sources

| Source | Method | Status |
|--------|--------|--------|
| Google Calendar | OAuth script | ✅ Ready |
| Google Tasks | OAuth script | ✅ Ready |
| Gmail | OAuth script | ✅ Ready |
| YouTube Data API | OAuth script | ✅ Ready |
| BTC price | CoinGecko API (web fetch) | ✅ Ready |
| TSLA / ES / Gold | Web fetch (Yahoo Finance, etc.) | ✅ Available |
| Recession indicators | Web fetch / Brave Search | ✅ Available |
| Homebuilder stocks | Web fetch (Yahoo Finance) | ✅ Available |
| Brave Search (headlines) | API key in gateway config | ✅ Ready |
| RCL Lectionary | Web fetch (Vanderbilt) | ✅ Available |
| Weather | wttr.in (Nashville IL) | ✅ Ready |
| Memory/daily logs | Local file read | ✅ Ready |
| X/Twitter | bird CLI (cookie auth) | ✅ Ready (read; posting has rate limit issue) |
| Fear & Greed (BTC) | alternative.me API | ✅ Available |
| Fear & Greed (CNN) | web-scout skill (Playwright) | ✅ Ready — `node skills/web-scout/profiles/cnn-fg.js` |
| IntoTheCryptoverse | web-scout skill (Firebase auth) | ✅ Ready — `node skills/web-scout/profiles/itc.js` |

## Format Rules
- Emoji-sectioned, scannable
- No markdown tables (Telegram-unfriendly)
- Each section 2-5 lines max (markets can be longer)
- Bold key numbers
- No email body text — subject lines only for flagged items
- Conservative perspective on news — not left-wing propaganda
- Flag anything urgent
- Telegram-friendly formatting throughout

## Rick's Preferences
- Markets FIRST (BTC is primary interest)
- Weather: Nashville, IL 62263
- Gmail flagged subject lines shown (that's why they're flagged)
- 4:30 AM CST delivery
- Go beyond mainstream talking heads — contrarian/data-driven signals
- ESV for Scripture readings

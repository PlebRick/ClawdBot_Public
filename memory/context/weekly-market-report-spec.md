# Weekly Market Analysis Report — Spec
*Created: 2026-01-29 | Author: Clawd*

## Delivery
- **Schedule:** Friday 4:00 AM CST via cron
- **Outputs:** (1) Telegram DM to Rick, (2) `.docx` uploaded to Trading folder on Drive
- **Naming:** `YYYY-MM-DD_Weekly_Market_Analysis.docx`
- **Approval:** NOT required — auto-send approved by Rick (2026-01-29)
- **Tone:** Data-driven, contrarian, concise but thorough. No bloviating.

## Section Order

### 1. 📊 EXECUTIVE SUMMARY
- Bull/Bear/Neutral scorecard per asset class (BTC, equities, gold/silver, DXY, bonds)
- 1-paragraph "state of the market" — what happened this week in 4 sentences
- Fear & Greed trajectory: Monday → Friday (getting greedier or more fearful?)

### 2. ₿ BITCOIN & CRYPTO
- Weekly price action: open, close, high, low, % change
- Key support/resistance levels
- On-chain signals: MVRV ratio, exchange flows, whale accumulation (Glassnode/CryptoQuant summaries via Brave)
- ETF flows if notable
- Catalysts that moved price this week
- Short/medium/long-term outlook

### 3. 📈 EQUITIES & AI
- S&P 500, Nasdaq weekly performance
- TSLA: price action, news, catalysts
- AI headlines: major moves, earnings, spending narratives
- Notable earnings or guidance this week

### 4. 🏠 18-YEAR REAL ESTATE CYCLE WATCH
- Homebuilder stocks: XHB ETF, DHI, LEN, KBH — weekly performance
- Housing data if released this week (starts, permits, existing/new home sales)
- Mortgage rates trend
- Crash signals / top indicators — flag anything concerning
- Cycle position commentary

### 5. 🏦 MACRO & RECESSION WATCH
- Fed activity / FOMC notes if applicable
- DXY (dollar index) — weekly trend, implications
- 10Y yield — direction, yield curve status
- Bank of Japan carry trade — any BOJ moves or yen volatility
- Gold & Silver — weekly price action, what metals are signaling
- Liquidity indicators — reverse repo, M2 money supply if searchable
- Recession probability signals — flag any deterioration

### 6. 🔮 CONTRARIAN SIGNAL SECTION
- "What the crowd thinks vs. what the data says"
- Sentiment extremes (greed = caution, fear = opportunity)
- Divergences between assets (e.g., gold up + stocks up = something's off)
- Positions that mainstream is ignoring

### 7. 📡 RICK'S RADAR
- Items matching Rick's thesis: real estate cycle top, dollar weakness, BTC accumulation zones
- Things mainstream isn't covering but data supports
- Pattern recognition across domains

### 8. 🎙️ ANALYST & CREATOR ROUNDUP
Summary of key perspectives from this week. For each, pull from YouTube, X, Substack, or whatever is available:

| Creator | Platform(s) | Focus |
|---------|------------|-------|
| Lyn Alden | X (@LynAldenContact), Substack, YouTube | Macro, liquidity, BTC |
| Benjamin Cowen | YouTube (Into The Cryptoverse), X | BTC/crypto cycles, risk metrics |
| Trading Fraternity | YouTube | Day trading, ES/NQ, market structure |
| Invest Answers | YouTube | BTC, macro, portfolio strategy |
| BTC Sessions News | YouTube | Bitcoin news, adoption |
| Amit Kukreja | YouTube, X | Markets, geopolitics |
| Jason Pizzino | YouTube | BTC/crypto, charting, cycles |
| Rabbit Hole Recap | YouTube | Bitcoin weekly news recap |

For each creator: 1-3 sentence summary of their key take this week. If no new content, skip.

### 9. 📰 HEADLINES & CATALYSTS
- Top 5-7 headlines of the week (crypto, macro, AI, politics)
- Conservative perspective where relevant
- Elon/Trump/Driscoll activity flagged if notable

### 10. 📅 NEXT WEEK'S CATALYST CALENDAR
- Scheduled data releases (CPI, jobs, PMI, etc.)
- Fed speeches
- Major earnings
- Geopolitical events
- Crypto-specific dates (unlocks, upgrades, ETF deadlines)

## Data Sources

### APIs / Scripts
- `morning-brief-data.py` — BTC, TSLA, ES, Gold, DXY, 10Y, homebuilders, Fear & Greed
- CoinGecko — BTC price data
- Yahoo Finance — equities, futures, yields
- alternative.me — BTC Fear & Greed

### Web Scout Skill (Headless Browser) — NEW 2026-01-30
- CNN Fear & Greed — index + 7 components (`node skills/web-scout/profiles/cnn-fg.js`)
- IntoTheCryptoverse — risk levels, macro data, recession indicators, 118+ charts (`node skills/web-scout/profiles/itc.js`)
- See `memory/context/web-scout-scope.md` for full capability list

### Web Search (Brave)
- Weekly recaps from major outlets
- On-chain data summaries (Glassnode, CryptoQuant, lookintobitcoin)
- Creator content (YouTube titles + descriptions, X posts, Substack)
- Housing/real estate data
- BOJ / carry trade news
- Upcoming economic calendar

### X/Twitter (bird CLI)
- @LynAldenContact — weekly posts
- Other creators' X accounts as discovered

### YouTube Data API
- Latest videos from all 8 channels (title, description, publish date)

## Document Format
- `.docx` with headers, bullet points, bold key numbers
- Date-first filename: `YYYY-MM-DD_Weekly_Market_Analysis.docx`
- Footer: "Prepared by Clawd for Rick Arnold | [date]"
- No markdown tables (Telegram-unfriendly)
- Telegram version: emoji-sectioned, scannable, same content but formatted for chat

## Logging
- Log each delivery to `memory/arnoldos-proving-log.md`
- Note any data source failures for debugging

---

## ITC Integration (Added 2026-02-02)

### Data Fetcher
```bash
python3 scripts/itc-data.py
# or
node scripts/itc-data.js
```

### Available Metrics
- **BTC Risk Level** — `/assets/bitcoin/risk` page
- **Interest Rate / Macro** — `/charts/interest-rate` (recession indicators, Fed data)
- **MVRV-Z Score** — `/charts/mvrv-z-score` (on-chain valuation)
- **Fear & Greed** — `/charts/fear-greed-index` (ITC's version)

### Session Management
- ITC uses Firebase auth (IndexedDB token injection)
- Session tokens stored in `skills/web-scout/cookies/itc-firebase.json`
- If session expires, `itc-data.py` sends Telegram alert to Rick
- Report continues without ITC data (graceful degradation)

### Weekly Report Usage
The weekly market cron should call `python3 scripts/itc-data.py` and include:
1. BTC Risk value (if available)
2. Note which ITC pages were accessible
3. Flag if session expired (needs re-login)

### To Re-authenticate ITC
1. Log into https://app.intothecryptoverse.com in Chrome
2. Use DevTools > Application > IndexedDB > firebaseLocalStorageDb
3. Copy the auth user object
4. Update `skills/web-scout/cookies/itc-firebase.json`

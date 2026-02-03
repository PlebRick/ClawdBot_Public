#!/usr/bin/env python3
"""Gather all morning brief data from Google APIs + market data.
Outputs JSON to stdout for Clawd to consume.
"""

import json
import sys
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(__file__))

CT = timezone(timedelta(hours=-6))


def load_google_creds():
    """Load Google OAuth credentials with auto-refresh."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    TOKEN_FILE = os.path.expanduser("~/.config/clawd/google-tokens.json")
    SCOPES = [
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/tasks",
        "https://www.googleapis.com/auth/youtube.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/gmail.compose",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.readonly",
    ]

    if not os.path.exists(TOKEN_FILE):
        return None

    with open(TOKEN_FILE) as f:
        token_data = json.load(f)

    creds = Credentials(
        token=token_data["token"],
        refresh_token=token_data["refresh_token"],
        token_uri=token_data["token_uri"],
        client_id=token_data["client_id"],
        client_secret=token_data["client_secret"],
        scopes=token_data.get("scopes", SCOPES),
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_data["token"] = creds.token
        with open(TOKEN_FILE, "w") as f:
            json.dump(token_data, f, indent=2)

    return creds


def fetch_json(url, timeout=10):
    """Fetch JSON from a URL."""
    req = urllib.request.Request(url, headers={"User-Agent": "Clawd/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def fetch_text(url, timeout=10):
    """Fetch text from a URL."""
    req = urllib.request.Request(url, headers={"User-Agent": "Clawd/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def get_calendar_events(creds):
    """Get today's calendar events."""
    try:
        from googleapiclient.discovery import build
        svc = build("calendar", "v3", credentials=creds)
        now = datetime.now(CT)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0)
        events = svc.events().list(
            calendarId="primary",
            timeMin=start_of_day.isoformat(),
            timeMax=end_of_day.isoformat(),
            singleEvents=True,
            orderBy="startTime",
            maxResults=20,
        ).execute()
        result = []
        for e in events.get("items", []):
            start = e.get("start", {})
            time_str = start.get("dateTime", start.get("date", ""))
            result.append({
                "summary": e.get("summary", "(no title)"),
                "start": time_str,
                "location": e.get("location", ""),
                "all_day": "date" in start and "dateTime" not in start,
            })
        return {"ok": True, "events": result}
    except Exception as ex:
        return {"ok": False, "error": str(ex)}


def get_tasks(creds):
    """Get tasks due today or overdue."""
    try:
        from googleapiclient.discovery import build
        svc = build("tasks", "v1", credentials=creds)
        lists = svc.tasklists().list(maxResults=10).execute()
        all_tasks = []
        for tl in lists.get("items", []):
            tasks = svc.tasks().list(
                tasklist=tl["id"],
                showCompleted=False,
                showHidden=False,
                maxResults=50,
            ).execute()
            for t in tasks.get("items", []):
                all_tasks.append({
                    "title": t.get("title", "(no title)"),
                    "due": t.get("due", ""),
                    "list": tl.get("title", ""),
                    "notes": t.get("notes", ""),
                })
        all_tasks.sort(key=lambda t: t["due"] if t["due"] else "9999")
        return {"ok": True, "tasks": all_tasks}
    except Exception as ex:
        return {"ok": False, "error": str(ex)}


def get_gmail_snapshot(creds):
    """Get unread count and flagged/starred emails."""
    try:
        from googleapiclient.discovery import build
        svc = build("gmail", "v1", credentials=creds)
        unread = svc.users().messages().list(
            userId="me", q="is:unread in:inbox", maxResults=1,
        ).execute()
        unread_count = unread.get("resultSizeEstimate", 0)
        starred = svc.users().messages().list(
            userId="me", q="is:starred is:unread", maxResults=5,
        ).execute()
        flagged = []
        for msg in starred.get("messages", []):
            detail = svc.users().messages().get(
                userId="me", id=msg["id"], format="metadata",
                metadataHeaders=["Subject", "From"],
            ).execute()
            headers = {h["name"]: h["value"] for h in detail.get("payload", {}).get("headers", [])}
            flagged.append({
                "subject": headers.get("Subject", "(no subject)"),
                "from": headers.get("From", ""),
            })
        return {"ok": True, "unread_count": unread_count, "flagged": flagged}
    except Exception as ex:
        return {"ok": False, "error": str(ex)}


def get_youtube_channels(creds):
    """Get latest videos from watchlist channels."""
    try:
        from googleapiclient.discovery import build
        svc = build("youtube", "v3", credentials=creds)

        channels = {
            "Trading Fraternity": "UCfBYOmKJB0ixAGl8gECbsYg",
            "Amit Investing": "UC5OMi0UBnr7Bx0sPjSGQ28g",
            "Into The Cryptoverse": "UCRvqjQPSeaWn-uEx-w0XOIg",
        }

        results = {}
        for name, channel_id in channels.items():
            try:
                search = svc.search().list(
                    part="snippet",
                    channelId=channel_id,
                    order="date",
                    maxResults=2,
                    type="video",
                ).execute()
                videos = []
                for item in search.get("items", []):
                    snippet = item.get("snippet", {})
                    videos.append({
                        "title": snippet.get("title", ""),
                        "published": snippet.get("publishedAt", ""),
                        "video_id": item.get("id", {}).get("videoId", ""),
                        "description": snippet.get("description", "")[:200],
                    })
                results[name] = {"ok": True, "videos": videos}
            except Exception as ex:
                results[name] = {"ok": False, "error": str(ex)}

        return {"ok": True, "channels": results}
    except Exception as ex:
        return {"ok": False, "error": str(ex)}


# ── Market Data ──────────────────────────────────────────────

def get_btc_price():
    """BTC price from CoinGecko."""
    try:
        data = fetch_json(
            "https://api.coingecko.com/api/v3/simple/price"
            "?ids=bitcoin&vs_currencies=usd&include_24hr_change=true&include_market_cap=true"
        )
        btc = data.get("bitcoin", {})
        return {
            "ok": True,
            "price_usd": btc.get("usd"),
            "change_24h": btc.get("usd_24h_change"),
            "market_cap": btc.get("usd_market_cap"),
        }
    except Exception as ex:
        return {"ok": False, "error": str(ex)}


def get_btc_fear_greed():
    """BTC Fear & Greed Index from alternative.me."""
    try:
        data = fetch_json("https://api.alternative.me/fng/?limit=1")
        entry = data.get("data", [{}])[0]
        return {
            "ok": True,
            "value": int(entry.get("value", 0)),
            "label": entry.get("value_classification", ""),
        }
    except Exception as ex:
        return {"ok": False, "error": str(ex)}



def get_cnn_fear_greed():
    """CNN Fear & Greed Index via Web Scout headless browser."""
    import subprocess
    try:
        result = subprocess.run(
            ["node", os.path.expanduser("~/clawd/skills/web-scout/profiles/cnn-fg.js")],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            return {"ok": False, "error": f"Web Scout failed: {result.stderr[:100]}"}
        
        data = json.loads(result.stdout)
        index = data.get("data", {}).get("index", 0)
        label = data.get("data", {}).get("label", "unknown")
        components = data.get("data", {}).get("components", {})
        
        # Flag extremes
        extreme = None
        if index <= 25:
            extreme = "EXTREME FEAR"
        elif index >= 75:
            extreme = "EXTREME GREED"
        
        return {
            "ok": True,
            "index": index,
            "label": label,
            "extreme": extreme,
            "components": components
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "CNN F&G timeout (30s)"}
    except json.JSONDecodeError as e:
        return {"ok": False, "error": f"JSON parse error: {e}"}
    except Exception as ex:
        return {"ok": False, "error": str(ex)}


def get_yahoo_quote(symbol):
    """Get a stock/futures quote from Yahoo Finance v8 API."""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1d&interval=1d"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Clawd/1.0",
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())

        result = data.get("chart", {}).get("result", [{}])[0]
        meta = result.get("meta", {})
        price = meta.get("regularMarketPrice", meta.get("previousClose"))
        prev_close = meta.get("chartPreviousClose", meta.get("previousClose"))
        change_pct = None
        if price and prev_close and prev_close > 0:
            change_pct = ((price - prev_close) / prev_close) * 100

        return {
            "ok": True,
            "symbol": symbol,
            "price": price,
            "prev_close": prev_close,
            "change_pct": change_pct,
        }
    except Exception as ex:
        return {"ok": False, "symbol": symbol, "error": str(ex)}


def get_market_quotes():
    """Get TSLA, ES futures, Gold, Homebuilder stocks."""
    symbols = {
        "TSLA": "TSLA",
        "ES_futures": "ES=F",
        "Gold": "GC=F",
        "XHB": "XHB",       # Homebuilder ETF
        "DHI": "DHI",       # D.R. Horton
        "LEN": "LEN",       # Lennar
        "KBH": "KBH",       # KB Home
        "DXY": "DX-Y.NYB",  # Dollar index
    }
    results = {}
    for key, symbol in symbols.items():
        results[key] = get_yahoo_quote(symbol)
    return results


def get_recession_indicators():
    """Fetch key recession indicator data points."""
    indicators = {}

    # 10Y-2Y yield spread (inverted = recession signal)
    try:
        t10 = fetch_json("https://query1.finance.yahoo.com/v8/finance/chart/%5ETNX?range=1d&interval=1d")
        t2 = fetch_json("https://query1.finance.yahoo.com/v8/finance/chart/%5EIRX?range=1d&interval=1d")
        t10_price = t10.get("chart", {}).get("result", [{}])[0].get("meta", {}).get("regularMarketPrice")
        # IRX is 13-week T-bill, not 2Y — approximate
        indicators["10Y_yield"] = {"ok": True, "value": t10_price}
    except Exception as ex:
        indicators["10Y_yield"] = {"ok": False, "error": str(ex)}

    return indicators


# ── Lectionary ───────────────────────────────────────────────

def get_lectionary():
    """Try to fetch today's RCL readings."""
    try:
        now = datetime.now(CT)
        # Try the Vanderbilt lectionary or a simpler API
        url = f"https://api.dailyprayer.aminder.dev/api/{now.strftime('%m-%d-%Y')}"
        data = fetch_json(url)
        return {"ok": True, "data": data}
    except Exception:
        # Fallback: just return the date for Brave Search lookup
        now = datetime.now(CT)
        return {"ok": False, "fallback": f"Revised Common Lectionary {now.strftime('%B %d %Y')}"}


# ── Main ─────────────────────────────────────────────────────

def main():
    result = {
        "generated_at": datetime.now(CT).isoformat(),
        "calendar": {"ok": False, "error": "no creds"},
        "tasks": {"ok": False, "error": "no creds"},
        "gmail": {"ok": False, "error": "no creds"},
        "youtube": {"ok": False, "error": "no creds"},
        "btc": get_btc_price(),
        "btc_fear_greed": get_btc_fear_greed(),
        "cnn_fear_greed": get_cnn_fear_greed(),
        "market_quotes": get_market_quotes(),
        "recession": get_recession_indicators(),
        "lectionary": get_lectionary(),
    }

    creds = load_google_creds()
    if creds:
        result["calendar"] = get_calendar_events(creds)
        result["tasks"] = get_tasks(creds)
        result["gmail"] = get_gmail_snapshot(creds)
        result["youtube"] = get_youtube_channels(creds)

    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()

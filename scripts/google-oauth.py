#!/usr/bin/env python3
"""Google OAuth2 token management for Clawd.

Usage:
  python3 google-oauth.py auth      # Run OAuth flow (opens browser)
  python3 google-oauth.py refresh   # Refresh existing token
  python3 google-oauth.py test      # Test all APIs
"""

import sys
import os
import json
from pathlib import Path

CREDS_FILE = os.path.expanduser("~/.config/clawd/google-oauth.json")
TOKEN_FILE = os.path.expanduser("~/.config/clawd/google-tokens.json")

# Scopes: read-only for everything except Tasks (read/write per Rick's future needs)
SCOPES = [
    "https://www.googleapis.com/auth/calendar",                # Calendar: READ/WRITE
    "https://www.googleapis.com/auth/tasks",                   # Tasks: READ/WRITE
    "https://www.googleapis.com/auth/youtube.readonly",        # YouTube: READ
    "https://www.googleapis.com/auth/drive",                   # Drive: READ/WRITE
    "https://www.googleapis.com/auth/gmail.compose",           # Gmail: CREATE/SEND drafts
    "https://www.googleapis.com/auth/gmail.send",              # Gmail: SEND messages
    "https://www.googleapis.com/auth/gmail.readonly",          # Gmail: READ
]


def do_auth():
    """Run the OAuth2 browser flow and save tokens."""
    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
    creds = flow.run_local_server(port=8085, prompt="consent", access_type="offline")

    # Save tokens
    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes or SCOPES),
    }
    Path(TOKEN_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)
    os.chmod(TOKEN_FILE, 0o600)

    print(f"✅ Tokens saved to {TOKEN_FILE} (permissions: 600)")
    print(f"   Refresh token: {'present' if creds.refresh_token else '⚠️ MISSING'}")


def load_creds():
    """Load and auto-refresh credentials from saved tokens."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    if not os.path.exists(TOKEN_FILE):
        print(f"❌ No token file at {TOKEN_FILE}. Run: python3 google-oauth.py auth")
        sys.exit(1)

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
        print("🔄 Token expired, refreshing...")
        creds.refresh(Request())
        # Save refreshed token
        token_data["token"] = creds.token
        with open(TOKEN_FILE, "w") as f:
            json.dump(token_data, f, indent=2)
        print("✅ Token refreshed and saved.")

    return creds


def do_refresh():
    """Force-refresh the token."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    creds = load_creds()
    creds.refresh(Request())
    with open(TOKEN_FILE) as f:
        token_data = json.load(f)
    token_data["token"] = creds.token
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)
    print("✅ Token force-refreshed.")


def do_test():
    """Test each API with a simple read call."""
    from googleapiclient.discovery import build

    creds = load_creds()
    results = {}

    # Calendar
    try:
        svc = build("calendar", "v3", credentials=creds)
        events = svc.events().list(calendarId="primary", maxResults=3).execute()
        count = len(events.get("items", []))
        results["Calendar"] = f"✅ {count} upcoming events"
    except Exception as e:
        results["Calendar"] = f"❌ {e}"

    # Tasks
    try:
        svc = build("tasks", "v1", credentials=creds)
        lists = svc.tasklists().list(maxResults=3).execute()
        count = len(lists.get("items", []))
        results["Tasks"] = f"✅ {count} task lists"
    except Exception as e:
        results["Tasks"] = f"❌ {e}"

    # YouTube
    try:
        svc = build("youtube", "v3", credentials=creds)
        resp = svc.channels().list(part="snippet", mine=True).execute()
        results["YouTube"] = f"✅ connected"
    except Exception as e:
        results["YouTube"] = f"❌ {e}"

    # Drive
    try:
        svc = build("drive", "v3", credentials=creds)
        files = svc.files().list(pageSize=3).execute()
        count = len(files.get("files", []))
        results["Drive"] = f"✅ {count} files visible"
    except Exception as e:
        results["Drive"] = f"❌ {e}"

    # Gmail
    try:
        svc = build("gmail", "v1", credentials=creds)
        profile = svc.users().getProfile(userId="me").execute()
        results["Gmail"] = f"✅ {profile.get('emailAddress')}"
    except Exception as e:
        results["Gmail"] = f"❌ {e}"

    print("\n--- API Test Results ---")
    for api, result in results.items():
        print(f"  {api}: {result}")
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd == "auth":
        do_auth()
    elif cmd == "refresh":
        do_refresh()
    elif cmd == "test":
        do_test()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)

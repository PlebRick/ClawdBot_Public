#!/usr/bin/env python3
"""Headless Google OAuth2 flow - manual URL + code entry."""

import os
import json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

CREDS_FILE = os.path.expanduser("~/.config/clawd/google-oauth.json")
TOKEN_FILE = os.path.expanduser("~/.config/clawd/google-tokens.json")

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/tasks",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
]

flow = InstalledAppFlow.from_client_secrets_file(
    CREDS_FILE, 
    SCOPES,
    redirect_uri="urn:ietf:wg:oauth:2.0:oob"
)

auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent")

print("\n" + "="*60)
print("Open this URL in your browser:")
print("="*60)
print(auth_url)
print("="*60)
print("\nAfter authorizing, you'll get a code. Paste it below:")

code = input("Code: ").strip()
flow.fetch_token(code=code)
creds = flow.credentials

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

print(f"\n✅ Tokens saved to {TOKEN_FILE}")
print(f"   Refresh token: {'present' if creds.refresh_token else '⚠️ MISSING'}")

#!/bin/bash
# Encrypts clawdbot.json with GPG and uploads to Drive (datestamped)
# Keeps last 5 versions on Drive, cleans older ones
# Run: bash ~/clawd/scripts/backup-config-encrypted.sh

set -euo pipefail

CONFIG="$HOME/.clawdbot/clawdbot.json"
PASSFILE="$HOME/.config/clawd/config-backup-passphrase"
DATE=$(date +%Y-%m-%d)
FILE_NAME="clawdbot-config-${DATE}.json.gpg"
ENCRYPTED="/tmp/${FILE_NAME}"
DRIVE_FOLDER_ID="1zmrz7wWkmXZdj3FXhFspsdAl0wRpn_4N"
KEEP=5

if [ ! -f "$CONFIG" ]; then echo "❌ Config not found"; exit 1; fi
if [ ! -f "$PASSFILE" ]; then echo "❌ Passphrase not found"; exit 1; fi

PASSPHRASE=$(cat "$PASSFILE")

# Encrypt
gpg --batch --yes --symmetric --cipher-algo AES256 \
  --passphrase "$PASSPHRASE" \
  -o "$ENCRYPTED" "$CONFIG"

echo "✅ Encrypted ${FILE_NAME} ($(stat -c%s "$ENCRYPTED") bytes)"

# Upload to Drive
python3 << PYEOF
import sys, os, json, requests
sys.path.insert(0, os.path.expanduser("~/clawd/scripts"))
from arnoldos import get_creds

creds = get_creds()
FOLDER_ID = "${DRIVE_FOLDER_ID}"
FILE_NAME = "${FILE_NAME}"
KEEP = ${KEEP}

# Check if today's file already exists (update instead of duplicate)
r = requests.get(
    "https://www.googleapis.com/drive/v3/files",
    headers={"Authorization": f"Bearer {creds.token}"},
    params={"q": f"'{FOLDER_ID}' in parents and name='{FILE_NAME}' and trashed=false", "fields": "files(id)"}
)
existing = r.json().get("files", [])

with open("${ENCRYPTED}", "rb") as f:
    data = f.read()

if existing:
    file_id = existing[0]["id"]
    r = requests.patch(
        f"https://www.googleapis.com/upload/drive/v3/files/{file_id}?uploadType=media",
        headers={"Authorization": f"Bearer {creds.token}", "Content-Type": "application/octet-stream"},
        data=data
    )
    print(f"✅ Updated {FILE_NAME} on Drive ({len(data)} bytes)")
else:
    boundary = "----ConfigBackup"
    metadata = json.dumps({"name": FILE_NAME, "parents": [FOLDER_ID]})
    body = (
        f"--{boundary}\r\nContent-Type: application/json\r\n\r\n{metadata}\r\n"
        f"--{boundary}\r\nContent-Type: application/octet-stream\r\n\r\n"
    ).encode() + data + f"\r\n--{boundary}--".encode()
    r = requests.post(
        "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
        headers={"Authorization": f"Bearer {creds.token}", "Content-Type": f"multipart/related; boundary={boundary}"},
        data=body
    )
    print(f"✅ Created {FILE_NAME} on Drive ({len(data)} bytes)")

if r.status_code not in (200, 201):
    print(f"❌ Drive upload failed: {r.status_code} {r.text}")
    sys.exit(1)

# Cleanup: keep only last KEEP files
r = requests.get(
    "https://www.googleapis.com/drive/v3/files",
    headers={"Authorization": f"Bearer {creds.token}"},
    params={"q": f"'{FOLDER_ID}' in parents and name contains 'clawdbot-config-' and trashed=false", "fields": "files(id,name,createdTime)", "orderBy": "createdTime desc", "pageSize": 50}
)
all_files = r.json().get("files", [])
if len(all_files) > KEEP:
    for old in all_files[KEEP:]:
        requests.patch(
            f"https://www.googleapis.com/drive/v3/files/{old['id']}",
            headers={"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"},
            data=json.dumps({"trashed": True})
        )
        print(f"🗑️ Trashed old backup: {old['name']}")
PYEOF

rm -f "$ENCRYPTED"
echo "✅ Done"
